# jihoon-projects

Vue.jsを主軸に6年以上のフロントエンド実務経験があり、Nuxt 2からNuxt 3への移行などに取り組んできました。このリポジトリでは、実務で培ったフロントエンドの知見を土台に、React / Next.js と Laravel API を使った業務アプリケーションを個人開発しています。

**実務経験の中心はVue.js / TypeScriptです。React / Next.js、Laravelはこのポートフォリオで設計・実装した個人開発の経験として紹介しています。**

## メインプロジェクト：Ticket

社内利用を想定した、プロジェクト・メンバー・チケット管理アプリケーションです。認証付きのReact / Next.js画面とLaravel APIを連携し、権限管理からチケット操作、コメントまでを実装しています。

- Sanctumによるセッション認証
- プロジェクトの作成・検索・選択、メンバー管理、閲覧・編集権限
- チケットの作成・編集・削除、ステータス・優先度・担当者の管理
- 検索、担当者フィルター、ドラッグ＆ドロップ
- コメントの作成・編集・削除
- プロジェクトの終了・復元

### 動作デモ

![Ticketの操作デモ：ログインからプロジェクト作成、チケット追加・ドラッグ移動・削除、ブラウザー再読み込み後の選択プロジェクト維持](docs/ticket/images/ticket-demo-clean.gif)

### 画面イメージ

| チケットボード | ログイン画面 |
| --- | --- |
| [<img src="docs/ticket/images/ticket-board-v1.png" alt="Ticket V1のプロジェクト選択、検索・担当者フィルターとカンバンボード" width="560">](docs/ticket/images/ticket-board-v1.png) | [<img src="docs/ticket/images/login-v1.png" alt="Ticket V1のメールログイン、パスワード表示切替、Google・LINEログインボタン" width="280">](docs/ticket/images/login-v1.png) |
| プロジェクトごとにチケットの状態・優先度・担当者を確認できます。 | メールでのログインと、登録・パスワード再設定への入口です。 |

ローカル環境で撮影した画面です。画像をクリックすると元のサイズで表示できます。

### 設計・実装で取り組んだこと

- **サーバー側の権限確認:** プロジェクト所属、閲覧・編集権限、コメント所有権をAPI側でも検証します。
- **API境界の整理:** Laravelのsnake_case応答とReactの画面モデルを分離し、API境界で変換します。
- **更新競合への対応:** チケットの状態と列内の並び順をサーバーに保存し、ボードのバージョンを使って古い状態からの更新を検知します。
- **CSRF対策:** statefulなSPA APIでもCSRF検証を適用し、トークンなしの状態変更が拒否されることをテストで確認しています。

[機能別V1マニュアル](docs/ticket/README.md)では操作方法を、[Ticket開発・検証記録](docs/ticket/TICKET.md)では公開範囲、実装上の前提、検証内容を紹介しています。

## 技術スタック

- **フロントエンド:** Next.js、React、TypeScript、Zustand、dnd-kit
- **バックエンド:** Laravel、PHP、Laravel Sanctum、Socialite
- **品質確認:** Vitest、Testing Library、PHPUnit、ESLint、TypeScript
- **開発プロセス:** Git、生成AIを活用した実装補助・レビュー・検証

## テスト・検証実績

2026年10月18日の記録では、React 248 tests、Laravel 158 tests（1,624 assertions）、TypeScript、ESLint、production buildを確認しています。Chrome HeadlessとローカルAPIを使い、ログイン、プロジェクト一覧の操作、選択・作成、幅390pxでの表示も確認しました。

詳細な対象範囲と検証条件は[開発・検証記録](docs/ticket/TICKET.md)に記載しています。

## AIを活用した開発プロセス

生成AIをコード生成だけでなく、作業範囲の整理、レビュー、テスト観点の検討にも活用しています。作業を小さな単位に分け、検証結果を確認してから統合する進め方を、公開資料にまとめています。

- [AGENTS v2.1](docs/agent/AGENTS-v2.1.md)
- [WORK v2.1](docs/agent/WORK-v2.1.md)
- [MANUAL v2.1](docs/agent/MANUAL-v2.1.md)

AIの生成結果や設計案は人が確認し、テストと動作確認をもとに変更を判断しています。

## リポジトリ構成

```text
laravel/       Laravel API、認証、DBマイグレーション、バックエンドテスト
react/         Next.jsアプリ、認証・投稿・お知らせ・Ticket UI
docs/ticket/   Ticket V1の機能別マニュアルと開発・検証記録
docs/agent/    公開エージェント構成のポートフォリオ保存例
micropython/   趣味のMicroPython・Thumby制作
vue/           Vue関連の作業領域
```
