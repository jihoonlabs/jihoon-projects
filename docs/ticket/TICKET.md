# Ticket Epic

## 目的
小規模チームが、ログインからTicketの作成・担当・優先度設定・ボード運用・協業・完了まで行えるProject単位の業務フローを提供する。

## 完了基準
社内利用に必要な基本機能を揃え、利用者が実画面で指摘した修正を反映してから次の段階に進む。自動テストだけでV1完了と扱わない。

## 現在の基準（2026-10-14）
- 作業・引継ぎの統一基準は `feature/ticket`。検証候補 `4e9542be5d61f17b4b426c451b19e6f8b9d8bf4d` を旧Epic `5af147b515bff8a2c85192e2009333968962d0c1` からfast-forward採用した。採用記録以外のアプリtreeは候補と同一。
- 承認済みboardデザインとDB保存型の重複しない淡色paletteを維持する。Project別DnD楽観順序、遅延成功後の新しい取得error保全、保存待ち入力lock/失敗draft保全、Login表示・認証応答競合修正を含む。
- 最終React 222 tests、type、ESLint、変更sourceのPrettier、production build通過。実frontend→Laravel→専用MySQLで認証/初回Project・Ticket、save409→明示retry201、遅延move200/新しいGET500、遅延認証応答の中断後のsession維持を検証した。詳細handoffは `BOARD_POLISH_WORK.md`。
- 新Childの追加を止め、この基準から利用者画面と残る問題を確認する。会社SMTP、元ユーザーの再ログイン後の実環境、外部OAuth、keyboard DnD、今回の独立reviewは未検証。V1全体は未完了。
- 今後は承認済み作業のcommitを通常pushして他環境へ渡す。Epic採用は明示承認時のみ。採用済みbranchは不要な参照・比較用途を確認して整理し、進行中・未採用・dirty/DB/.envを保持する。

## 既存採用結果（履歴）
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

- Persistent Project Paletteを検証候補 `972051af5e1ebb3c26963df1256d4a07cdd48182` からローカルfast-forward採用した（採用前Epic: `9269be437b16cfe9e2a9db55e1f7deec558d3faa`）。最終Child: `4ed28c96d27756f6fa746d1962cd9194cc951abc`、アプリ検証SHA: `0b953a72f54f9426b3b28d6fb7414069c23c6a73`。key hashを廃止し、216種類の明るい黄・緑・ミント・青系の色をProjectに保存する。DB unique制約と生成再試行で重複を防ぎ、名前変更・別ユーザー・再接続でもカード全面の同色を保つ。デザインは利用者承認済み、V1は実使用確認待ち。

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

## Persistent Palette採用検証
- MySQL 8.4.11専用DBの既存3 Project・3 user・4 membership・4 Ticket・4 commentの全fieldを保持してcolor migration成功。非null/unique、直接重複UPDATEの1062拒否、6実session/複数PHP workerの同時生成で6色、別PDO row lockの1205とrollback解放を確認。この環境以外のDB設定・分離レベルまで保証しない。
- 候補の実frontend→Laravel→MySQLで作成・version付き編集・担当者再編集・pointer状態移動/reload・comment CRUD/権限・Project切替/色分離・確認付き削除を検証。6 grouped scenarios、Parent React208 testsが成功。アプリコード修正なしで承認済みデザインを維持した。
- 元のユーザーSQLite・envと4デザインProject/20 Ticketを保持。採用後のアプリtreeは検証SHAと同一。追加変更はこの採用記録のみ。Child149 Laravel tests、type/lint/buildの同一コード検証は反復しない。
- 詳細: `PROJECT_PALETTE_WORK.md` / `PROJECT_PALETTE_INTEGRATION_WORK.md`。最終採用状態の正本は本Epic文書。Child/candidateは保持する。外部OAuth完了・keyboard DnDと利用者による実使用確認は残り、V1全体は未完了。

