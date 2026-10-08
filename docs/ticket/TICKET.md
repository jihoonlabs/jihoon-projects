# Ticket Epic

## 目的
小規模チームが、ログインからTicketの作成・担当・優先度設定・ボード運用・協業・完了まで行えるProject単位の業務フローを提供する。

## 現在の状態
- Epic: `feature/ticket`
- Project Access Child `feature/ticket-team-access`、カード順序保存 Child `feature/ticket-order-persistence`、Project別Ticket key Child `feature/ticket-project-key` を統合済み。
- Project key統合の採用Child SHA: `2ab0ea4e2a64fa7207de799669aeab7b03574935`。
- V1にはTicketカードの表示・DnD回帰修正と回帰テスト、および統合検証記録を含む。
- ローカルEpicは `origin/feature/ticket` の最新を含む。AGENTS.mdは `origin/main` の承認済み規則に一致。

## V1に含む範囲
- SanctumログインとTicket画面保護。
- Project切替、Project単位のread/writeメンバー権限。
- Ticketの作成・詳細・編集・削除、担当者・優先度、状態変更、コメントCRUD。
- 検索・担当者フィルター、Kanban DnD、順序の永続化と古いboard versionの409再同期。
- Projectごとの不変な3文字keyとTicket連番。Project名変更後もkeyを維持し、Seeder再実行で既存keyや採番を巻き戻さない。

## 統合検証
- 採用Child SHA: `2ab0ea4e2a64fa7207de799669aeab7b03574935`。このSHAにはProject key、Seeder再実行時の採番維持、カード表示回帰修正と対応テストが含まれる。
- Child検証記録: Laravel 109 tests / 487 assertions、React 129 tests、TypeScript、ESLint、production buildが成功。Chromeで2 Project間のkey独立、同一Project内連番、Project名変更後のkey維持を確認。
- Epic再検証: Laravel全109 tests / 487 assertions、Pint、React全22 files / 129 tests、TypeScript、ESLint、production buildが成功。Pintが指摘した2つのテストメソッド間の余分な空行を整理して再実行した。
- Chrome実機相当のブラウザー確認: Child SHA上で2 Projectのkey独立、同一Project内の連番、Project名変更後のkey維持を確認済み。テストデータは一時SQLite DBと一時Chrome contextを使用。
- MySQL上のmigrationは未検証。SQLite migrationと既存データのkey backfillはテスト済み。
- 2026-10-08の追加修正: 同時Project作成で生成した3文字keyがDBのunique制約に衝突した場合、Project作成APIは `project_key` のunique違反に限り最大5回まで再生成・再試行する。他のunique違反は再試行しない。既存key、Ticket採番、API契約は変更しない。
- 追加回帰テスト: creatingイベントで既存keyを注入し、unique違反後に新規keyで作成成功すること・既存keyが保持されることを検証するケースと、5回連続で衝突して500応答となりProjectが残らないケースを追加。イベント注入による競合再現であり、実際の複数DB接続による同時実行テストではない。
- 今回の検証状態: GitHub上でコード・差分を確認。追加PHPテスト、Laravel全件、Pint、Reactテスト、実MySQLでの同時実行/migrationは未実行。過去の成功記録を今回の結果として扱わない。

## 合意済みの次期Project管理仕様（未実装部分を含む）
- Project作成者を初期リーダーとして登録し、Ticket権限は `write` にする。一般ユーザーも作成可能にする変更は既存のadmin限定APIからの権限変更となるため、実装・テストを一体で扱う。
- Projectごとのリーダーは1名。リーダー譲渡時は新リーダーを `leader`、旧リーダーを `member` に更新し、途中状態やリーダー不在を作らないようDB transactionで実装する。
- メンバーのProject役割（leader/member）とTicket権限（read/write）は別軸。Ticketの参照・編集は選択中Projectの権限で判定する。
- 3文字の `project_key` は画面表示、Project検索、Project別Ticket検索・共有URLで使う公開識別子。既存DBの数値 `id` は内部参照・FKとして維持し、`project_key` は改名やリーダー譲渡でも不変とする。
- Project作成 → key自動採番 → 作成者をleader登録 → Project選択 → Project内Ticket発行（例 `ABC-01`）の一連の操作をUIで提供する。
- 既存実装: DBのProject key生成、Project別Ticket連番、メンバーpivotのrole/permission、管理者によるProject作成API、メンバー管理API。未実装: 一般ユーザー作成/自動リーダー登録、単一リーダー制約と安全な譲渡、Project作成UI、key検索/公開URL。
- 上記は仕様記録であり、実装・テスト完了の宣言ではない。既存のTicket V1の動作を維持し、権限変更は回帰テストを追加する。

## Project管理 Child の作業状況（2026-10-08）
- Project作成の新仕様はChild `feature/ticket-project-creation` に分離した。Child作業MD: `docs/ticket/PROJECT_CREATION_WORK.md`（Child上のみ）。
- Child実装commit: `03a983f5c925a2ffaffcbf37e06de2182e0cacdb`、テストcommit: `6e7614b06d8022b15cdd7ee06f841ceac4c90e0d`。Child作業MD commit: `a2854d3a70393713c2df8fbb200c9abf4c43d51c`。
- 上記コードを一時的にEpicへ直接commitしたことを修正し、Epic上で同等内容をrevertした（履歴は保持）。`08ed10d8` に対するEpicのコード差分はゼロであることをGitHub compareで確認。
- Childのテストは未実行。検証・採用SHA確認前にEpicへ統合しない。
- リーダー譲渡、Project key検索・画面、保管・復元・完全削除は責任単位ごとに別Child候補とする。仕様確定と実装完了を混同しない。

## 次の作業
- 実行手順と検証記録のテンプレートは `docs/ticket/TICKET_REMOTE_VALIDATION.md` を参照。追加回帰テストとLaravel/Pintの再検証、MySQL migration・独立接続の競合確認、main統合時の競合確認が未完了。
- main merge/pushとbranch削除は承認待ち。

## 今後の候補
- Activity / HistoryはV1完了後に再評価する。
