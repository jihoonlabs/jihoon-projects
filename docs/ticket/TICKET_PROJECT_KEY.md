# Ticket Project Key

## 目的と範囲
- Project作成時に変更されない3文字の英字keyを自動発行する。
- TicketはProjectごとの連番を使い、`KEY-01`, `KEY-02` の形式で `issue_key` を発行する。
- Project名の変更はkeyへ影響させない。
- Ticket詳細を開く操作やProject色など、他のUX変更は本作業に含めない。

## 境界と前提
- Project keyはDBでuniqueとし、Project作成時に自動生成する。
- Ticket番号はProject rowをlockした既存の作成transaction内で採番し、Projectごとに独立して増加する。
- 既存Project/Ticketはmigration時にProject keyとProject内の作成順に基づくissue keyへ移行する。
- APIはProject resourceに `project_key` を返す。Ticketの既存 `issue_key` 契約は維持する。

## 完了条件
- Project作成時にkeyが生成される。
- 同一ProjectではTicket番号が増加し、別Projectでは01から始まる。
- 既存Ticket cardは新しい `issue_key` をそのまま表示する。
- 関連Laravel/React検証が成功する。

## Handoff
- 状態: Project key、Project別採番、Seederの既存キー維持と再実行時のカウンター維持を実装済み。
- 検証: 専用SQLite DBへの全migrationとseedが成功。既存データのkey backfillを含むLaravel全109テスト、React全129テスト、TypeScript、ESLint、production build、変更PHPのPintが成功。Chromeで2 Projectを作成し、Alpha `JKZ-01` / `JKZ-02`、Beta `OSZ-01` のカード表示とProject名変更後のkey維持を確認。Seederの既存Ticket、再seed、削除後の番号非再利用も回帰テスト済み。
- 制約: 全体Pintは既存の `ProjectManagementTest.php` と `StoreTest.php` のフォーマット差分で失敗。今回変更したPHPファイルには問題なし。MySQL上でのmigrationは未検証。
- 次の作業: 最終diffを確認し、このChildの変更を承認済みの手順で親Epicへ統合する。
