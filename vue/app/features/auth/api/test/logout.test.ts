import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { useApiClient } from '~/shared/api/apiClient';
import { apiUrl } from '~/test/mocks/apiUrl';
import { authApi } from '~/test/mocks/auth/authApiHandlers';
import { overrideApi } from '~/test/mocks/overrideApi';

import { logout } from '../logout';

describe('ログアウト API', () => {
  it('ログアウト要求を送ること', async () => {
    let requested = false;
    overrideApi(
      http.post(apiUrl('/api/auth/logout'), () => {
        requested = true;
        return HttpResponse.json({ message: 'ログアウトしました。' });
      }),
    );

    await logout(useApiClient());

    expect(requested).toBe(true);
  });

  it('失敗したら利用者向けの文言で失敗すること', async () => {
    overrideApi(authApi.logoutFails());

    await expect(logout(useApiClient())).rejects.toThrow(
      'ログアウトに失敗しました。',
    );
  });
});
