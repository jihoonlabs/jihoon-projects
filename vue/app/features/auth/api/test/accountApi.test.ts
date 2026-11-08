import { describe, expect, it } from 'vitest';

import { accountApi } from '~/test/auth/accountApiHandlers';
import { overrideApi } from '~/test/msw/overrideApi';

import { AccountError, useAccountApi } from '../accountApi';

describe('アカウント API', () => {
  describe('会員登録', () => {
    it('名前とメールアドレスの前後の空白を除き、確認用パスワードを Laravel の項目名で送ること', async () => {
      const received: { body?: unknown } = {};
      overrideApi(accountApi.records('/api/auth/register', received));

      await useAccountApi().register({
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

      const request = useAccountApi().register({
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
        useAccountApi().register({
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
        useAccountApi().register({
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
        useAccountApi().register({
          name: 'a',
          email: 'a@example.com',
          password: 'password1',
          passwordConfirmation: 'password1',
        }),
      ).rejects.toThrow('会員登録処理に失敗しました。');
    });
  });

  describe('パスワード再設定メール', () => {
    it('前後の空白を除いたメールアドレスを送り、サーバーのメッセージを返すこと', async () => {
      const received: { body?: unknown } = {};
      overrideApi(accountApi.records('/api/auth/forgot-password', received));

      const response =
        await useAccountApi().requestPasswordReset(' user@example.com ');

      expect(received.body).toEqual({ email: 'user@example.com' });
      expect(response).toEqual({ message: '送信しました。' });
    });

    it('試行回数の上限（429）では送信回数が多いことを伝えること', async () => {
      overrideApi(accountApi.fails('/api/auth/forgot-password', 429));

      await expect(
        useAccountApi().requestPasswordReset('user@example.com'),
      ).rejects.toThrow(
        'パスワード再設定メールの送信回数が多すぎます。しばらくしてから再度お試しください。',
      );
    });
  });

  describe('パスワード再設定', () => {
    it('メールアドレス・トークン・新しいパスワードを Laravel の項目名で送ること', async () => {
      const received: { body?: unknown } = {};
      overrideApi(accountApi.records('/api/auth/reset-password', received));

      await useAccountApi().resetPassword({
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
        useAccountApi().resetPassword({
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
        useAccountApi().resetPassword({
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
        useAccountApi().resetPassword({
          email: 'user@example.com',
          token: 'token',
          password: 'newpass123',
          passwordConfirmation: 'newpass123',
        }),
      ).rejects.toThrow('パスワードの再設定に失敗しました。');
    });
  });

  describe('認証メールの再送', () => {
    it('前後の空白を除いたメールアドレスを送ること', async () => {
      const received: { body?: unknown } = {};
      overrideApi(
        accountApi.records(
          '/api/auth/email/verification-notification',
          received,
        ),
      );

      await useAccountApi().resendVerificationEmail(' user@example.com ');

      expect(received.body).toEqual({ email: 'user@example.com' });
    });

    it('中断したときは利用者向けの文言に変えず、中断として伝えること', async () => {
      overrideApi(
        accountApi.succeeds(
          '/api/auth/email/verification-notification',
          '送信しました。',
        ),
      );
      const controller = new AbortController();
      controller.abort();

      await expect(
        useAccountApi().resendVerificationEmail(
          'user@example.com',
          controller.signal,
        ),
      ).rejects.toMatchObject({ name: 'AbortError' });
    });

    it('試行回数の上限（429）では再送回数が多いことを伝えること', async () => {
      overrideApi(
        accountApi.fails('/api/auth/email/verification-notification', 429),
      );

      await expect(
        useAccountApi().resendVerificationEmail('user@example.com'),
      ).rejects.toThrow(
        '認証メールの再送回数が多すぎます。しばらくしてから再度お試しください。',
      );
    });
  });
});
