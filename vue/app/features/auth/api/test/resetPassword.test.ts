import { describe, expect, it } from 'vitest';

import { useApiClient } from '~/shared/api/apiClient';
import { accountApi } from '~/test/mocks/auth/accountApiHandlers';
import { overrideApi } from '~/test/mocks/overrideApi';

import { resetPassword } from '../resetPassword';

describe('パスワード再設定 API', () => {
  it('メールアドレス・トークン・新しいパスワードを Laravel の項目名で送ること', async () => {
    const received: { body?: unknown } = {};
    overrideApi(accountApi.records('/api/auth/reset-password', received));

    await resetPassword(useApiClient(), {
      email: ' user@example.com ',
      token: 'reset-token',
      password: 'newpass123',
      passwordConfirmation: 'newpass123',
    });

    expect(received.body).toEqual({
      email: 'user@example.com',
      token: 'reset-token',
      password: 'newpass123',
      password_confirmation: 'newpass123',
    });
  });

  it('入力エラー（422）に項目別メッセージがなければサーバーのメッセージを返すこと', async () => {
    overrideApi(
      accountApi.fails('/api/auth/reset-password', 422, {
        message: 'このパスワード再設定トークンは無効です。',
      }),
    );

    await expect(
      resetPassword(useApiClient(), {
        email: 'user@example.com',
        token: 'expired',
        password: 'newpass123',
        passwordConfirmation: 'newpass123',
      }),
    ).rejects.toThrow('このパスワード再設定トークンは無効です。');
  });

  it('入力エラー（422）でトークンの項目別メッセージがあればそれを返すこと', async () => {
    overrideApi(
      accountApi.fails('/api/auth/reset-password', 422, {
        message: '入力内容を確認してください。',
        errors: { token: ['トークンの有効期限が切れています。'] },
      }),
    );

    await expect(
      resetPassword(useApiClient(), {
        email: 'user@example.com',
        token: 'expired',
        password: 'newpass123',
        passwordConfirmation: 'newpass123',
      }),
    ).rejects.toThrow('トークンの有効期限が切れています。');
  });

  it('サーバーエラー（500）では再設定に失敗したことを伝えること', async () => {
    overrideApi(accountApi.fails('/api/auth/reset-password', 500));

    await expect(
      resetPassword(useApiClient(), {
        email: 'user@example.com',
        token: 'token',
        password: 'newpass123',
        passwordConfirmation: 'newpass123',
      }),
    ).rejects.toThrow('パスワードの再設定に失敗しました。');
  });
});
