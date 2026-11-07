import { defineVitestConfig } from '@nuxt/test-utils/config';

export default defineVitestConfig({
  test: {
    // Nuxt の実行環境（runtimeConfig・Pinia・ルーター）でコンポーネントを検証する
    environment: 'nuxt',
    environmentOptions: {
      nuxt: {
        // Next.js 版と同じ DOM 実装にそろえる
        domEnvironment: 'jsdom',
      },
    },
    setupFiles: ['./app/test/setup.ts'],
    include: ['app/**/*.test.ts'],
  },
});
