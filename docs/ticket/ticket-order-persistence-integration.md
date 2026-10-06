# Ticketカード順序永続化 統合

## 目的
検証済みの `feature/ticket-order-persistence` を最新の `feature/ticket` へ安全に統合し、競合解消後の回帰を検証する。

## 基準
- `AGENTS.md` を最優先とする。
- 統合元: `feature/ticket-order-persistence`
- 統合先の基準: このブランチ（`feature/ticket` から作成）
- 元の2ブランチは変更しない。
- 競合は現在のTicket仕様とorder persistenceの意図を両立させる。仕様判断が必要なら推測せず停止する。
- order persistence以外の機能追加・リファクタリングを混ぜない。

## 作業
1. 現在のbranchとgit statusを確認する。
2. `feature/ticket-order-persistence` をこのブランチへmergeする。
3. 競合ファイルだけを確認し、双方の意図を比較して最小限に解消する。
4. 最終diffでorder persistence以外の意図しない変更がないことを確認する。

## 検証
- LaravelのTicket関連テストを実行する。
- ReactのTicket関連テストを実行する。
- 必要なPHP syntax / Pint / TypeScript / ESLint / buildを実行する。
- 可能ならTicketボードの並び替え保存、再読込後の順序、stale board_version、フィルタ中DnD制御をブラウザで再確認する。
- 失敗は原因を特定して修正し、同じ検証を再実行する。
- 未実行は未検証として扱う。

## 完了条件
- merge conflictが残っていない。
- 関連テストと必要な静的検証が成功している。
- 最終diffとgit statusを確認している。
- 検証結果をこのMDへ必要最小限で記録する。
- この統合ブランチへcommit/pushする。
- `feature/ticket` へのmergeはユーザー承認なしに行わない。
