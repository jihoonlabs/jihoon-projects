import '@testing-library/jest-dom/vitest';

import { cleanup } from '@testing-library/vue';
import { afterAll, afterEach, beforeAll, beforeEach, vi } from 'vitest';

import { resetAppState } from './appState';
import { apiHandlers } from './mocks/handlers';
import { server } from './mocks/server';

const clearCookies = () => {
  for (const cookie of document.cookie.split('; ')) {
    const name = cookie.split('=')[0];

    if (name) {
      document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
    }
  }
};

beforeAll(() => {
  // Nuxt 自身がテスト用の同一オリジンへ送る内部要求だけを許可する。
  // 判定はテスト環境の起動時に一度だけ行い、Nuxt の文脈に依存しないようにする。
  const appOrigin = window.location.origin;

  server.listen({
    // 応答を定義していない外部への要求（Laravel API を含む）はテストを失敗させる
    onUnhandledRequest(request, print) {
      if (new URL(request.url).origin !== appOrigin) {
        print.error();
      }
    },
  });

  // テスト開始前に Nuxt が最初の画面遷移でセッションを確認するため、待ち受けと同時に既定の応答を入れる
  server.resetHandlers(...apiHandlers());
});

beforeEach(() => {
  // 前のテストの上書きを残さず、既定の応答から始める
  server.resetHandlers(...apiHandlers());
  resetAppState();
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  server.resetHandlers();
  clearCookies();
});

afterAll(() => {
  server.close();
});
