# Ticket Epic

## 目的と範囲

Laravel API と React による Jira 形式の Ticket ボードを提供する。Epic の基準ブランチは `feature/ticket`。Ticket CRUD、ボード操作、コメント機能を統合する。

## 確定事項

- Laravel API の応答は snake_case とし、React は API 応答型と画面モデルを分離して API 境界で変換する。
- `position` はクライアント側の並び替えに使用する。永続化は未実装。
- コメント作成者は Sanctum のログインユーザーから決定し、他ユーザーのコメント編集・削除はサーバーで拒否する。
- Ticket 担当者の全ユーザー検索、管理機能、カード順序の DB 永続化は本範囲外。

## 現在の実装

- Laravel: Ticket の一覧・詳細・作成・更新・状態変更・削除 API と、コメントの一覧・作成・更新・削除 API。
- React: Ticket ボード、検索・担当者フィルター、DnD と手動状態変更、作成・編集・削除 UI、コメント UI。
- Ticket API の snake_case/camelCase 変換、楽観更新の失敗時復元、コメントの認証・所有者検査を実装。

## 検証状態

- `feature/ticket-complete` と `feature/ticket-comments` の変更は本ブランチで順番に統合済み。
- Laravel全テスト 83件、React全テスト 112件、TypeScript、ESLint、Pint、production build は通過。
- テストで判明したボードテストのコメントAPI mock不足・曖昧なアクセシビリティ検索を修正した。Ticket modal の初期値をpropsから設定し、対象Ticket変更時に再生成することでESLint違反も解消した。
- 初回Laravelテストは隔離環境にAPP_KEYがなく失敗したため、一時環境変数を設定して再実行した。初回buildはGoogle Fonts取得に失敗したが、ネットワーク許可後の再実行で成功した。
- Laravel Sanctum のセッション認証には `token` Cookie がないため、古い Cookie 判定を行う `middleware.ts` を削除した。保護画面は既存の `/api/auth/me` による `AuthInitializer` と `DashboardLayout` の認証状態で制御する。
- middleware 相当の認証動作テストで、認証済みユーザーの保護画面表示と未認証ユーザーの `/login` リダイレクトを確認した。
- Chrome Headless 154 で実ログイン後の Ticket 一覧・作成・編集・状態変更・再読み込み後の保持・削除、およびコメント作成・編集・削除を確認した。各変更は Laravel API に反映され、最後に Ticket が0件であることを確認した。

## 次の作業

1. 既存の `feature/ticket` worktreeにある未コミット変更を保持したまま、統合結果を同Epicブランチへ安全に反映する。
2. Epicブランチへ反映後、最終diffと検証状態を確認する。
