# Project Audit History — Child WORK

## 目的と責任
- Branch: `feature/ticket-project-audit-history`; parent: `feature/ticket`.
- Projectの作成・改名・既存条件内の削除を記録し、削除後もProject ID/keyと操作情報を保持する。
- Archive/restore、公開監査一覧、Ticket履歴は対象外。

## 実装契約
- Fetch時点の最新Epicは`be3cb7b`で、本Childのbaseと一致。Child tipはEpicから10 commits ahead。
- `project_audit_events` はProject/Userへの外部キーを持たず、削除後もID/key、実行者、action、snapshot、時刻を保持する。
- 作成・改名・削除の監査insertは各状態変更と同一transaction。変更のない改名ではイベントを作らない。
- 削除権限は従来どおりadmin限定、Ticketを持たないProjectに限定する。
- Project key生成はlive Projectsと監査ledgerの両方を予約済みとして扱う。監査済みkeyの明示指定も拒否する。
- Creation Child (`67aa0cd`) は同じ `ProjectController::store` と作成フローを変更する。creator設定・leader/write登録・`project.created`記録を一つのtransactionに統合し、Epicの5回key衝突retryをtransaction外側に維持する。
- Lifecycle Child (`a52c78c`) は同じControllerの一覧・改名・削除を変更し、archive/restoreも追加する。改名・削除監査を残し、archive/restoreイベントも各状態変更transaction内に記録する必要がある。LifecycleのProject model castも保持する。
- Discovery API Child (`31d9dc7`) は同じControllerの検索一覧とkey検索を変更する。Lifecycleのactive/archive絞り込みを検索にも適用する。Leadership Child (`0d52402`) は別の `ProjectMemberController` を変更し、作成時leaderを唯一のleaderとして扱う。

## 検証状態 (SHA `e723d79f3de5ef503827b3192e1f711b26395fb1`)
- SQLite in-memoryで `ProjectAuditHistoryTest`: 5 tests / 31 assertions、`ProjectManagementTest`: 8 / 44、Laravel全体: 116 / 527 が成功。
- Epic既存のevent injectionによるkey unique衝突・最大5回retryテストも成功。これは複数DB接続を使う実競合テストではない。
- `vendor/bin/pint --test` 成功。
- 専用SQLiteファイルDBで既存Project rowを作成後、Lifecycle `archived_at` (`000001`) → audit ledger (`000003`) → creator (`000004`) をschema-only overlayで適用。Project rowが保持され、`archived_at`/`created_by`は`null`、audit ledgerは作成された。Controller統合はしていない。
- 検証環境: Childごとに依存vendorとComposer autoloadを分離し、テスト用APP_KEYとSQLiteを指定。初回はvendor symlinkがEpic側のautoloadを参照し、APP_KEYも未設定だったためその結果を破棄して再実行した。migration helperも初回にDB環境変数を渡せず、明示設定で再実行した。既存`.env`・DBは使用していない。

## 未検証と統合ゲート
- MySQL migration、複数DB接続による高競合、transaction rollback fault injection、key全枯渇、直接DB書込みによるEloquent迂回は未検証。
- Ledger導入前に既に削除されたProjectのkeyは復元できない。migration後の通常API削除では予約が維持される。
- 統合後は作成・leader/write membership・created_by・audit insertの一括rollbackを回帰テストし、監査insert失敗時にProject/memberが残らないことを確認する。
- Migration順はProject key (`2026_10_07_000001`) → Lifecycle `archived_at` (`2026_10_08_000001`) → audit ledger (`2026_10_08_000003`) → creator (`2026_10_08_000004`)。この順で既存rowを保持するSQLite overlayを確認済み。MySQL上の互換性は未検証。
- 本Childは未merge。次はProject Creation ChildとController/Modelの3-way統合設計・統合テスト。
