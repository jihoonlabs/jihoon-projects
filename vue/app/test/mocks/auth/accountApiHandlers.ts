import { http, HttpResponse } from 'msw';

import { apiUrl } from '../apiUrl';

type AccountEndpoint =
  | '/api/auth/register'
  | '/api/auth/forgot-password'
  | '/api/auth/reset-password'
  | '/api/auth/email/verification-notification';

/**
 * 会員登録・パスワード再設定・認証メール再送の応答。各テストで overrideApi に渡して使う。
 */
export const accountApi = {
  succeeds(endpoint: AccountEndpoint, message: string) {
    return http.post(apiUrl(endpoint), () =>
      HttpResponse.json({ message }, { status: 200 }),
    );
  },

  fails(
    endpoint: AccountEndpoint,
    status: number,
    body: Record<string, unknown> = {},
  ) {
    return http.post(apiUrl(endpoint), () =>
      HttpResponse.json(body, { status }),
    );
  },

  /**
   * 送られた本文を記録し、成功を返す
   */
  records(endpoint: AccountEndpoint, received: { body?: unknown }) {
    return http.post(apiUrl(endpoint), async ({ request }) => {
      received.body = await request.json();
      return HttpResponse.json({ message: '送信しました。' });
    });
  },
};
