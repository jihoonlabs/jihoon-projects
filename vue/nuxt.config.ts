// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2026-11-01',

  // Next.js 版と同じく、Laravel API を呼ぶクライアント専用 SPA として静的生成する
  ssr: false,

  modules: ['@pinia/nuxt', '@nuxt/eslint', '@nuxt/test-utils/module'],

  css: ['~/assets/styles/global.scss'],

  app: {
    head: {
      htmlAttrs: { lang: 'ja' },
      title: 'タスク管理',
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
