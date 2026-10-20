# jihoon-projects

Vueを中心としたフロントエンドの実務経験を基盤に、React / Next.js と Laravel による業務アプリケーションを個人開発しています。生成AIを実装支援に活用し、コード・テスト・動作確認で成果を検証しています。

メインプロジェクトの **Ticket** は、チーム内のタスク・担当者・進捗を共有するためのチケット管理アプリです。社内利用を目標に開発しており、このリポジトリではV1のコード、画面、利用手順、テストを公開しています。

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

### 実装で確認できる工夫

- **権限:** 画面の表示制御に加え、APIでも所属・編集権限を検証。処理中に権限が変わるケースもテストしています。
- **同時編集:** バージョンを比較し、古い画面からの更新を409で検出。並び替え後の競合も検証しています。
- **非同期UI:** 遅い一覧応答やログアウト前の処理が、新しい画面状態を上書きしないよう制御しています。

[設計・テストの具体例](docs/ticket/TICKET.md#設計とテストの具体例)から実装とテストを確認できます。操作方法は [機能別V1マニュアル](docs/ticket/README.md)、実行環境は [React](react/README.md) / [Laravel](laravel/README.md) を参照してください。

### 検証結果

2026-10-20、コミット `fe40e95` の [GitHub Actions](https://github.com/jihoonlabs/jihoon-projects/actions/runs/39352159731) で次を確認しました。

| フロントエンド | バックエンド |
| --- | --- |
| React 250 tests、TypeScript、ESLint、production build通過 | Laravel 158 tests・1,624 assertions通過（PHP 8.4 / SQLite） |

外部OAuth・メール実配送・本番DBでの負荷や同時実行はこのCIの対象外です。[検証範囲と再実行手順](docs/ticket/TICKET.md#自動検証と再実行)を公開しています。

## AIを活用した開発プロセス

AI支援を取り入れながら、作業範囲と検証結果を管理しています。過去の公開例は [AGENTS v2.1](docs/agent/AGENTS-v2.1.md)、[WORK v2.1](docs/agent/WORK-v2.1.md)、[MANUAL v2.1](docs/agent/MANUAL-v2.1.md) を参照してください。これらは保存資料であり、現在の作業指示ではありません。現在の内部運用資料は公開対象外です。

## 技術スタック

- **フロントエンド:** Next.js、React、TypeScript、Zustand、dnd-kit
- **バックエンド:** Laravel、PHP、Laravel Sanctum、Socialite
- **品質確認:** Vitest、Testing Library、PHPUnit、ESLint、TypeScript
- **開発プロセス:** Git、AI支援開発、作業範囲と検証記録の管理

## その他の制作：Thumby Brawl Base

72×40の白黒Thumby向けに、MicroPythonで1対1アクションRPGのベースを制作しています。AI支援開発を小型ゲームに適用する実験です。開発中のため、PCテストと実機での確認範囲を分けています。

概要・操作・テストは [公開マニュアル](docs/thumby-brawl-base/MANUAL.md)、コードは [Thumby Brawl Base](micropython/Thumby/ThumbyBrawlBase/) を参照してください。

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

公開V1の範囲と制約は [Ticket開発・検証記録](docs/ticket/TICKET.md) にまとめています。
