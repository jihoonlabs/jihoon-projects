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

- Laravel の `api/*` CSRF 例外を削除し、stateful Sanctum API でも通常の CSRF 検証を適用する。
- 回帰テストで有効な CSRF トークン付き状態変更が成功し、トークンなしの状態変更が `419` で拒否されることを確認。
- Laravel 全テスト 85件（361 assertions）、React 全テスト 112件、TypeScript、ESLint、Pint、production build が通過。
- Chrome Headless 154 でログイン後、Ticket 一覧・作成・編集・状態変更・再読み込み後の保持・削除、コメント作成・編集・削除を確認。最後に Ticket が0件であることを確認。

## 次の作業

1. この変更の最終 diff を確認し、ユーザーと `main` への統合可否を判断する。
