import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { authApi } from '~/test/auth/authApiHandlers';
import { apiUrl } from '~/test/msw/apiUrl';
import { overrideApi } from '~/test/msw/overrideApi';

import { userFixture } from '../../test/userFixture';
import { LoginError, useAuthApi } from '../authApi';

describe('認証 API', () => {
  describe('ログイン', () => {
    it('入力したメールアドレスとパスワードを送り、ログインした利用者を返すこと', async () => {
      const user = userFixture({ id: 7, name: '山田 花子' });
      let payload: unknown;
      overrideApi(
        http.post(apiUrl('/api/auth/login'), async ({ request }) => {
          payload = await request.json();
          return HttpResponse.json({ message: 'ログイン成功', user });
        }),
      );

      const result = await useAuthApi().login({
        email: 'hanako@example.com',
        password: 'password123',
      });

      expect(payload).toEqual({
        email: 'hanako@example.com',
        password: 'password123',
      });
      expect(result).toEqual(user);
    });

    it('入力エラー（422）ではメールアドレス欄のメッセージを返すこと', async () => {
      overrideApi(
        authApi.loginFails(422, {
          errors: { email: ['メールアドレス及びパスワードが違います。'] },
        }),
      );

      const request = useAuthApi().login({
        email: 'user@example.com',
        password: 'wrong-password',
      });

      await expect(request).rejects.toBeInstanceOf(LoginError);
      await expect(request).rejects.toMatchObject({
        message: 'メールアドレス及びパスワードが違います。',
        reason: undefined,
      });
    });

    it('入力エラー（422）に項目別メッセージがなければ既定の文言を返すこと', async () => {
      overrideApi(authApi.loginFails(422, { message: 'invalid' }));

      await expect(
        useAuthApi().login({ email: 'user@example.com', password: 'x' }),
      ).rejects.toMatchObject({ message: 'ログイン情報が正しくありません。' });
    });

    it('メール未認証（403）ではサーバーの文言と未認証の理由を返すこと', async () => {
      overrideApi(
        authApi.loginFails(403, {
          message: 'メール認証が完了していません。',
          code: 'email_not_verified',
        }),
      );

      await expect(
        useAuthApi().login({
          email: 'user@example.com',
          password: 'password123',
        }),
      ).rejects.toMatchObject({
        message: 'メール認証が完了していません。',
        reason: 'email_not_verified',
      });
    });

    it('未認証コードのない 403 は一般的な失敗として扱うこと', async () => {
      overrideApi(authApi.loginFails(403, { message: 'Forbidden' }));

      await expect(
        useAuthApi().login({
          email: 'user@example.com',
          password: 'password123',
        }),
      ).rejects.toMatchObject({
        message: 'ログイン処理に失敗しました。',
        reason: undefined,
      });
    });

    it('試行回数の上限（429）では時間をおくよう案内すること', async () => {
      overrideApi(authApi.loginFails(429, { message: 'Too Many Attempts.' }));

      await expect(
        useAuthApi().login({
          email: 'user@example.com',
          password: 'password123',
        }),
      ).rejects.toMatchObject({
        message:
          'ログイン試行回数が多すぎます。しばらくしてから再度お試しください。',
      });
    });

    it('サーバーエラー（500）では一般的な失敗の文言を返すこと', async () => {
      overrideApi(authApi.loginFails(500, { message: 'Server Error' }));

      await expect(
        useAuthApi().login({
          email: 'user@example.com',
          password: 'password123',
        }),
      ).rejects.toMatchObject({ message: 'ログイン処理に失敗しました。' });
    });

    it('通信できないときも一般的な失敗の文言を返すこと', async () => {
      overrideApi(
        http.post(apiUrl('/api/auth/login'), () => HttpResponse.error()),
      );

      await expect(
        useAuthApi().login({
          email: 'user@example.com',
          password: 'password123',
        }),
      ).rejects.toMatchObject({ message: 'ログイン処理に失敗しました。' });
    });
  });

  describe('ログアウト', () => {
    it('ログアウト要求を送ること', async () => {
      let requested = false;
      overrideApi(
        http.post(apiUrl('/api/auth/logout'), () => {
          requested = true;
          return HttpResponse.json({ message: 'ログアウトしました。' });
        }),
      );

      await useAuthApi().logout();

      expect(requested).toBe(true);
    });

    it('失敗したら利用者向けの文言で失敗すること', async () => {
      overrideApi(authApi.logoutFails());

      await expect(useAuthApi().logout()).rejects.toThrow(
        'ログアウトに失敗しました。',
      );
    });
  });

  describe('現在の利用者', () => {
    it('セッションの利用者を返すこと', async () => {
      const user = userFixture({ id: 3, role: 'admin' });
      overrideApi(authApi.currentUser(user));

      await expect(useAuthApi().fetchCurrentUser()).resolves.toEqual(user);
    });

    it('未ログイン（401）ではステータス付きで失敗すること', async () => {
      overrideApi(authApi.unauthenticated());

      await expect(useAuthApi().fetchCurrentUser()).rejects.toMatchObject({
        status: 401,
      });
    });
  });
});
