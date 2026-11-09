import { http, HttpResponse } from 'msw';

import type { User } from '~/features/users/types/user';

import { apiUrl } from '../apiUrl';

/**
 * 認証 API の応答。各テストで overrideApi に渡して使う。
 */
export const authApi = {
  currentUser(user: User) {
    return http.get(apiUrl('/api/auth/me'), () => HttpResponse.json(user));
  },

  unauthenticated() {
    return http.get(apiUrl('/api/auth/me'), () =>
      HttpResponse.json({ message: 'Unauthenticated.' }, { status: 401 }),
    );
  },

  loginSucceeds(user: User) {
    return http.post(apiUrl('/api/auth/login'), () =>
      HttpResponse.json({ message: 'ログイン成功', user }),
    );
  },

  loginFails(status: number, body: Record<string, unknown>) {
    return http.post(apiUrl('/api/auth/login'), () =>
      HttpResponse.json(body, { status }),
    );
  },

  logoutSucceeds() {
    return http.post(apiUrl('/api/auth/logout'), () =>
      HttpResponse.json({ message: 'ログアウトしました。' }),
    );
  },

  logoutFails() {
    return http.post(apiUrl('/api/auth/logout'), () =>
      HttpResponse.json({ message: 'Server Error' }, { status: 500 }),
    );
  },
};
