# jihoon-projects

フロントエンド開発の経験を基盤に、React / Next.js と Laravel による業務アプリケーション開発、生成AIを活用した開発プロセスの設計と改善に取り組んでいます。

メインプロジェクトは、社内利用を目標に開発している **Ticket** です。プロジェクト単位のチケット管理、メンバー権限、コメントを備えています。公開情報はこのリポジトリで確認できるV1機能を対象にしています。

## メインプロジェクト：Ticket

- Sanctumセッション認証
- プロジェクト作成、メンバー管理、閲覧・編集権限
- チケットの作成・編集・削除、ステータスと優先度、担当者設定
- 検索、担当者フィルター、ドラッグ＆ドロップ
- コメント、プロジェクトの終了・復元

### 画面イメージ

| チケットボード | ログイン画面 |
| --- | --- |
| [<img src="docs/ticket/images/ticket-board-v1.png" alt="Ticket V1のプロジェクト選択、検索・担当者フィルターとカンバンボード" width="560">](docs/ticket/images/ticket-board-v1.png) | [<img src="docs/ticket/images/login-v1.png" alt="Ticket V1のメールログイン、パスワード表示切替、Google・LINEログインボタン" width="280">](docs/ticket/images/login-v1.png) |
| プロジェクトごとにチケットの状態・優先度・担当者を確認できます。 | メールでのログインと、登録・パスワード再設定への入口です。 |

ローカル環境のデモ画面です。画像をクリックすると元のサイズで表示できます。

[機能別V1マニュアル](docs/ticket/README.md)では操作方法を説明し、[Ticket開発・検証記録](docs/ticket/TICKET.md)では公開範囲、実装上の前提、過去の検証記録を説明しています。操作説明と開発記録を分け、テスト記録が現在の全環境を保証するものではないことも明記しています。

## AIを活用した開発プロセス

AIをコード生成だけに使わず、作業範囲、検証、レビュー、統合を整理しながら開発しています。公開されたエージェント資料は [AGENTS v2.1](docs/agent/AGENTS-v2.1.md)、[WORK v2.1](docs/agent/WORK-v2.1.md)、[MANUAL v2.1](docs/agent/MANUAL-v2.1.md) に保存しています。これらは当時の公開ポートフォリオ例であり、現在のリポジトリ作業用Codex指示ではありません。内部AI向けの作業指示や引き継ぎ内容は公開資料に含めていません。

この取り組みはAIによる完全自律開発を達成したという意味ではありません。実装と判断を確認し、テストや動作確認の結果に基づいて変更しています。

## 技術スタック

- **フロントエンド:** Next.js、React、TypeScript、Zustand、dnd-kit
- **バックエンド:** Laravel、PHP、Laravel Sanctum、Socialite
- **品質確認:** Vitest、Testing Library、PHPUnit、ESLint、TypeScript
- **開発プロセス:** Git、AI支援開発、作業範囲と検証記録の管理

## Thumbyゲームとエージェント開発の試験

`micropython/Thumby/ThumbyBrawlBase/` では、個人で整備しているエージェント用Markdownの作業基準を使い、Thumby向けゲームのベースを開発しています。ユーザーが方向と要件を決め、エージェントが実装・テストを支援する進行です。これは完成ゲームの紹介ではなく、エージェント作業基準を実際の開発成果につなげる試験プロジェクトです。公開するゲームコードと利用案内を掲載しています。

ゲームの概要、操作、テストと未確認事項は [Thumby Brawl Base README](micropython/Thumby/ThumbyBrawlBase/README.md) と [公開マニュアル](docs/thumby-brawl-base/MANUAL.md) を参照してください。

## リポジトリ構成

```text
laravel/       Laravel API、認証、DBマイグレーション、バックエンドテスト
react/         Next.jsアプリ、認証・投稿・お知らせ・Ticket UI
docs/ticket/   Ticket V1の機能別マニュアルと開発・検証記録
docs/agent/    公開エージェント構成のポートフォリオ保存例
docs/thumby-brawl-base/  Thumby Brawl Baseの公開マニュアル
micropython/   Thumby向けゲームの試作
vue/           Vue用の作業領域（現在は未実装）
```

機能の採用状況と検証範囲はブランチごとに異なります。READMEの概要だけで本番利用可能と判断せず、対象ブランチのコードと検証記録を確認してください。
