# Ticket V1 統合検証

## 目的と範囲
- `feature/ticket-v1-integration` 上で Ticket V1 の既存仕様を最新 `main` と統合し、回帰を確認する。
- `feature/ticket` と `main` への統合、ブランチ削除、新機能追加はこの作業範囲に含めない。

## 現在の状態
- `origin/main` (`53b268d`) を2026-10-07に競合なく取り込み済み。統合コミットは `d96e1fe`。
- ブラウザー確認で、DnD無効状態をカード全体の `aria-disabled` で表すと、カード内の手動状態変更やreadメンバーの詳細操作まで無効扱いになる回帰を確認し、カードラッパーから同属性を外した。DnD自体は `useSortable` のdisabled設定で制御する。
- 検索中の手動状態変更とreadメンバーのカード操作を確認するReact回帰テストを追加した。

## 検証結果 (2026-10-07)
- Laravel: 全103テスト・456 assertions、Pint、PHP syntax checkが成功。
- React: 全22テストファイル・129テスト、TypeScript、ESLint、production buildが成功。
- Chromeブラウザー回帰: 未ログイン時の保護、Sanctumログイン、Project切替、leaderによるメンバー権限変更・追加・削除、read/write UI/API権限、assignee制約、Ticket CRUD、コメントCRUD、同列/列間DnDと再読込、stale `board_version` の409と再同期、検索・担当者フィルター中のDnD停止、検索中の手動状態変更を確認。
- ブラウザー用データは一時SQLiteと一時Chrome contextに限定し、既存 `.env` とDBは使用していない。

## 次の作業
- `feature/ticket` / `main` への統合は別途承認後に行う。
