# jihoon-projects

Vue.jsを主軸としたフロントエンドの実務経験を土台に、React / Next.js と Laravel API を組み合わせた業務アプリケーションを個人開発しています。実務で培ったUI開発の経験を異なるスタックへ応用し、認証・認可、API連携、テスト、生成AIを活用した開発プロセスまで取り組んだ内容を紹介します。

## メインプロジェクト：Ticket

社内利用を想定した、プロジェクト・メンバー・チケットを管理するWebアプリケーションです。React / Next.jsの画面とLaravel APIを連携し、認証や権限確認を含む一連の操作を実装しています。

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

### 技術上の工夫

- **権限をAPI側でも確認:** プロジェクト所属、閲覧・編集権限、コメント所有権をサーバー側で検証します。
- **API境界でデータ変換:** Laravelのsnake_case応答とReactの画面モデルを分離し、API境界で変換します。
- **更新競合への対応:** チケットの状態と列内の並び順をサーバーに保存します。移動時にはボードのバージョンを比較し、古い状態からの更新を競合として扱います。
- **品質確認:** 認証付きSPA APIのCSRF検証を行い、トークンなしの状態変更が拒否されることをテストで確認しています。

[機能別V1マニュアル](docs/ticket/README.md)では操作方法を、[Ticket開発・検証記録](docs/ticket/TICKET.md)では公開範囲、実装上の前提、検証記録を説明しています。公開V1の範囲や既知の制約も開発記録に記載しています。

## 技術スタック

- **フロントエンド:** Next.js、React、TypeScript、Zustand、dnd-kit
- **バックエンド:** Laravel、PHP、Laravel Sanctum、Socialite
- **品質確認:** Vitest、Testing Library、PHPUnit、ESLint、TypeScript
- **開発プロセス:** Git、生成AIを活用した実装補助・レビュー・検証

## テスト・検証記録

2026年10月18日のプロジェクト一覧ダイアログ改善では、React 248 tests、Laravel 158 tests（1,624 assertions）、TypeScript、ESLint、production buildを確認しました。Chrome HeadlessとローカルAPIでは、ログイン、一覧の開閉、Escape後のフォーカス復帰、プロジェクト選択・作成、幅390pxでの表示を確認しています。

これは記録されたチェックポイントの検証結果です。メールの実配送、外部OAuth、本番環境での動作はこの確認に含みません。また、現ブランチでテストを再実行した結果ではありません。

## AIを活用した開発プロセス

生成AIをコード生成だけでなく、作業範囲の整理、レビュー、テスト観点の検討にも活用しています。公開資料では、作業の状態管理や検証、レビュー、統合の進め方を紹介しています。

- [AGENTS v2.1](docs/agent/AGENTS-v2.1.md)
- [WORK v2.1](docs/agent/WORK-v2.1.md)
- [MANUAL v2.1](docs/agent/MANUAL-v2.1.md)

設計や生成されたコードは人が確認し、テストと動作確認の結果をもとに変更を判断しています。

## リポジトリ構成

```text
laravel/       Laravel API、認証、DBマイグレーション、バックエンドテスト
react/         Next.jsアプリ、認証・投稿・お知らせ・Ticket UI
docs/ticket/   Ticket V1の機能別マニュアルと開発・検証記録
docs/agent/    公開エージェント構成のポートフォリオ保存例
micropython/   趣味のMicroPython・Thumby制作
vue/           Vue関連の作業領域
```
