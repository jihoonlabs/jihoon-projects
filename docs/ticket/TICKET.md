# Ticket Epic

## 目的
小規模チームが、ログインからTicketの作成・担当・優先度設定・ボード運用・協業・完了まで行えるProject単位の業務フローを提供する。

## 現在の状態
- Epic branch: `feature/ticket`。Project管理Integration Child `feature/ticket-project-integration` を `083e11c8b70e4f2e53ed13360567bb33300bdbe9` までfast-forward統合した。
- Ticket V1のログイン、Project切替/メンバー権限、Ticket CRUD、コメント、検索/担当者filter、DnD/順序保存、Project別Ticket keyを含む。
- Project APIはactive userによる作成、creatorの不変性と初期leader/write登録、rename、archive/restore、leader譲渡、メンバー範囲検索、監査記録に対応する。監査履歴の画面は未実装。
- Project Color Child `feature/ticket-project-colors` を `279556ae55fed766d0299c4bdfb16e4c051b0d3e` までfast-forward統合した。Projectの不変keyから決まる淡い色をTicketカードの枠線に適用する。Project名や再接続後も色は変わらない。

- Ticket詳細中心UXを検証候補 `d260a70568d11272d8098e07ebc3f1a3370ae649` からローカルfast-forwardで採用した。カードから詳細を開き、編集・削除を詳細内で行う。担当者の再編集、ドラッグ失敗時の並行成功データ保持と再取得失敗時の案内も含む。Ticket V1全体は未完了。

- Ticketの最新詳細取得・編集競合防止を検証候補 `07b0f0088798f1180879c46dcdd2fc3443401370` からローカルfast-forwardで採用した。取得中・失敗・削除・権限喪失を区別し、version条件付き保存で古い編集を拒否する。競合入力を保持し、明示再取得・再編集と遅延応答破棄に対応する。Ticket V1全体は未完了。

- Board Usability Child `feature/ticket-board-polish` のアプリ検証SHA `1dcaf449e949396caf5de89cb7fba78d64830f7b` を含む単独候補を採用する。ログアウト、Projectのカード背景色、タイトルクリック/カード余白ダブルクリック、重複詳細ボタンの整理、Project・操作権限の表示、コメントの改行・折返し・投稿日時を対象とする。API・権限・データモデルは変更していない。

## 採用Child SHA
- Project Lifecycle: `a52c78cfbb9c1d70d724adc06aa593ae0e67f0f3`
- Project Creation: `f401c960c0d125f07569cda775b7bc28f581d5e5`
- Project Audit: `3c8cee61d083a524159f76e9287a621c0cfc57b0`
- Project Leadership: `0d524028e4b6e16cae929ccc914b571443451845`
- Project Discovery API: `31d9dc71e59d8a01c14b6bcdb0047efe9683b897`
- Project Integration: `083e11c8b70e4f2e53ed13360567bb33300bdbe9`
- 既存のProject key Child: `2ab0ea4e2a64fa7207de799669aeab7b03574935`
- Project Color: `279556ae55fed766d0299c4bdfb16e4c051b0d3e`
- Ticket Detail UX Child: `5c9c6e03a60b9b0ccba86e2d0915d2fbcbf0d99f`
- Ticket Detail UX採用候補: `d260a70568d11272d8098e07ebc3f1a3370ae649`（採用前Epic基準: `fdccd96faa20bf9e5f424bd8ae47b1756b2978b6`、fast-forward採用済み）。先行修正の重複適用なし。

- Ticket Detail Concurrency Child / アプリ検証SHA: `37a649666f1a45bff111a06c6d30b65da0a3df6f`
- Ticket Detail Concurrency採用候補: `07b0f0088798f1180879c46dcdd2fc3443401370`（採用前Epic基準: `1d0af6114d2b354f64e4bc179a2eec94ce0c43a9`、fast-forward採用済み）。UX・先行修正は既に基準に含まれ、重複適用なし。

- Board Usability Child / アプリ検証SHA: `1dcaf449e949396caf5de89cb7fba78d64830f7b`（基準: `cd6ada3aafdcdd6d2e561e1180880e44a77be271`）。

