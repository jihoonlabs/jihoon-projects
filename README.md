# jihoon-projects

フロントエンド開発の経験を基盤に、React / Next.js と Laravel による業務アプリケーション開発、生成AIを活用した開発プロセスの設計・自動化・品質向上に取り組んでいます。

メインプロジェクトは、社内利用を目標とする **Ticket（Project単位のタスク管理システム）** です。Thumby向けゲーム制作は趣味・技術検証として取り組んでいます。

## メインプロジェクト：Ticket

社内での実利用を想定した、プロジェクト・チケット管理アプリケーションを開発しています。React / Next.js と Laravel を使用し、ログイン・認証、権限管理、チケットの作成・編集・削除、ステータス管理などの基本機能を実装しています。

開発状況の詳細は [Ticketの開発記録](docs/ticket/TICKET.md) にまとめています。

## AIを活用した開発プロセス

AIを単なるコード生成補助として使うだけでなく、複数のAI・開発環境をまたぐ作業分担、責任範囲、作業状態の引き継ぎ、テストと統合の判断を整理し、再現可能な開発フローを目指しています。

- AGENTS / WORK形式を使った作業の入口と責任範囲の整理（公開資料は当時の例）
- Gitブランチ単位での実装・レビュー・検証・統合
- 実行結果に基づく検証済み／未検証の区別
- 長い会話履歴に依存しない作業再開の改善

公開可能な構成・成果はこのリポジトリで紹介し、内部運用の詳細は公開対象に含めていません。AIによる完全自律開発を達成したという意味ではありません。

公開ポートフォリオ資料: [AGENTS v2.1](docs/agent/AGENTS-v2.1.md)、[WORK v2.1](docs/agent/WORK-v2.1.md)、[MANUAL v2.1](docs/agent/MANUAL-v2.1.md)。これらは公開エージェント構成の保存例です。現在のリポジトリ作業用のCodex指示としては扱いません。

## 技術スタック

- **フロントエンド:** Next.js、React、TypeScript、Zustand、dnd-kit
- **バックエンド:** Laravel、PHP、Laravel Sanctum、Socialite
- **品質確認:** Vitest、Testing Library、PHPUnit、ESLint、TypeScript
- **開発プロセス:** Git、AI支援開発、AGENTS / WORK

## 趣味のAI開発・実験：Thumby

`micropython/` では、Thumby向けMicroPythonゲーム制作を題材に、ローカルAI（Ollama）を利用した開発環境・作業フローを実験しています。AIによる実装支援や作業の引き継ぎを試しながら、小型デバイスの制約下でゲームを開発する趣味のプロジェクトです。AIによる自律的な開発フローは検証中であり、完成・実証済みとは扱いません。メインのTicketとは区別して掲載しています。

## リポジトリ構成

```text
laravel/       Laravel API、認証、DBマイグレーション、バックエンドテスト
react/         Next.jsアプリ、認証・投稿・お知らせ・Ticket UI
docs/ticket/   Ticketの開発・採用・検証記録
docs/agent/    公開エージェント構成 v2.1 のポートフォリオ保存例
micropython/   Thumby向けゲームの試作
vue/           Vue用の作業領域（現在は未実装）
```

機能の採用状況と検証範囲はブランチごとに異なります。READMEの概要だけで本番利用可能と判断せず、対象ブランチのコードと検証記録を確認してください。
