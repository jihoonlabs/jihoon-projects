# Ticket V1 統合検証

## 目的
現在の `feature/ticket` を最新の `main` と安全に統合し、Ticket V1として回帰検証できる状態にする。

## 基準
- `AGENTS.md` を最優先とする。
- このブランチは `feature/ticket` から作成した統合検証専用ブランチ。
- 元の `main` と `feature/ticket` は変更しない。
- Ticket V1の既存仕様を維持し、新機能・リファクタリングを混ぜない。
- 競合で複数の妥当な解決案、仕様差、意図不明がある場合は推測せず停止して報告する。
- `AGENTS.md` の競合は最新mainの正規版を基準とし、内容を弱体化・独自変更しない。

## 作業
1. 現在のbranchとgit statusを確認する。
2. 最新のremote状態を取得する。
3. `main` をこのブランチへmergeする。
4. 競合があれば双方の意図を比較し、Ticket V1を壊さない最小限の解消を行う。
5. `docs/ticket/TICKET_ORDER_PERSISTENCE.md` の古い「Epic統合待ち」状態を実態に合わせて最小限更新する。
6. 最終diffでTicket V1統合以外の意図しない変更がないことを確認する。

## 検証
- Laravelの全テストを実行する。
- Reactの全テストを実行する。
- PHP syntax / Pint / TypeScript / ESLint / production buildを必要な範囲で実行する。
- 可能ならブラウザでTicketの主要導線を回帰確認する。
- Project切替、read/write権限、assignee制約、コメント権限、カード順序保存、再読込、stale board_version、フィルタ中DnD制御を重点確認する。
- 失敗は原因を特定して修正し、同じ検証を再実行する。
- 未実行は未検証として扱う。

## 完了条件
- merge conflictが残っていない。
- 全関連テストと必要な静的検証が成功している。
- 実施したブラウザ確認と未実施項目を区別して記録している。
- 最終diffとgit statusを確認している。
- 検証結果をこのMDへ必要最小限で記録する。
- この統合ブランチへcommit/pushする。
- `feature/ticket` または `main` へのmergeはユーザー承認なしに行わない。

## 検証結果 (2026-10-06)
- **Merge Status**: `main` から `feature/ticket-v1-integration` への merge 完了（コンフリクトなし）
- **Laravel Backend Tests**: PASS (103 tests, 456 assertions)
- **Laravel Pint**: PASS (100 files checked)
- **React Frontend Tests**: PASS (22 test files, 128 tests)
- **ESLint & Build**: PASS (Next.js production build succeeded)
- **TICKET_ORDER_PERSISTENCE.md**: ステータス更新完了
## 次の作業
- 自動・静的検証は完了済み。次はブラウザ回帰確認だけを行う。
- 会社環境でブラウザ確認が可能なら、このブランチのまま実施する。環境準備の負担が大きい場合は無理に進めず未検証として残す。
- 重点確認: Project切替、read/write権限、assignee制約、コメント権限、カード順序保存と再読込、stale board_version、検索・担当者フィルタ中のDnD無効化。
- 実施した項目と結果だけをこのMDへ追記し、未実施項目を成功扱いしない。
- 問題が見つかった場合、明らかな既存仕様内の不具合は修正→関連テスト→再確認まで行う。仕様判断が必要なら停止して報告する。
- ブラウザ確認後、このブランチへcommit/pushする。
- `feature/ticket` への最終mergeとV1完了判断はユーザー承認後に行う。
