# Nuxt Frontend

Next.js 版（`react/`）と同じ Laravel API を使う Vue（Nuxt）フロントエンドです。現在は初期構成の段階です。

## 使用技術

- Nuxt 4（クライアント専用 SPA、静的生成）
- TypeScript
- Pinia
- CSS Modules（SFC の `<style module>`）+ Sass
- Vitest + @nuxt/test-utils + Testing Library + MSW
- pnpm

## セットアップ

依存関係をインストールします。

```bash
pnpm install
```

API の接続先は環境変数で上書きできます（既定値は `http://localhost:8000`）。

```env
NUXT_PUBLIC_API_URL=http://localhost:8000
```

Laravel 側では、Vue 版からの接続を許可するために `.env` に次を設定します。

```env
FRONTEND_VUE_URL=http://localhost:3001
SANCTUM_STATEFUL_DOMAINS=localhost:3000,localhost:3001
```

開発サーバーを起動します。Next.js 版（3000）と同時に起動できるよう、ポートは 3001 です。

```bash
pnpm dev
```

## コマンド

```bash
pnpm dev
pnpm generate
pnpm lint
pnpm typecheck
pnpm test:run
pnpm format:check
```
