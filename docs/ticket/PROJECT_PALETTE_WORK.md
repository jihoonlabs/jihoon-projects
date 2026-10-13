# Persistent Project Palette

owner_repo: jihoonlabs/jihoon-projects
owner_branch: feature/ticket-project-palette
role: child
parent_branch: feature/ticket
base_sha: 9269be437b16cfe9e2a9db55e1f7deec558d3faa
status: ready-for-integration

## Responsibility
Projectごとに重複しない明るい黄・緑・ミント・青系の色をDBに保存し、カード全面に使用する。既存データ・member権限を保持して移行する。4つ以上のデザイン確認Projectと複数状態のTicketを、既存API契約で重複なく準備する。V1は利用者確認待ち。

## Contract
- 色はサーバー所有・変更不可。rename、reload、別ユーザー、archive/restoreでも保持する。
- DB unique制約とProject生成の衝突再試行で重複を防ぐ。palette満杯時は503を返し、重複色にfallbackしない。削除済みProjectの色は再利用可能。
- Epicでは実装しない。今回は利用者承認によりMySQL・実API・隔離統合検証通過後のローカルEpic採用のみ可。push・main採用・既存資産削除は対象外。

## Verification
- Laravel 149 tests / 1584 assertions、React 29 files / 208 tests、TypeScript、ESLint、変更Prettier、Pint、production build、diff whitespaceが成功。
- 216色のpaletteは重複なし、RGBの最小値217以上、黒文字contrast 7:1超を検証。DB unique拒否、生成、rename、他member、clientによる色上書き無効化、capacity満杯503を確認。
- 既存SQLiteのbackupとcopy migration rehearsalを先行し、既存の全業務field・member権限を保持して実DBにもcolor migrationだけを適用。既存Ticket、ユーザー、権限、.envは変更していない。追加migration行は新規記録として区別する。
- 実frontend→Laravel→既存SQLiteで `test@example.com` が所有する `デザイン確認 01 · サポート` / `02 · 開発` / `03 · ドキュメント` / `04 · 運用` の4 Projectと各5状態・5優先度の20 Ticketを作成。既存Seederは使わない。
- 再実行の追加Project/Ticketは0。repo外manifestのProject IDとTicket IDを優先し、renameや入力変更を上書きしない。記録済みProjectが見つからなければ重複生成せず停止する。
- 4 Projectの実画面で保存hexとcard全面背景が一致、project切替のデータ分離、reload後の同色、393px dark表示と横overflowなし、pageerror 0を確認。別の一時SQLiteで実login/CSRF/APIによるadmin rename、他member、新sessionでの同色も確認。
- Evidence / backup / manifest: `/private/tmp/ticket-project-palette-check-20261013/`。秘密・DB・fixture scriptsはcommitしない。

## Runtime / Handoff
- Frontend http://localhost:3000、API http://localhost:8000 はこのChildのコード。APIは元のenvをread-onlyで読み、元のSQLiteを明示指定。cache/storageはrepo外、既存の重複frontend/APIを置き換えた。
- アプリ検証SHA: `0b953a72f54f9426b3b28d6fb7414069c23c6a73`。今回の追加変更は検証記録のみ。最終Child SHAはbranch HEAD。V1完了・pushは行わない。
- 色は有限で216 Projectまで（archivedも含む）。全paletteの知覚的な色差を保証せず、保存hexの重複を禁止する。MySQLの検証は下記の専用環境に限定し、他のDB設定・分離レベルまで保証しない。
- 利用者の画面確認と指摘修正は残る。

## Improvement note
- Migration保全checkは既存行・fieldの保持を検証し、追加migration記録まで「変更」と誤判定しない。

## MySQL / Integration validation (2026-10-14)
- デザインは利用者承認済み。アプリコード・CSSは変更していない。
- 専用MySQL 8.4.11 container / DBでcolor追加前schemaを用意。既存3 Project、3 user、4 membership、4 Ticket、4 commentを保持してmigration成功。既存全field・role/permissionとTicket versionを比較し、一致を確認。
- colorは全Projectに非null・重複なし。直接重複UPDATEは1062で拒否。6つの実login session・複数PHP workerの同時POSTで6 Projectが成功し、色も6種類。別PDOのrow lockは1205で待機失敗し、明示rollback後の取得が成功。元のDB・envは使用/変更しない。
- Parent基準 `9269be437b16cfe9e2a9db55e1f7deec558d3faa` の隔離候補 `integration/ticket-project-palette-v1` にChildを単独適用。実frontend→Laravel→MySQLで6 grouped scenarios成功: Ticket作成、version付き編集・担当者再編集、pointer状態移動/reload/詳細誤開防止、comment CRUDとread memberの投稿/権限403、Project切替/色/データ分離、確認付きTicket削除/reload/404。保存済みデータと元fixtureの保持も再確認。pageerrorなし。
- 候補のParent範囲React 29 files / 208 tests成功。既存Childのtype/lint/build/Laravel149検証は同一アプリコードのため反復しない。
- Harnessの担当者ID型比較と、out-of-band fixture追加後の初回一覧snapshotを原因別に補正。未完了項目だけ再実行し、製品不具合として扱わない。修正対象の製品エラーはなし。
- Evidence: `/private/tmp/ticket-palette-mysql-20261014/{migration-result.json,concurrency-result.json,lock-result.json,crud-result.json}`。秘密・DB・scriptはcommitしない。
- 元の主worktreeは別作業の `epic/thumby-growth` に変わっていたため保持。feature/ticket refは基準SHAのまま確認し、採用用Epic worktreeを別途用意する。
- 残る事項: 利用者による実運用確認、keyboard DnD（既存未実装）、外部OAuth完了。V1全体は未完了。