## Branch整理の境界
- Remote Ticket関連45 branches。現在Epicに全commitが含まれる既存26 Childは削除候補。最新recovery candidateとpalette候補は今回の採用・確認基準として保持する。実行中worktreeと旧previewは保持する。
- project-order/auth/delayed-drag/save-input/login-designのアプリcommitは採用済みだが、Child tipの追加文書commitは独立して残る。コード不足と文書差分を区別し、重複mergeしない。
- 旧project-ui/project-overview、login-ui/board-ux、audit-history、ui-modal、test-user-admin、preview等には独自commitがある。現行機能と同等か未採用かを個別照合するまで保持し、旧デザインの巻戻し・権限変更をまとめて適用しない。
- 優先順: 統合基準の利用者確認 → 再現する問題と修正案の一覧 → 必要な責任のみ実装。過去branchを統合するためだけの新Childを作らない。

## 安定性点検（2026-10-15）
対象アプリSHA: `a616ce06e36c1f88dd609c7ea788cf01de00ed39`。新機能・新Childを追加せず、共通基準の問題と修正方針を整理した。今回の変更は本記録のみで、下記問題は未修正。

| 優先度 | 確認結果 | 次の修正・確認 |
| --- | --- | --- |
| 高 | 同じTicketで2件のmoveを待機させ、先行moveを失敗させると後続も同じ失敗でrejectされ、APIは1回しか呼ばれない。storeの独立再現testが期待2回/実際1回で失敗。 | 先行失敗の利用者通知と個々のPromise結果を保ち、後から明示された操作を処理できる待機列へ修正する。古いboard_versionはserver409で拒否し、自動再試行・強制上書きをしない。UI経由の連続操作再現も追加する。 |
| 中 | 実browserでdevのTicket一覧/Project一覧は各2 GET、詳細は2 GET（1件中断）、comment一覧は2 GET。productionは全て各1 GET。 | Strict Effect再実行に耐えるcleanup/同時取得共有を検討する。単純なonce flagやStrict Mode無効化は使わない。最新情報取得・再試行・権限喪失・遅延応答guardを維持する。 |
| 中 | Ticket/Project/comment一覧が全件取得。小規模データで障害は未再現。Ticket一覧6件は3 SQL、計約2.39ms、response1855 bytes。これは単一測定で負荷・容量保証ではない。 | 想定人数/件数を定めてresponse size・query数・p95・同時更新を測る。必要ならProject絞込み/ページングを別途契約確認して導入する。TicketResourceで使わないproject eager loadも見直し候補。 |
| 確認 | expected_versionは既存client互換で任意。詳細編集は送信するが、全API clientが競合保護されるとは限らない。 | 各更新経路のversion/board_version送信範囲を確認する。互換契約を無断変更しない。 |

- 実frontend→Laravel→専用MySQLでwriter/別user/adminのlogin200、未認証401、存在しないTicket404、logout後401を確認。別userが閲覧できないTicket・comment・memberへの直接GETは403。一覧DTOの正version/一意ID、Project色の一意性を確認。今回の権限検証はread境界であり、全write権限・権限剥奪との並行実行の網羅検証ではない。
- 専用MySQLの13 Project/6 user/15 membership/7 Ticket/4 commentを読取検査。不正version、孤立Ticket/comment、重複color/issue_key/Project内status-positionは全て0。元ユーザーDBを検査した結果ではない。
- 実browserのlogin、reload、Project3件の切替、詳細、編集開始/取消、Project一覧表示でpageerror0。測定した変更APIはlogin1 POSTのみで、Ticketの二重作成を再現したものではない。CSRF取得・CORS preflight・変更後の再検証GETを同じ業務操作の重複と混同しない。
- Remote Ticket branches45件を再確認。Epicに全commitが含まれる別branch28件（最新の比較候補2件を含む）、独自commitが残る16件。order/auth/drag/save/login-designの残差はhandoff文書、旧UI/preview/audit等の残差は個別比較が必要。未採用commit・比較基準・実行中worktreeは保持し、削除未実行。
- ローカル証拠: `/private/tmp/ticket-recovery-local-check-20261014/request-audit-{production,development,production-detail,development-detail}.json`, `permission-audit.json`, `data-audit.json`。queue再現は `/private/tmp/ticket-readiness-audit-20261015/queue.test.ts`。これらは隔離検証用で公開しない。
- 画面はproduction `http://127.0.0.1:3280`（検証候補branch、Epicと同じアプリcode）、API8180/専用MySQLへ復元した。元3000/8000、SQLite/.envは保持。負荷test・実社内SMTP・元ユーザー認証環境・今回の独立Test Reviewは未実行。既存全suiteはcode変更がないため反復しない。V1完了ではない。
