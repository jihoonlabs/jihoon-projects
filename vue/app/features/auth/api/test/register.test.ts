import { describe, expect, it } from 'vitest';

import { useApiClient } from '~/shared/api/apiClient';
import { accountApi } from '~/test/mocks/auth/accountApiHandlers';
import { overrideApi } from '~/test/mocks/overrideApi';

import { AccountError } from '../accountRequest';
import { register } from '../register';

describe('会員登録 API', () => {
  it('名前とメールアドレスの前後の空白を除き、確認用パスワードを Laravel の項目名で送ること', async () => {
    const received: { body?: unknown } = {};
    overrideApi(accountApi.records('/api/auth/register', received));

    await register(useApiClient(), {
      name: '  山田 花子 ',
      email: ' hanako@example.com ',
      password: 'password123',
      passwordConfirmation: 'password123',
    });

    expect(received.body).toEqual({
      name: '山田 花子',
      email: 'hanako@example.com',
      password: 'password123',
      password_confirmation: 'password123',
    });
  });

  it('入力エラー（422）ではメールアドレス・パスワード・名前の順で最初のメッセージを返すこと', async () => {
    overrideApi(
      accountApi.fails('/api/auth/register', 422, {
        errors: {
          name: ['名前は必須です。'],
          password: ['パスワードが短すぎます。'],
        },
      }),
    );

    const request = register(useApiClient(), {
      name: '',
      email: 'user@example.com',
      password: 'short',
      passwordConfirmation: 'short',
    });

    await expect(request).rejects.toBeInstanceOf(AccountError);
    await expect(request).rejects.toThrow('パスワードが短すぎます。');
  });

  it('入力エラー（422）に項目別メッセージがなければ入力の確認を求めること', async () => {
    overrideApi(accountApi.fails('/api/auth/register', 422));

    await expect(
      register(useApiClient(), {
        name: 'a',
        email: 'a@example.com',
        password: 'password1',
        passwordConfirmation: 'password1',
      }),
    ).rejects.toThrow('入力内容を確認してください。');
  });

  it('試行回数の上限（429）では時間をおくよう案内すること', async () => {
    overrideApi(accountApi.fails('/api/auth/register', 429));

    await expect(
      register(useApiClient(), {
        name: 'a',
        email: 'a@example.com',
        password: 'password1',
        passwordConfirmation: 'password1',
      }),
    ).rejects.toThrow(
      '登録試行回数が多すぎます。しばらくしてから再度お試しください。',
    );
  });

  it('公開デモでの拒否（403）など、その他の失敗では一般的な文言を返すこと', async () => {
    overrideApi(accountApi.fails('/api/auth/register', 403));

    await expect(
      register(useApiClient(), {
        name: 'a',
        email: 'a@example.com',
        password: 'password1',
        passwordConfirmation: 'password1',
      }),
    ).rejects.toThrow('会員登録処理に失敗しました。');
  });
});
