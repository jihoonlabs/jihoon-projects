import { describe, expect, it } from 'vitest';

import { accountApi } from '~/test/mocks/auth/accountApiHandlers';
import { overrideApi } from '~/test/mocks/overrideApi';

import { usePasswordResetRequest } from '../usePasswordResetRequest';

const ENDPOINT = '/api/auth/forgot-password';

describe('パスワード再設定メールの送信フォーム（composable）', () => {
  describe('送信', () => {
    it('前後の空白を除いたメールアドレスを送り、応答のメッセージを結果にすること', async () => {
      const received: { body?: unknown } = {};
      overrideApi(accountApi.records(ENDPOINT, received));
      const form = usePasswordResetRequest();

      form.email.value = ' user@example.com ';
      await form.submit();

      expect(received.body).toEqual({ email: 'user@example.com' });
      expect(form.successMessage.value).toBe('送信しました。');
      expect(form.serverError.value).toBe('');
      expect(form.loading.value).toBe(false);
    });

    it('メールアドレスが空なら送信せず、入力エラーにすること', async () => {
      const received: { body?: unknown } = {};
      overrideApi(accountApi.records(ENDPOINT, received));
      const form = usePasswordResetRequest();

      await form.submit();

      expect(received.body).toBeUndefined();
      expect(form.errors.value).toEqual({
        email: 'メールアドレスを入力してください。',
      });
    });

    it('送信回数の上限に達したら、その旨をサーバーエラーとして示すこと', async () => {
      overrideApi(accountApi.fails(ENDPOINT, 429));
      const form = usePasswordResetRequest();

      form.email.value = 'user@example.com';
      await form.submit();

      expect(form.serverError.value).toBe(
        'パスワード再設定メールの送信回数が多すぎます。しばらくしてから再度お試しください。',
      );
      expect(form.successMessage.value).toBe('');
      expect(form.loading.value).toBe(false);
    });
  });

  describe('入力の変更', () => {
    it('前回の送信結果と入力エラーを消すこと', async () => {
      overrideApi(accountApi.succeeds(ENDPOINT, '送信しました。'));
      const form = usePasswordResetRequest();
      form.email.value = 'user@example.com';
      await form.submit();
      form.errors.value = { email: 'メールアドレスを入力してください。' };

      form.onEmailChange();

      expect(form.successMessage.value).toBe('');
      expect(form.serverError.value).toBe('');
      expect(form.errors.value).toEqual({});
    });
  });
});
