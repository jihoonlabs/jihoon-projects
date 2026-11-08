import { screen } from '@testing-library/vue';
import { describe, expect, it } from 'vitest';

import { accountApi } from '~/test/auth/accountApiHandlers';
import { signInAs, signedOut } from '~/test/auth/signInAs';
import { overrideApi } from '~/test/msw/overrideApi';
import { expectPath, renderRoute } from '~/test/renderRoute';

const VALID_LINK = '/reset-password?email=user%40example.com&token=reset-token';

const passwordInput = () => screen.getByLabelText('新しいパスワード');
const confirmationInput = () =>
  screen.getByLabelText('新しいパスワード（確認）');
const submitButton = () =>
  screen.getByRole('button', { name: 'パスワードを再設定' });

describe('パスワード再設定画面', () => {
  describe('再設定リンクの確認', () => {
    it('トークンがないリンクでは誤りを伝え、入力欄を出さずに再送信へ案内すること', async () => {
      signedOut();
      await renderRoute('/reset-password?email=user%40example.com');

      expect(screen.getByRole('alert')).toHaveTextContent(
        '再設定リンクが正しくありません。もう一度メールを送信してください。',
      );
      expect(screen.queryByLabelText('新しいパスワード')).not.toBeInTheDocument();
      expect(
        screen.getByRole('link', { name: '再設定メールをもう一度送信する' }),
      ).toHaveAttribute('href', '/forgot-password');
    });

    it('メールアドレスが重複したリンクは正しくないリンクとして扱うこと', async () => {
      signedOut();
      await renderRoute(
        '/reset-password?email=a%40example.com&email=b%40example.com&token=t',
      );

      expect(screen.getByRole('alert')).toHaveTextContent(
        '再設定リンクが正しくありません。',
      );
    });

    it('ログイン中でも再設定リンクを開けること', async () => {
      signInAs();

      await renderRoute(VALID_LINK);

      await expectPath(VALID_LINK);
      expect(passwordInput()).toBeInTheDocument();
    });
  });

  describe('入力の検証', () => {
    it('英字を含まないパスワードと不一致の確認用をそれぞれ指摘すること', async () => {
      signedOut();
      const { user } = await renderRoute(VALID_LINK);

      await user.type(passwordInput(), '12345678');
      await user.type(confirmationInput(), '87654321');
      await user.click(submitButton());

      expect(passwordInput()).toHaveAccessibleDescription(
        'パスワードには英字を含めてください。',
      );
      expect(confirmationInput()).toHaveAccessibleDescription(
        'パスワードが一致しません。',
      );
    });

    it('パスワードを確認用と一致するよう直すと、不一致のエラーも消すこと', async () => {
      signedOut();
      const { user } = await renderRoute(VALID_LINK);
      await user.type(passwordInput(), 'abc');
      await user.type(confirmationInput(), 'abc1');
      await user.click(submitButton());

      await user.type(passwordInput(), '1');

      expect(confirmationInput()).toHaveAttribute('aria-invalid', 'false');
    });
  });

  describe('再設定成功', () => {
    it('リンクの情報と新しいパスワードを送り、完了を表示して入力欄を閉じること', async () => {
      signedOut();
      const received: { body?: unknown } = {};
      overrideApi(accountApi.records('/api/auth/reset-password', received));
      const { user } = await renderRoute(VALID_LINK);

      await user.type(passwordInput(), 'newpass123');
      await user.type(confirmationInput(), 'newpass123');
      await user.click(submitButton());

      expect(await screen.findByRole('status')).toHaveTextContent(
        '送信しました。',
      );
      expect(received.body).toEqual({
        email: 'user@example.com',
        token: 'reset-token',
        password: 'newpass123',
        password_confirmation: 'newpass123',
      });
      expect(screen.queryByLabelText('新しいパスワード')).not.toBeInTheDocument();
      expect(
        screen.getByRole('link', { name: 'ログイン画面に戻る' }),
      ).toBeInTheDocument();
    });
  });

  describe('再設定失敗', () => {
    it('期限切れのトークン（422）ではサーバーのメッセージを表示し、入力欄を残すこと', async () => {
      signedOut();
      overrideApi(
        accountApi.fails('/api/auth/reset-password', 422, {
          message: 'このパスワード再設定トークンは無効です。',
        }),
      );
      const { user } = await renderRoute(VALID_LINK);

      await user.type(passwordInput(), 'newpass123');
      await user.type(confirmationInput(), 'newpass123');
      await user.click(submitButton());

      expect(await screen.findByRole('alert')).toHaveTextContent(
        'このパスワード再設定トークンは無効です。',
      );
      expect(passwordInput()).toBeInTheDocument();
    });
  });

  describe('パスワードの表示切り替え', () => {
    it('両方の入力欄の表示・非表示を切り替えること', async () => {
      signedOut();
      const { user } = await renderRoute(VALID_LINK);

      await user.click(screen.getByRole('button', { name: 'パスワードを表示' }));

      expect(passwordInput()).toHaveAttribute('type', 'text');
      expect(confirmationInput()).toHaveAttribute('type', 'text');
      expect(
        screen.getByRole('button', { name: 'パスワードを隠す' }),
      ).toHaveAttribute('aria-pressed', 'true');
    });
  });
});
