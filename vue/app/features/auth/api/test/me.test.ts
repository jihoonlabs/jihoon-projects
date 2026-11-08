import { describe, expect, it } from 'vitest';

import { userFixture } from '~/features/users/test/userFixture';
import { useApiClient } from '~/shared/api/apiClient';
import { authApi } from '~/test/mocks/auth/authApiHandlers';
import { overrideApi } from '~/test/mocks/overrideApi';

import { fetchCurrentUser } from '../me';

describe('現在の利用者 API', () => {
  it('セッションの利用者を返すこと', async () => {
    const user = userFixture({ id: 3, role: 'admin' });
    overrideApi(authApi.currentUser(user));

    await expect(fetchCurrentUser(useApiClient())).resolves.toEqual(user);
  });

  it('未ログイン（401）ではステータス付きで失敗すること', async () => {
    overrideApi(authApi.unauthenticated());

    await expect(fetchCurrentUser(useApiClient())).rejects.toMatchObject({
      status: 401,
    });
  });
});
