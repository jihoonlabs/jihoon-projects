# Next.js Frontend

Laravel APIと連携するNext.jsフロントエンドです。

## 使用技術

- Next.js
- TypeScript
- Zustand
- CSS Modules
- pnpm

## セットアップ

依存関係をインストールします。

```bash
pnpm install
```

環境に応じてAPIのURLを設定してください。

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

開発サーバーを起動します。

```bash
pnpm dev
```

ブラウザで `http://localhost:3000` を開いてください。

## コマンド

```bash
pnpm dev
pnpm build
pnpm lint
pnpm test:run
```