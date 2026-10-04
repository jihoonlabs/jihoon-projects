# Ticket Epic

## 目的と範囲
Laravel APIとReactによるProject単位のTicketボード。Epicは `feature/ticket`。

## 確定事項
- APIはsnake_case、ReactはAPI境界で画面モデルへ変換する。
- global roleはuser/admin、Project roleはleader/member、permissionはread/write。
- readは閲覧とコメント、writeはTicket CRUD・状態・担当者変更。leader/adminはメンバー管理、Project CRUDはadminのみ。
- コメント編集は投稿者のみ。削除は投稿者またはadmin。
- 担当者は同一Projectメンバーのみ。既存Ticketと移行時active userはGeneralへ移行し、新規userは自動参加しない。
- positionはクライアント内のみ。DB/API永続化は未実装。

## 現在の実装
- Ticket CRUD、検索・担当者フィルター、DnDによる列移動、手動状態変更、コメント。
- Project選択、メンバー管理、read/write別UIとサーバー権限境界。
- Sanctum/CSRF、APIモデル変換、楽観更新失敗時の復元。
- Project Access Childを2026-10-05にfast-forward統合。統合先は `767e3f6af6071192fc3ef828650eb78f418147c1`。main統合・Child削除は未実施。

## 検証状態
- 家のCodexで実装commit `129145e` を検証：Laravel 97 tests / 431 assertions、React 124 tests、Pint、TypeScript、ESLint、production build通過。
- 家の一時SQLite/Chrome環境でProject切替、leaderのメンバー管理、Ticket CRUD・状態・担当者、コメント、read制限を確認。
- 今回の遠隔統合は検証済みChildと同じコードへfast-forward。ローカルGitで統合可能性とdiff --checkを確認。
- 遠隔環境にはPHPがなく、Laravel全テスト・ブラウザー検証の再実行は未実施。共有/本番DB migrationとdeployも未検証。

## 次の作業と設計判断
次の候補はカード順序のDB/API永続化。実装前に以下を確定する。
- 保存単位：Project・statusごとに全員共有する順序を推奨。個人別順序は別設計となる。
- 最初の範囲：列移動・新規作成時の末尾順序保存のみ、または同一列内DnD並び替えまで実装。
- 同時更新：トランザクションで直列化して最後の操作を反映、またはversionで古い操作を409拒否して再取得。
- 検索/担当者フィルター中の並び替えは非表示カードを保持する必要がある。初版ではフィルター中の並び替えを無効にする案。
コード確認：Board/ViewのhandleDragEndは状態だけを更新し、storeは同じstatusへの移動を無視する。同一列内の任意順序変更は現在未実装。Laravel一覧はid昇順。
新設計確定後にEpicからChildを作成する。Activity/HistoryはV1後の候補。
