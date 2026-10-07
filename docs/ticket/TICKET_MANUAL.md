# Ticket V1 完了状態

## 目的と結果
小規模チームがProject単位でTicketを作成・担当・整理・完了できる業務フローを提供します。Project権限、カード順序の保存、Projectごとの不変な3文字keyとTicket連番をEpicへ統合済みです。

## 利用上の動作
- readメンバーは閲覧、writeメンバーはTicket更新、leaderはメンバー管理を行えます。
- Projectごとに `KEY-01`, `KEY-02` と採番し、Project名の変更やseed再実行で既存key・番号を変更しません。
- Kanbanの並び順を保存し、古いboard versionで更新された場合は再同期します。

## 根拠と制約 (2026-10-08)
- 今回のリモート環境でLaravel 109 tests / 487 assertions、Pint、React 129 tests、TypeScript、ESLint、production buildが成功しました。一時SQLiteで全migrationとseed再実行時のkey・counter維持も確認しました。
- 過去のChrome確認ではProject間のkey独立と名前変更後のkey維持、V1の主要操作を確認済みです。今回Chrome確認は再実行していません。
- MySQL migrationは未検証です。MySQLを使う環境への適用前に確認が必要です。現在の依存lockfileを使うPHP環境は8.4以上が必要です。

## 現在の完了状態
Epic `f18cfd7` とmain `59b27f2` の統合シミュレーションは競合なしで、mainの作業規則・文書も保持できます。mainへの統合準備は完了しましたが、main merge/pushとブランチ削除は未承認・未実行です。正確なSHAと再開条件は `TICKET_MAIN_INTEGRATION.md` を参照してください。
