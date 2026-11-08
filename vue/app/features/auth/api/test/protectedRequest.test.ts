import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { signInAs, signedOut } from '~/test/auth/signInAs';
import { apiUrl } from '~/test/mocks/apiUrl';
import { overrideApi } from '~/test/mocks/overrideApi';
import { ApiError } from '~/shared/api/apiClient';

import { useAuthStore } from '../../store/useAuthStore';
import { userFixture } from '../../../users/test/userFixture';
import { protectedRequest, useProtectedApi } from '../protectedRequest';

describe('ログインが必要な API 要求', () => {
  describe('成功', () => {
    it('ログイン中は応答をそのまま返すこと', async () => {
      signInAs();
      overrideApi(
        http.get(apiUrl('/api/tickets'), () =>
          HttpResponse.json({ data: [{ id: 1 }] }),
        ),
      );

      await expect(useProtectedApi().getJson('/api/tickets')).resolves.toEqual({
        data: [{ id: 1 }],
      });
    });
  });

  describe('セッション期限切れ', () => {
    it('ログイン中に 401 が返ったらセッション期限切れにすること', async () => {
      signInAs();
      overrideApi(
        http.get(apiUrl('/api/tickets'), () =>
          HttpResponse.json({ message: 'Unauthenticated.' }, { status: 401 }),
        ),
      );

      await expect(
        useProtectedApi().getJson('/api/tickets'),
      ).rejects.toMatchObject({ status: 401 });
      expect(useAuthStore().sessionExpired).toBe(true);
    });

    it('未ログインのときの 401 では期限切れにしないこと', async () => {
      signedOut();
      overrideApi(
        http.get(apiUrl('/api/tickets'), () =>
          HttpResponse.json({ message: 'Unauthenticated.' }, { status: 401 }),
        ),
      );

      await expect(
        useProtectedApi().getJson('/api/tickets'),
      ).rejects.toMatchObject({ status: 401 });
      expect(useAuthStore().sessionExpired).toBe(false);
    });

    it('401 以外のエラーでは期限切れにしないこと', async () => {
      signInAs();
      overrideApi(
        http.get(apiUrl('/api/tickets'), () =>
          HttpResponse.json({ message: 'Forbidden' }, { status: 403 }),
        ),
      );

      await expect(
        useProtectedApi().getJson('/api/tickets'),
      ).rejects.toBeInstanceOf(ApiError);
      expect(useAuthStore().sessionExpired).toBe(false);
    });

    it('期限切れの間は要求を送らずに中断すること', async () => {
      signInAs();
      useAuthStore().expireSession();
      let requested = false;
      overrideApi(
        http.get(apiUrl('/api/tickets'), () => {
          requested = true;
          return HttpResponse.json({});
        }),
      );

      await expect(
        useProtectedApi().getJson('/api/tickets'),
      ).rejects.toMatchObject({ name: 'AbortError' });
      expect(requested).toBe(false);
    });
  });

  describe('認証状態の変化', () => {
    it('要求中にログアウトしたら要求を中断し、応答を使わないこと', async () => {
      signInAs();
      const auth = useAuthStore();
      let receivedSignal: AbortSignal | undefined;

      const request = protectedRequest(auth, async (signal) => {
        receivedSignal = signal;
        auth.signOut();
        return { data: '古いセッションの応答' };
      });

      await expect(request).rejects.toMatchObject({ name: 'AbortError' });
      expect(receivedSignal?.aborted).toBe(true);
    });

    it('要求中に別のアカウントでログインしたら、古い 401 で新しいログインを期限切れにしないこと', async () => {
      signInAs(userFixture({ id: 1 }));
      const auth = useAuthStore();

      const request = protectedRequest(auth, async () => {
        auth.signIn(userFixture({ id: 2 }));
        throw new ApiError('API 要求に失敗しました (401)', 401);
      });

      await expect(request).rejects.toMatchObject({ name: 'AbortError' });
      expect(auth.sessionExpired).toBe(false);
      expect(auth.user?.id).toBe(2);
    });

    it('呼び出し元が中断したら要求も中断すること', async () => {
      signInAs();
      const controller = new AbortController();
      let receivedSignal: AbortSignal | undefined;

      const request = protectedRequest(
        useAuthStore(),
        async (signal) => {
          receivedSignal = signal;
          controller.abort();
          return { data: [] };
        },
        controller.signal,
      );

      await expect(request).rejects.toMatchObject({ name: 'AbortError' });
      expect(receivedSignal?.aborted).toBe(true);
    });
  });
});
