import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { userFixture } from '~/features/users/test/userFixture';
import { useApiClient } from '~/shared/api/apiClient';
import { apiUrl } from '~/test/mocks/apiUrl';
import { authApi } from '~/test/mocks/auth/authApiHandlers';
import { overrideApi } from '~/test/mocks/overrideApi';

import { login, LoginError } from '../login';

describe('ログイン API', () => {
  it('入力したメールアドレスとパスワードを送り、ログインした利用者を返すこと', async () => {
    const user = userFixture({ id: 7, name: '山田 花子' });
    let payload: unknown;
    overrideApi(
      http.post(apiUrl('/api/auth/login'), async ({ request }) => {
        payload = await request.json();
        return HttpResponse.json({ message: 'ログイン成功', user });
      }),
    );

    const result = await login(useApiClient(), {
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

    const request = login(useApiClient(), {
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
      login(useApiClient(), { email: 'user@example.com', password: 'x' }),
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
      login(useApiClient(), {
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
      login(useApiClient(), {
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
      login(useApiClient(), {
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
      login(useApiClient(), {
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
      login(useApiClient(), {
        email: 'user@example.com',
        password: 'password123',
      }),
    ).rejects.toMatchObject({ message: 'ログイン処理に失敗しました。' });
  });
});
