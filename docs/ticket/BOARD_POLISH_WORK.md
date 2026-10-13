# Ticket Runtime Verification Child

owner_repo: jihoonlabs/jihoon-projects
owner_branch: feature/ticket-runtime-verification
role: child
status: validated-user-review-pending
parent_branch: feature/ticket
base_sha: 1fcc0cce1d8403629af6efbb6c93587036c249cb

## Responsibility / Boundary
Ticket V1を実browser・実Laravel・一時DBで検証した。既存DB・.envを変更せず、runtime・DB・browser profileは一時領域に置いた。API・DB schema・権限・機能仕様を変更していない。

## Changes
- TicketSeederの再実行で既存leaderがmemberへ降格し、readがwriteへ変わる回帰を再現して修正した。Project row lock内で未参加active userのみ追加し、既存role/permissionを保つ。繰り返しseedの回帰テストを追加した。
- Projectの追加操作ボタンを既存デザインのサイズ・余白・focus表示に合わせた。明るいボード背景の文字色も明示し、system dark設定でも案内を読めるようにした。
- MySQLで失敗した既存5 testsのSQLite前提を修正した。生成IDはresponseから取得、atomic SQLはdriver grammarのidentifier引用を使用、audit失敗triggerはSQLite/MySQL両対応。trigger DDLの暗黙commitを避けるためauditテストはDatabaseMigrationsで分離する。検証対象・assertionsを削除していない。

## Validation / Handoff
- PHP 8.4.24、MySQL 8.0.36、Chromium 153で検証。現在のcomposer.lockのSymfony 8依存はPHP 8.4以上を必要とする。lock変更・platform checkの回避はしていない。
- Laravel全145 tests / 707 assertionsがSQLite・MySQLの両方で成功。Pintと変更PHPのsyntax checkも成功。
- React全29 files / 194 tests、TypeScript、ESLint、変更CSSのPrettier、production buildが成功。
- 実frontend→Laravel→一時SQLiteで16 browser scenarios、最終Header CSSを含む実frontend→Laravel→MySQLで17 scenariosが成功。APP_ENV=localでCSRFを有効にし、無効tokenの419拒否を確認した。Project作成/初期leader/write、member read/write、Ticket key/背景色、pointer DnD保存/reload、詳細click/double click/focus、コメント改行/編集、閲覧memberの投稿、2 sessionの200/409/入力保持、leader譲渡後の権限消失、admin rename、終了409拒否/終了/閲覧/復元、Ticket削除、実session logoutを確認した。MySQL側では393px mobileの収まりも確認し、pageerrorは0件だった。最終View CSSはdark-systemの実browser smoke 4 scenariosで追加確認し、作成案内の文字色を確認した。
- 6並列PHPプロセスによる実Laravel controller/別DB接続で、Project 6件のunique key/creator/leader/write/audit、Ticket 6件の連番key/position/counterを確認。別PDO接続の行lock待ちが1205 timeoutとなり、明示rollback後に取得できることを確認した。
- MySQLの全migrationと、version追加前の既存Ticket 5件へのmigrationを確認。全フィールドを保持し、全件version=1となった。
- アプリ検証SHA: `a44f832067b77ea16fb7e98c063088ca9f5276b6`。公開Git treeと検証済みローカルファイルの一致を確認した。利用者の実ローカル画面確認と指摘の修正は残るため、V1全体の完了とは扱わない。keyboard DnDは未実装で、既存status selectは維持する。
