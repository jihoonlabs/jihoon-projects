# Persistent Project Palette

owner_repo: jihoonlabs/jihoon-projects
owner_branch: feature/ticket-project-palette
role: child
parent_branch: feature/ticket
base_sha: 9269be437b16cfe9e2a9db55e1f7deec558d3faa
status: validated-user-review-pending

## Responsibility
Projectごとに重複しない明るい黄・緑・ミント・青系の色をDBに保存し、カード全面に使用する。既存データ・member権限を保持して移行する。4つ以上のデザイン確認Projectと複数状態のTicketを、既存API契約で重複なく準備する。V1は利用者確認待ち。

## Contract
- 色はサーバー所有・変更不可。rename、reload、別ユーザー、archive/restoreでも保持する。
- DB unique制約とProject生成の衝突再試行で重複を防ぐ。palette満杯時は503を返し、重複色にfallbackしない。削除済みProjectの色は再利用可能。
- Epicでは実装しない。push・Epic/main採用・既存資産削除は行わない。

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
- 検証済みsourceはこのbranchの最終commit。Parent/Epicは基準SHAのまま。Epic採用・push・V1完了は行わない。
- 新color migrationのMySQL、複数接続の同時Project作成/row lockは未検証。SQLite unique結果だけでMySQL実行を検証済みとしない。色は有限で216 Projectまで（archivedも含む）。全paletteの知覚的な色差を保証せず、保存hexの重複を禁止する。
- 利用者の画面確認と指摘修正は残る。

## Improvement note
- Migration保全checkは既存行・fieldの保持を検証し、追加migration記録まで「変更」と誤判定しない。
