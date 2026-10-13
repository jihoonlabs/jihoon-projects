# Project Management Integration Child — WORK

## 目的と範囲
- Branch: `feature/ticket-project-integration`、親Epic: `feature/ticket`。
- Project Lifecycle → Creation → Audit → Leadership → Discovery APIを接続し、既存契約とDB transactionを回帰検証する。
- Epic/mainへのmerge・push、Child branch削除、React UI変更は対象外。

## 採用Child SHA
- Lifecycle: `a52c78cfbb9c1d70d724adc06aa593ae0e67f0f3`
- Creation: `f401c960c0d125f07569cda775b7bc28f581d5e5`
- Audit: `3c8cee61d083a524159f76e9287a621c0cfc57b0`
- Leadership: `0d524028e4b6e16cae929ccc914b571443451845`
- Discovery API: `31d9dc71e59d8a01c14b6bcdb0047efe9683b897`
- 統合基準は最新Epic `be3cb7b77ae77bfae5c686ee725b38d0a9f03b3e`。Epic Router `docs/ticket/TICKET.md` とAGENTS.mdを保持した。

## 統合契約
- `Project::archived_at` はdatetime castを維持し、Project Resourceは`archived_at`とnullableな`created_by`を返す。
- active userの作成は、Project・不変な`created_by`・作成者のleader/write membership・`project.created`監査記録を1つのtransactionで保存する。project_key unique競合の再試行も維持する。
- rename/deleteの監査記録は状態変更と同一transaction。監査テーブルにはProject FKを付けず、削除後もproject_keyを予約する。
- archive/restoreはProject row lock後に権限と状態を確認し、状態変更と監査イベントを同一transactionで記録する。同じ状態への再要求では重複イベントを作らない。
- membership変更とleader transferはProject row lockで直列化し、archived Projectへの変更を拒否する。leader transferは現leaderが正確に1名の場合だけ行い、read/write permissionを保つ。
- Discoveryはメンバー範囲のsearchとactive/archive filterを合成し、数値ID routeとproject_key lookupを維持する。
- migration順は`000001 archived_at` → `000003 audit ledger` → `000004 created_by`。legacy Projectの行とkeyを維持し、archive/creatorはnullのままにする。

## Child別の統合確認
- Lifecycle `a52c78c`: archive cast、Ticket変更ガード、archive/restoreと検索filterを統合suiteで確認。
- Creation `f401c96`: active user作成、creator不変性、初期leader/write、監査失敗時の全rollbackを確認。
- Audit `3c8cee6`: 作成/rename/deleteイベント、actor/snapshot、削除後key予約、イベント失敗時rollbackを確認。
- Leadership `0d52402`: 譲渡時の権限保持、leaderの間接変更/削除拒否、leader 0名/複数名の409を確認。
- Discovery API `31d9dc7`: key/name検索、所属範囲、key lookup、archive filterとの合成を確認。
- 上記は統合後のLaravel suiteによる確認。独立MySQL接続による同時操作は未検証。

## 実装・検証状態
- Integration Child内でLifecycle、Creation、Audit、Leadership、Discoveryの順にmergeし、ProjectController、ProjectResource、ProjectMemberControllerの共有境界を解決した。
- 追加回帰: 作成者・初期leader/write・監査記録、作成/Archive/Restoreの監査失敗時rollback、archive/restoreの冪等性、検索とarchive filterの合成、leaderが0名/複数名のtransfer拒否、既存行を保持するmigration順。
- Focused tests: `php artisan test --filter='ProjectManagementTest|ProjectAuditHistoryTest|ProjectLifecycleAuditMigrationTest'` — 33 tests / 186 assertions passed。
- Laravel全件: `php artisan test` — 136 tests / 638 assertions passed。
- Pint: `vendor/bin/pint --test` passed。変更PHPのsyntax check passed。
- テストはPHPUnit設定のSQLite `:memory:` DBを使用し、既存`.env`・DBには接続していない。
- 実ブラウザー: 一時SQLite DBでReactログイン→Ticket boardを開き、Project APIを操作。作成時の`created_by`偽装を無視し、本人がcreatorかつleader/writeになること、rename後もcreator/keyが不変であること、archive/restore、名前/key検索とarchive filter、board selectorでactive/archive/restoreの表示が切り替わることを確認。
- 同DBの`project_audit_events`で`project.created`、`project.renamed`、`project.archived`、`project.restored`のactor/snapshotを確認。UI上の監査履歴画面はない。
- 別SQLite DBで全migrationをseed付きで適用し、実ブラウザー回帰に使用。既存`.env`・DBには接続していない。
- この実行環境にMySQL/MariaDB client/serverがないため、MySQL migration、独立接続による同時Project作成、実row lock競合は未検証。

## 現在状態と次の作業
- 各Childのmerge checkpointと今回のIntegration検証結果をこのbranchに保持する。Epic/mainには未統合。
- MySQL環境でのmigration・複数接続・row lock検証は残る。Epicへの採用判断時に未検証事項として引き継ぐ。
