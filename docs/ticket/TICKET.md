# Ticket Epic

## 目的
小規模チームが、ログインからTicketの作成・担当・優先度設定・ボード運用・協業・完了まで行えるProject単位の業務フローを提供する。

## 完了基準
社内利用に必要な基本機能を揃え、利用者が実画面で指摘した修正を反映してから次の段階に進む。自動テストだけでV1完了と扱わない。

## 現在の状態
- Epic branch: `feature/ticket`。Project管理Integration Child `feature/ticket-project-integration` を `083e11c8b70e4f2e53ed13360567bb33300bdbe9` までfast-forward統合した。
- Ticket V1のログイン、Project切替/メンバー権限、Ticket CRUD、コメント、検索/担当者filter、DnD/順序保存、Project別Ticket keyを含む。
- Project APIはactive userによる作成、creatorの不変性と初期leader/write登録、rename、archive/restore、leader譲渡、メンバー範囲検索、監査記録に対応する。監査履歴の画面は未実装。
- Project Color Child `feature/ticket-project-colors` を `279556ae55fed766d0299c4bdfb16e4c051b0d3e` までfast-forward統合した。Projectの不変keyから決まる淡い色をTicketカードの枠線に適用する。Project名や再接続後も色は変わらない。

- Ticket詳細中心UXを検証候補 `d260a70568d11272d8098e07ebc3f1a3370ae649` からローカルfast-forwardで採用した。カードから詳細を開き、編集・削除を詳細内で行う。担当者の再編集、ドラッグ失敗時の並行成功データ保持と再取得失敗時の案内も含む。Ticket V1全体は未完了。

- Ticketの最新詳細取得・編集競合防止を検証候補 `07b0f0088798f1180879c46dcdd2fc3443401370` からローカルfast-forwardで採用した。取得中・失敗・削除・権限喪失を区別し、version条件付き保存で古い編集を拒否する。競合入力を保持し、明示再取得・再編集と遅延応答破棄に対応する。Ticket V1全体は未完了。

- Board Usability Child `feature/ticket-board-polish` のアプリ検証SHA `1dcaf449e949396caf5de89cb7fba78d64830f7b` を含む単独候補を採用した。ログアウト、Projectのカード背景色、タイトルクリック/カード余白ダブルクリック、重複詳細ボタンの整理、Project・操作権限の表示、コメントの改行・折返し・投稿日時を対象とする。API・権限・データモデルは変更していない。

- Project Entry Child `feature/ticket-project-entry` のアプリ検証SHA `79f2a8e36012621e5fb6150703263459c435ac21` を採用した。Project一覧・名前/key検索・選択と作成を既存APIにつなぎ、Projectがない利用者もleader membership取得後にTicket作成へ進める。Ticket作成成功後のProject再取得失敗は保存失敗として扱わない。

- Project Operations Child `feature/ticket-project-operations` のアプリ検証SHA `9c511b34d814e293d339d05f60399025a9d2bcf7` を採用した。Project名変更（admin）、終了・復元（admin/leader）、終了一覧と閲覧専用ボード、専用leader譲渡を画面に接続した。直接role変更/leader追加/leader削除を画面から除き、保存成功後の再取得失敗と遅延Project応答を安全に扱う。Backend API・DB schema・権限は変更していない。

- Runtime Verification Child `feature/ticket-runtime-verification` の検証SHA `a44f832067b77ea16fb7e98c063088ca9f5276b6` を採用した。実browser/Laravel/SQLite/MySQLの検証を実行し、再seedで既存role/permissionを上書きする回帰、MySQLで動かないテストの前提、追加Projectボタンとsystem dark時の案内表示を修正した。API・DB schema・権限仕様の拡張はない。V1全体は利用者の実ローカル画面確認前であり未完了。

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

- Project Entry Child / アプリ検証SHA: `79f2a8e36012621e5fb6150703263459c435ac21`（基準: `ed67f6edbaa8369ef7059ec6fe43f9ee91a19350`）。

- Project Operations Child / アプリ検証SHA: `9c511b34d814e293d339d05f60399025a9d2bcf7`（基準: `07db066adb8b9171531680c5b297d25c88cbd02f`）。

- Runtime Verification Child / 検証SHA: `a44f832067b77ea16fb7e98c063088ca9f5276b6`（基準: `1fcc0cce1d8403629af6efbb6c93587036c249cb`）。

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

- Project EntryはReact全体27 files / 180 tests、TypeScript、ESLint、変更ファイルのPrettier、production buildに成功した。CSRF付き作成、二重送信防止、入力保持・再試行、初期読み込み中の作成抑止、一覧検索/選択、最初のProject作成→leader権限取得→Ticket作成画面、Ticket保存成功後のProject GET失敗を検証した。公開Git treeとローカル検証済みファイルは一致する。
- 今回のbackend API・DB schema・権限変更はない。実browser/実Laravel接続/MySQLは未検証であり、モックによる画面・API境界検証を実DB検証とは扱わない。現行WORK: `docs/ticket/BOARD_POLISH_WORK.md`。

- Project Operationsは対象58 tests、React全体29 files / 194 tests、TypeScript、ESLint、変更ファイルのPrettier、production buildに成功した。名前変更のadmin制限、archive確認/未完了Ticket拒否/再試行、restore/二重要求抑止、終了一覧、adminを含む終了ProjectのTicket・コメント変更抑止、leader譲渡直後の旧leader権限消失を確認した。
- archive後に古いProject GETが到着してもactive一覧に戻さないこと、メンバー変更成功後GET失敗で操作を凍結し再取得のみ提供すること、保存中dismiss抑止を検証した。公開Git treeとローカル検証済みファイルは一致する。現行WORK: `docs/ticket/BOARD_POLISH_WORK.md`。
- production serverはhostname指定で起動し、同じ実行内で `/login`・`/tickets` のHTTP 200、HTML/Next assetsを確認した。以前のnetworkInterfaces起動失敗はhostname指定で回避できる。実browserや実backend接続を確認した結果ではない。

