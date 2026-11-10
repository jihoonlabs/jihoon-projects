// https://nuxt.com/docs/api/configuration/nuxt-config
import { APP_NAME } from './app/shared/utils/pageTitle';

export default defineNuxtConfig({
  compatibilityDate: '2026-11-01',

  // Next.js 版と同じく、Laravel API を呼ぶクライアント専用 SPA として静的生成する
  ssr: false,

  modules: ['@pinia/nuxt', '@nuxt/eslint', '@nuxt/test-utils/module'],

  css: ['~/assets/styles/global.scss'],

  // 機能ごとの composables も Nuxt の自動インポートに含める（components は名前の衝突を避けるため明示的に import する）
  imports: {
    dirs: ['features/*/composables'],
  },

  app: {
    head: {
      htmlAttrs: { lang: 'ja' },
      // 画面ごとの名前は各ページで pageTitle() から付ける
      title: APP_NAME,
      meta: [{ name: 'description', content: 'チケット管理アプリケーション' }],
    },
  },

  // API の接続先はここだけで定義し、画面やモジュールでは環境変数を直接読まない
  runtimeConfig: {
    public: {
      apiUrl: 'http://localhost:8000',
      demoMode: false,
    },
  },

  // Next.js 版（3000）と同時に起動できるようにする
  devServer: {
    port: 3001,
  },

  typescript: {
    strict: true,
  },

  devtools: { enabled: false },
});
