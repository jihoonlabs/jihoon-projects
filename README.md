# jihoon-projects

Webアプリケーション開発を中心としたポートフォリオです。Laravel APIとReact/Next.jsを連携し、認証付きの業務アプリケーション機能を開発しています。

## 技術スタック

- フロントエンド: Next.js 16、React 19、TypeScript、Zustand
- バックエンド: Laravel 13、PHP 8.3、Laravel Sanctum、Socialite
- テスト・品質確認: Vitest、Testing Library、PHPUnit、ESLint、TypeScript
- Ticketボード: dnd-kit

## 実装済みの機能

- Sanctumのセッション認証を使ったログイン、登録、パスワード再設定などの認証機能
- 投稿・お知らせのAPIとReact画面
- Ticketボードの一覧・作成・編集・削除、状態変更、検索、担当者フィルター、ドラッグ＆ドロップ
- Ticketコメントの作成・編集・削除。投稿者と編集・削除権限はAPI側で検証
- statefulなSPA APIに対するCSRFトークン検証

TicketボードはLaravel APIとReactの型・データ変換を分離しています。カードの並び順は現在クライアント側で管理し、サーバーには保存しません。

## 開発中・未実装

Ticket機能はEpicとして継続開発中です。カード順序のサーバー永続化、担当者候補の拡充、管理者機能は未実装です。今後の変更は機能単位で検証し、実装済みの範囲と区別して公開します。

## テスト・検証

Ticket公開チェックポイントでは、Laravel 85テスト（361 assertions）、React 112テスト、TypeScript、ESLint、Pint、production buildを確認しています。実ブラウザーでログイン後のTicketおよびコメントの主要なCRUDフローも確認済みです。これらは現在のTicketチェックポイントに対する結果であり、リポジトリ全体のすべての機能・環境を保証するものではありません。

## ディレクトリ構成

```text
laravel/       Laravel API、認証、DBマイグレーション、バックエンドテスト
react/         Next.jsアプリ、認証・投稿・お知らせ・Ticket UI
docs/ticket/   Ticket Epicの現在の仕様・実装・検証状況
vue/           Vue用の作業領域（現在は未実装）
micropython/   Thumby向けゲームの試作コード
```

## 開発プロセス

要件と作業範囲を整理したうえで、生成AIを実装補助、レビュー、テスト観点の検討に活用しています。設計や生成されたコードを確認し、テストと動作検証の結果に基づいて変更を判断しています。