## 統合検証
- Project関連Laravel tests: 33 tests / 186 assertions、Laravel全件: 136 tests / 638 assertions passed。Pintと変更PHPのsyntax checkもpassed。
- ChromeでReactログイン後、一時SQLite DBを使ったProject作成、creator保持、初期leader/write、rename、archive/restore、名前/key検索、archive filter、board selectorの表示を確認。DBでcreate/rename/archive/restore監査eventも確認した。
- Project Integrationのブラウザー検証SHAは当時の採用先HEADと同じ `083e11c`。マージはfast-forwardのため、検証済みコードから差分なし。
- 既存Projectを保持するSQLite migrationテストと、一時DBへの全migration適用を確認。MySQL migration、複数接続での同時作成、実row lock競合は未検証。
- Project Color統合後のReact tests 23 files / 132 tests、TypeScript、ESLintはpassed。Production buildは同一コードのChild SHA `279556a` で検証済み。fast-forward後にコード変更はない。
- Chromeで同一Projectのカードが同色、別Projectが別色になること、rename/reload後の色とissue keyの維持、状態・優先度・keyboard focus属性を確認した。Pointer DnDでTicket `TZX-01`を`TODO`から`DONE`へ移動し、一時SQLite DBへの保存と枠線色・key・role/tabIndexの維持を確認した。既存DBは使用していない。
- 詳細: `docs/ticket/PROJECT_COLORS_WORK.md` と `docs/ticket/PROJECT_COLORS_MANUAL.md`。
- 詳細: `docs/ticket/PROJECT_INTEGRATION_WORK.md` と `docs/ticket/PROJECT_INTEGRATION_MANUAL.md`。

- Ticket Detail UX候補で独立test review、React 145 tests、関連Laravel 38 tests / 231 assertions、TypeScript、ESLint、Prettier、production buildが成功。実frontend→Laravel→一時SQLiteの8シナリオと、Project再取得403時の案内保持・再試行の集中確認が成功した。
- 今回の採用後、候補とのアプリコード一致、文書参照、Git状態と既存`ai/`・環境/SQLiteファイルの保全を確認した。追加変更はこの採用記録のみで、全テストは再実行していない。候補WORKの未採用表記は候補検証時点の記録であり、採用状態の正本はこのEpic文書とする。
- UX詳細: `docs/ticket/TICKET_DETAIL_FIRST_UX_INTEGRATION_WORK.md` と `docs/ticket/TICKET_DETAIL_FIRST_UX_MANUAL.md`。Child/integration branch・worktreeは保持する。

- Ticket Detail Concurrency候補自身で実frontend→Laravel→一時SQLiteの16シナリオ、関連Laravel 23 tests / 162 assertions、最後のParent範囲React 169 testsが成功した。既存Ticket 5件へのversion migrationでデータ保持と初期値1を確認。詳細の最新取得・2クライアントの200/409・入力保持/再取得・500/403/404・遅延応答、担当者・DnD・失敗復元と編集中move後の競合を検証した。
- Childの同一コードで全Laravel 144 tests / 703 assertions、TypeScript・Lint・buildと独立test reviewが成功済み。今回の採用後は候補とのアプリコード一致、文書参照、Git状態と既存`ai/`・環境/DBの保全を確認し、コード変更・新たな不確実性がないため通過済みテストを反復していない。採用後の追加変更はこの記録のみ。候補WORKの未採用表記は候補検証時点の記録であり、採用状態はこのEpic文書を正本とする。
- 詳細: `docs/ticket/TICKET_DETAIL_CONCURRENCY_INTEGRATION_WORK.md` と `docs/ticket/TICKET_DETAIL_CONCURRENCY_MANUAL.md`。今回の採用段階では既存DBへのmigrationを実行していない。API/frontend起動前に `2026_10_11_000000_add_version_to_tickets_table.php` の適用が必要。MySQL migration・別接続同時実行・isolation・row lockは未検証。SQLite結果で検証済みとは扱わない。

- Board UsabilityのReact全体26 files / 172 tests、TypeScript、ESLint、変更ファイルのPrettier、production buildは成功。対象37 testsでlogout成功/失敗/再試行/重複防止、titleとdouble click、status操作の分離、既存詳細・権限フローを確認した。公開Git treeと検証済みファイルの一致を確認し、採用記録のみを追加する。
- 実browser表示、pointer DnD、frontend→Laravelのlogoutは今回未検証。Chromium downloadと実行環境のnetworkInterfaces制限により検証できなかった。PHP/MySQL環境は存在せず、過去のbackend検証を今回の実行結果として扱わない。詳細: `docs/ticket/BOARD_POLISH_WORK.md`。

## 次の作業
- Board Usabilityの実browser確認（背景色、コメントの折返し、詳細focus復帰、pointer DnD、Laravel logout）。Ticket V1全体は未完了。
- MySQL migrationと複数接続の同時作成/row lock検証は未検証。SQLiteや制御した要求順序で検証済みとは扱わず、専用環境で確認する。
- keyboard DnDは未検証・未実装の範囲として残る。詳細の最新取得・編集競合防止は上記候補から採用済みだが、Ticket V1全体は未完了。

## 今後の候補
- 監査記録の画面表示、Activity / Historyの利用者向け機能は別途優先度を判断する。
