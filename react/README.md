技術スタック (Tech Stack)
フレームワーク: Next.js (App Router)

言語: TypeScript

状態管理: Zustand

スタイリング: SCSS Modules

パッケージマネージャー: pnpm

セットアップ (Getting Started)
前提条件 (Prerequisites)
Node.js および pnpm がインストールされていることを確認してください。

クイックスタート (Quick Start)
依存関係のインストール

コマンド: pnpm install

ビルドスクリプトの承認 (セキュリティポリシーで求められた場合のみ)

コマンド: pnpm approve-builds

開発サーバー起動

コマンド: pnpm dev

ブラウザで http://localhost:3000 を開いて確認します。

利用可能なスクリプト (Available Scripts)
pnpm dev — ローカル開発サーバー起動 (localhost:3000)

pnpm build — プロダクション用にアプリケーションをビルド

pnpm start — ビルド後にプロダクションサーバーを起動

pnpm lint — コードクオリティチェック (ESLint)

ディレクトリ構造 (Project Structure)
react/
├── public/ # 静的ファイル (ファビコン、パブリックメディア)
└── src/
├── app/ # App Router ページ & レイアウト
├── assets/ # スタイル & ローカルメディア
├── components/ # UI コンポーネント
└── store/ # 状態管理

Git ワークフロー (Development Workflow)
main — 安定した本番コードベース

feature/* — 機能開発および実験用ブランチ (例: feature/dashboard)

ライセンス (License)
社内開発および学習目的で管理されています。
