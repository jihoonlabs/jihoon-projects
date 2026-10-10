# Ticket preview 検証結果

ドラッグ保存が失敗したとき、同じProjectの別Ticketで成功していた編集・作成・削除まで消える問題を修正しました。手動status変更の失敗も画面内で処理します。

- React 140 tests、Laravel 136 tests / 638 assertions、TypeScript、ESLint、production build、Pintが通過しました。
- 実ブラウザーでログイン、Project切替、read権限、編集失敗後の入力保持と再保存、status失敗後の再試行、DnDの並べ替え・列移動・再読込・409再取得を確認しました。
- DnD失敗とTicket一覧再取得失敗を同時に起こし、成功済みの編集・作成・削除が維持されることも実ブラウザーで確認しました。
- CSRFログインの一時的な失敗は検証サーバーのCookie Path設定ミスでした。設定を直してログインでき、アプリコードは変更していません。
- MySQLの独立接続競争・row lockは環境がないため未検証です。詳細モーダルの最新データ再取得と編集競合検知も未実装です。

検証worktreeは `/private/tmp/ticket-preview-worktree`、branchは `ticket-preview`、基準SHAは `7504cb5a1ec7744ce2ad178518b46d5ab7f0c217` です。Ticket V1全体は未完了です。次の作業候補は、詳細画面からの編集・削除、ボタン/モーダル/カードのデザイン整理、タイトル領域の淡いProject色の検討、Project色の保存と完全一致色の重複防止（類似色は許可）です。これらは未着手です。詳しい結果は `TICKET_PREVIEW_VALIDATION_WORK.md` を参照してください。
