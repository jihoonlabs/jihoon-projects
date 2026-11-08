import { http, HttpResponse, type RequestHandler } from 'msw';

import { apiUrl } from './apiUrl';

/**
 * すべてのテストで最初から有効な API 応答。
 * 画面固有の応答は各テストで overrideApi を使って追加・上書きする。
 */
export function apiHandlers(): RequestHandler[] {
  return [
    // 新しいブラウザと同じく、既定では未ログイン（セッション復元は 401）
    http.get(apiUrl('/api/auth/me'), () =>
      HttpResponse.json({ message: 'Unauthenticated.' }, { status: 401 }),
    ),

    // Sanctum の CSRF Cookie 発行（Next.js 版の既定ハンドラーと同じ振る舞い）
    http.get(apiUrl('/sanctum/csrf-cookie'), () => {
      document.cookie = 'XSRF-TOKEN=test-csrf-token; path=/';

      return new HttpResponse(null, { status: 204 });
    }),
  ];
}
