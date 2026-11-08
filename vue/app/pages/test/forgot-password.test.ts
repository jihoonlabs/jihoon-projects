import { screen } from '@testing-library/vue';
import { describe, expect, it } from 'vitest';

import { attendanceApi } from '~/test/attendance/attendanceApiHandlers';
import { accountApi } from '~/test/auth/accountApiHandlers';
import { signInAs, signedOut } from '~/test/auth/signInAs';
import { overrideApi } from '~/test/msw/overrideApi';
import { expectPath, renderRoute } from '~/test/renderRoute';

const emailInput = () => screen.getByLabelText('メールアドレス');
const submitButton = () =>
  screen.getByRole('button', { name: '再設定メールを送信' });

describe('パスワード再設定メールの送信画面', () => {
  describe('入力の検証', () => {
    it('未入力で送信するとメールアドレスの入力を求めること', async () => {
      signedOut();
      const { user } = await renderRoute('/forgot-password');

      await user.click(submitButton());

      expect(emailInput()).toHaveAccessibleDescription(
        'メールアドレスを入力してください。',
      );
    });
  });

  describe('送信成功', () => {
    it('入力したメールアドレスを送り、サーバーのメッセージを表示すること', async () => {
      signedOut();
      const received: { body?: unknown } = {};
      overrideApi(accountApi.records('/api/auth/forgot-password', received));
      const { user } = await renderRoute('/forgot-password');

      await user.type(emailInput(), 'user@example.com');
      await user.click(submitButton());

      expect(await screen.findByRole('status')).toHaveTextContent(
        '送信しました。',
      );
      expect(received.body).toEqual({ email: 'user@example.com' });
    });

    it('送信後にメールアドレスを変えると、前回の結果表示を消すこと', async () => {
      signedOut();
      overrideApi(
        accountApi.succeeds(
          '/api/auth/forgot-password',
          'パスワード再設定用のリンクを送信しました。',
        ),
      );
      const { user } = await renderRoute('/forgot-password');
      await user.type(emailInput(), 'user@example.com');
      await user.click(submitButton());
      await screen.findByRole('status');

      await user.type(emailInput(), 'x');

      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });
  });

  describe('送信失敗', () => {
    it('試行回数の上限（429）では送信回数が多いことを表示すること', async () => {
      signedOut();
      overrideApi(accountApi.fails('/api/auth/forgot-password', 429));
      const { user } = await renderRoute('/forgot-password');

      await user.type(emailInput(), 'user@example.com');
      await user.click(submitButton());

      expect(await screen.findByRole('alert')).toHaveTextContent(
        'パスワード再設定メールの送信回数が多すぎます。しばらくしてから再度お試しください。',
      );
    });
  });

  describe('画面移動', () => {
    it('ログイン画面に戻るリンクを表示すること', async () => {
      signedOut();
      await renderRoute('/forgot-password');

      expect(
        screen.getByRole('link', { name: 'ログイン画面に戻る' }),
      ).toHaveAttribute('href', '/login');
    });

    it('ログイン済みなら勤怠画面へ移すこと', async () => {
      signInAs();
      overrideApi(...attendanceApi.emptyHome());

      await renderRoute('/forgot-password');

      await expectPath('/attendance');
    });
  });
});
