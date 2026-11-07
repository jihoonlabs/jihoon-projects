import '@testing-library/jest-dom/vitest';

import { cleanup } from '@testing-library/vue';
import { afterAll, afterEach, beforeAll, beforeEach } from 'vitest';

import { apiHandlers } from './msw/apiHandlers';
import { apiUrl } from './msw/apiUrl';
import { server } from './msw/server';

const clearCookies = () => {
  for (const cookie of document.cookie.split('; ')) {
    const name = cookie.split('=')[0];

    if (name) {
      document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
    }
  }
};

beforeAll(() => {
  server.listen({
    // Laravel API への未定義の要求はテストを失敗させる。
    // Nuxt 自身の内部要求など API 以外は対象外にする。
    onUnhandledRequest(request, print) {
      if (request.url.startsWith(apiUrl('/'))) {
        print.error();
      }
    },
  });
});

beforeEach(() => {
  // 前のテストの上書きを残さず、既定の応答から始める
  server.resetHandlers(...apiHandlers());
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
  clearCookies();
});

afterAll(() => {
  server.close();
});
