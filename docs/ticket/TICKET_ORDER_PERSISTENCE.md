# Ticket Order Persistence Child

## 目的と範囲
Ticketボードのカード順序をDB/APIへ永続化する。対象ブランチは `feature/ticket-order-persistence`。
このMDはChild専用の作業コンテキストであり、Epicへはmergeせず、完了時に必要な確定結果だけをEpic MDへ反映する。

## 確定事項
- 順序はProject・status単位で全ユーザー共有とする。
- Ticketは `position`、Projectは `board_version` を保持する。
- 同一列内の並び替えと列間DnDを保存する。
- 新規作成と通常のステータス変更は移動先列の末尾へ追加する。
- DnDは `PATCH /api/tickets/{ticket}/move` を使用し、`status`・`position`・`board_version` を送る。
- Projectをtransaction内で `lockForUpdate()` し、古いversionは409で拒否する。
- 順序を変える作成・削除・ステータス変更・DnDでは `board_version` を更新する。
- 検索または担当者フィルター中はDnDを無効にし、手動ステータス変更は許可する。

## 実装状態
- tickets.position / projects.board_version migrationを追加。
- Laravel Resourceへposition / board_versionを追加。
- 作成・削除・通常ステータス変更の順序維持を実装。
- move APIと同一列・列間の再採番、409競合処理を実装。
- React API境界をサーバーpositionへ変更し、move APIを追加。
- BoardのDnDを永続化APIへ接続し、フィルター中のDnD無効化を実装。
- Laravel BoardOrderTestを追加し、削除後の再採番とboard_version更新も対象化。
- Project lock取得後にTicketを再取得し、並行更新時も最新statusを基準に処理する。
- Reactはサーバーpositionを正とし、順序変更後はwrite完了後に一度だけ再取得して同期する。

## 検証状態
- Epicとの差分はカード順序永続化関連ファイルのみで、ChildはEpicよりahead、behindなしを確認済み。
- Laravel/Reactの実行テスト、TypeScript、ESLint、production build、ブラウザー動作確認は未実施。
- main/Epicへの統合は未実施。

## 未完了と次の作業
- このChildではカード順序永続化だけを扱い、他のTicket機能や別Childの詳細は持ち込まない。
- React既存テストへの型・fixture影響を確認し、必要なテストを追加・修正する。
- Laravel BoardOrderTestを含む関連テストを実行する。
- TypeScript、ESLint、production buildを実行する。
- 同一列DnD、列間DnD、409後の再取得、フィルター中DnD無効、手動ステータス変更をブラウザーで確認する。
- 全検証後に最終diffを確認し、Epic統合可否を判断する。
