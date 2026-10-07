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
- 状態: 実装完了、実行検証待ち
- 採用SHA: この文書更新commit
- 検証: Project key生成、Project別連番、既存データbackfillの自動テストを追加。実行環境がないため未実行。
- 残る制約・未検証事項: Laravel test/Pintを実行し、migrationのSQLite/MySQL互換と既存Ticket回帰を確認する。
