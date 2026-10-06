# Ticket Epic

## 概要
Laravel APIとReactによるProject単位のTicketボード。Epicは `feature/ticket`。

## Router

| 機能 | 担当ブランチ | 状態 |
|---|---|---|
| Ticketボード基盤 | `feature/ticket` | 実装済み |
| Projectアクセス・権限 | `feature/ticket-project-access` | 統合済み |
| カード順序永続化 | `feature/ticket-order-persistence` | 統合済み |
| Activity / History | 未定 | V1後候補 |

新機能はここに担当ブランチを追加してから、そのブランチで詳細を管理する。1作業単位より大きい機能は担当ブランチ側でさらに分割する。

## 統合
- 各機能は担当ブランチで実装・検証してからこのEpicへ統合する。
- 統合後は下位の関連テストを再実行し、Ticket全体の統合・回帰テストと必要な全体検証も行う。
- カード順序永続化の詳細仕様と検証結果は担当ブランチ側が所有する。