- Runtime Verification: Laravel全145 tests / 707 assertionsがSQLite・MySQL両方で成功、React全29 files / 194 tests、TypeScript、ESLint、Pint、変更PHPのsyntax、変更CSSのPrettier、production buildも成功。PHP 8.4.24・MySQL 8.0.36・Chromium 153を使った。現在のcomposer.lockのSymfony 8依存はPHP 8.4以上を必要とする。
- 実frontend→Laravel→一時SQLiteで16 browser scenarios、最終Header CSSを含むMySQLで17 scenariosが成功した。APP_ENV=localでCSRFを有効にし、無効token419、実login、Project作成/初期leader/member追加、Ticket key/背景色、pointer DnD保存/reload、詳細click/double click/focus、コメント改行/編集、read memberの投稿、2 sessionの200/409/入力保持、leader譲渡後の権限消失、admin rename、Project終了409拒否/終了/閲覧/復元、Ticket削除、実session logoutを確認した。MySQL側は393px mobileの収まりも確認し、pageerrorは0件。最終View CSSはsystem darkの実browser smoke 4 scenariosで案内の可読性を追加確認した。
- MySQLの複数PHPプロセス/別接続でProject 6件の同時作成（unique key/creator/leader/write/audit）とTicket 6件の同時作成（連番key/position/counter）を確認した。別PDOの行lockが1205 timeoutになり、明示rollback後に取得できた。全migrationと、version追加前の既存Ticket 5件の全フィールド保持・version=1を確認した。上記環境・対象の検証結果として扱い、その他のDB設定・分離レベルの結果とは扱わない。
- TicketSeederのrole/read permission破壊を修正前に再現し、繰り返しseedでも保全する回帰テストを追加した。検証用DB・runtime・profileのみを使用し、既存DB・.envは変更していない。公開Git treeと検証済みローカルファイルは一致する。現行WORK: `docs/ticket/BOARD_POLISH_WORK.md`。

- Comment Reliability Child / アプリ検証SHA: `768a438461051b77d117059315771947295bc060`（基準: `dd5d547430511234336a1c5278244adc14dd39e8`）を採用した。コメント取得中の投稿を抑止し、取得失敗の再試行、POST待ちで入力した次の下書きの保全、重複送信防止、Ticket切替前の遅延GET/POST応答の分離を修正した。API・DB・権限変更はない。
- 対象13 tests、React全29 files / 200 tests、TypeScript、ESLint、変更TSXのPrettier、production buildが成功した。今回の実browser/実Laravel接続は未実行。前回の接続検証と今回のReact遅延応答検証を区別する。現行WORK: `docs/ticket/BOARD_POLISH_WORK.md`。

- Member Recovery Child / アプリ検証SHA: `da7ef46235416c57dd9086af39a7a685eb6bcded`（基準: `6f744b2b2c924938b2f6c69f3c87f361997c5993`）を採用した。member取得失敗時に同じProjectで権限を再取得できる。dialogを閉じた後も遅延応答guardを使用し、再確認中の古いmembership使用と別Projectへの応答混入を防ぐ。member取得でProject一覧errorを消さない。API・DB・権限仕様は変更しない。
- 修正前で新規4 testsの失敗を確認し、対象View 32 tests、React全29 files / 204 tests、TypeScript、ESLint、変更TSX/CSSのPrettier、最終production buildが成功した。今回の実browser/実Laravel接続は未実行。現行WORK: `docs/ticket/BOARD_POLISH_WORK.md`。

- List Recovery Child / アプリ検証SHA: `739c51d0f01a9bc601f178280d82715308d8aeb8`（基準: `1e5f5e8660af43a9cd6518f25674217434fbfba6`）を採用した。Ticket削除成功後のProject取得失敗を削除失敗と扱わずdetailを閉じる。Ticket一覧の取得失敗はboard上で再取得でき、取得中の案内と既存一覧の保全に対応する。
- 対象View 36 tests、React全29 files / 208 tests、TypeScript、ESLint、変更TSXのPrettier、production buildが成功。実browser/実Laravel接続は今回未実行。API・DB・権限仕様の変更はない。現行WORK: `docs/ticket/BOARD_POLISH_WORK.md`。

- Board Design Child / アプリ検証SHA: `c5417c648f1380dd673b26f1c8317c26ad817346`（基準: `a02f37781e0c2fbc5d8852e1f26fcaecb2edf582`）を採用した。利用者の実画面指摘に合わせ、Header/toolbarを圧縮・整理し、Project色を維持しながらcard背景を淡くした。文字・列幅・間隔、dark-systemの検索入力を調整した。既存accessible nameと機能・API・DB・権限を維持する。
- React 208 tests、TypeScript、ESLint、Prettier、production buildが成功。実Chromiumのdark-systemで1440/940/393px、ページ横overflowなし、検索可読性、mobile detail、pageerror 0件を確認。API fixtureによる表示検証であり、実Laravel接続ではない。修正後の利用者画面確認は残る。現行WORK: `docs/ticket/BOARD_POLISH_WORK.md`。

## 次の作業
- 利用者の実ローカル環境で画面を確認し、指摘を修正する。社内基本機能と指摘修正が満たされるまでV1完了とは扱わない。
- keyboard DnDは未実装・未検証。pointer DnD/保存・reconnectionと既存status selectは上記実接続で検証済み。

## 今後の候補
- 監査記録の画面表示、Activity / Historyの利用者向け機能は別途優先度を判断する。
