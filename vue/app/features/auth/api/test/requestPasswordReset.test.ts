import { describe, expect, it } from 'vitest';

import { useApiClient } from '~/shared/api/apiClient';
import { accountApi } from '~/test/mocks/auth/accountApiHandlers';
import { overrideApi } from '~/test/mocks/overrideApi';

import { requestPasswordReset } from '../requestPasswordReset';

describe('パスワード再設定メール API', () => {
  it('前後の空白を除いたメールアドレスを送り、サーバーのメッセージを返すこと', async () => {
    const received: { body?: unknown } = {};
    overrideApi(accountApi.records('/api/auth/forgot-password', received));

    const response =
      await requestPasswordReset(useApiClient(), ' user@example.com ');

    expect(received.body).toEqual({ email: 'user@example.com' });
    expect(response).toEqual({ message: '送信しました。' });
  });

  it('試行回数の上限（429）では送信回数が多いことを伝えること', async () => {
    overrideApi(accountApi.fails('/api/auth/forgot-password', 429));

    await expect(
      requestPasswordReset(useApiClient(), 'user@example.com'),
    ).rejects.toThrow(
      'パスワード再設定メールの送信回数が多すぎます。しばらくしてから再度お試しください。',
    );
  });
});
