# jihoon-projects

Vue.jsを中心にフロントエンド開発に取り組んできた経験をもとに、React / Next.js と Laravel API を組み合わせた業務アプリケーションを個人開発しています。認証・権限確認、API境界でのデータ変換、Ticketボードの操作、テストまで、画面とAPIをつないだ実装をまとめています。

## メインプロジェクト：Ticket

Laravel API と React / Next.js で構成した、プロジェクト単位で利用するTicket管理アプリケーションです。

### 実装している機能

- Sanctumによるセッション認証（ログイン、登録、パスワード再設定）
- 投稿・お知らせのAPIとReact画面
- Ticketの一覧・作成・編集・削除、状態変更
- Ticketの検索・担当者フィルター・ドラッグ＆ドロップ
- Ticketコメントの作成・編集・削除
- コメントの編集・削除権限をAPI側で検証
- statefulなSPA APIに対するCSRFトークン検証

### 実装上の工夫

- **API境界の型とデータ変換:** Laravelのsnake_caseレスポンスとReactの画面モデルを分離し、API境界で変換しています。
- **認証・認可:** Sanctumのセッションを利用し、コメントの投稿者や編集・削除権限をサーバー側でも確認します。
- **ボード操作:** Ticketの状態変更や並び替えを画面から操作できます。カードの並び順は現在クライアント側で管理し、サーバーへの永続化は未実装です。
- **CSRF対策:** statefulなSPA APIでも通常のCSRF検証を適用し、トークンなしの状態変更が拒否されることをテストで確認しています。

## 技術スタック

- **フロントエンド:** Next.js 16、React 19、TypeScript、Zustand、dnd-kit
- **バックエンド:** Laravel 13、PHP 8.3、Laravel Sanctum、Socialite
- **テスト・品質確認:** Vitest、Testing Library、PHPUnit、ESLint、TypeScript、Pint

## テスト・検証記録

Ticket公開チェックポイントでは、次の検証を行いました。

- Laravel：85 tests、361 assertions
- React：112 tests
- TypeScript、ESLint、Pint、production build
- Chrome Headlessでログイン後のTicketおよびコメントの主要なCRUDフロー

これは該当チェックポイントに対する検証記録です。現在のブランチやリポジトリ全体、すべての実行環境での動作を保証するものではありません。

## リポジトリ構成

```text
laravel/       Laravel API、認証、DBマイグレーション、バックエンドテスト
react/         Next.jsアプリ、認証・投稿・お知らせ・Ticket UI
docs/ticket/   Ticketの仕様と検証記録
vue/           Vue関連の作業領域
micropython/   Thumby向けゲームの試作コード
```

## 開発プロセス

要件と作業範囲を整理し、生成AIを実装補助、レビュー、テスト観点の検討に活用しています。生成されたコードや設計案は人が確認し、テストと動作検証の結果をもとに変更を判断しています。
