import { screen } from '@testing-library/vue';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { attendanceApi } from '~/test/attendance/attendanceApiHandlers';
import { accountApi } from '~/test/auth/accountApiHandlers';
import { signInAs, signedOut } from '~/test/auth/signInAs';
import { apiUrl } from '~/test/msw/apiUrl';
import { overrideApi } from '~/test/msw/overrideApi';
import { expectPath, renderRoute } from '~/test/renderRoute';

const field = (label: string) => screen.getByLabelText(label);
const submitButton = () =>
  screen.getByRole('button', { name: 'メールアドレスで登録' });

describe('会員登録画面', () => {
  describe('入力の検証', () => {
    it('未入力で送信すると全項目にエラーを表示し、登録要求を送らないこと', async () => {
      signedOut();
      let requested = false;
      overrideApi(
        http.post(apiUrl('/api/auth/register'), () => {
          requested = true;
          return HttpResponse.json({});
        }),
      );
      const { user } = await renderRoute('/register');

      await user.click(submitButton());

      expect(field('名前')).toHaveAccessibleDescription(
        '名前を入力してください。',
      );
      expect(field('メールアドレス')).toHaveAccessibleDescription(
        'メールアドレスを入力してください。',
      );
      expect(field('パスワード')).toHaveAccessibleDescription(
        'パスワードを入力してください。',
      );
      expect(field('パスワード確認')).toHaveAccessibleDescription(
        '確認用のパスワードを入力してください。',
      );
      expect(requested).toBe(false);
    });

    it('入力し直した項目のエラーだけを消すこと', async () => {
      signedOut();
      const { user } = await renderRoute('/register');
      await user.click(submitButton());

      await user.type(field('名前'), '山田');

      expect(field('名前')).toHaveAttribute('aria-invalid', 'false');
      expect(field('メールアドレス')).toHaveAttribute('aria-invalid', 'true');
    });
  });

  describe('登録成功', () => {
    it('入力内容を送り、認証メール送信の案内付きでログイン画面へ移ること', async () => {
      signedOut();
      const received: { body?: unknown } = {};
      overrideApi(accountApi.records('/api/auth/register', received));
      const { user } = await renderRoute('/register');

      await user.type(field('名前'), '山田 花子');
      await user.type(field('メールアドレス'), 'hanako@example.com');
      await user.type(field('パスワード'), 'password123');
      await user.type(field('パスワード確認'), 'password123');
      await user.click(submitButton());

      expect(
        await screen.findByText(
          '認証メールを送信しました。メールをご確認ください。',
        ),
      ).toBeInTheDocument();
      await expectPath('/login');
      expect(received.body).toEqual({
        name: '山田 花子',
        email: 'hanako@example.com',
        password: 'password123',
        password_confirmation: 'password123',
      });
    });
  });

  describe('登録失敗', () => {
    it('登録済みのメールアドレス（422）ではサーバーのメッセージを表示し、画面に残ること', async () => {
      signedOut();
      overrideApi(
        accountApi.fails('/api/auth/register', 422, {
          errors: { email: ['このメールアドレスは既に使用されています。'] },
        }),
      );
      const { user } = await renderRoute('/register');

      await user.type(field('名前'), '山田 花子');
      await user.type(field('メールアドレス'), 'used@example.com');
      await user.type(field('パスワード'), 'password123');
      await user.type(field('パスワード確認'), 'password123');
      await user.click(submitButton());

      expect(await screen.findByRole('alert')).toHaveTextContent(
        'このメールアドレスは既に使用されています。',
      );
      await expectPath('/register');
      expect(submitButton()).toBeEnabled();
    });
  });

  describe('ソーシャルログイン', () => {
    it('Google と LINE のリンクが Vue 版へ戻る指定付きで Laravel の開始 URL を指すこと', async () => {
      signedOut();
      await renderRoute('/register');

      expect(
        screen.getByRole('link', { name: 'Googleで続ける' }),
      ).toHaveAttribute(
        'href',
        'http://localhost:8000/api/auth/google/redirect?client=vue',
      );
      expect(
        screen.getByRole('link', { name: 'LINEで続ける' }),
      ).toHaveAttribute(
        'href',
        'http://localhost:8000/api/auth/line/redirect?client=vue',
      );
    });
  });

  describe('画面移動', () => {
    it('ログイン画面へのリンクを表示すること', async () => {
      signedOut();
      await renderRoute('/register');

      expect(screen.getByRole('link', { name: 'ログインへ' })).toHaveAttribute(
        'href',
        '/login',
      );
    });

    it('ログイン済みなら勤怠画面へ移すこと', async () => {
      signInAs();
      overrideApi(...attendanceApi.emptyHome());

      await renderRoute('/register');

      await expectPath('/attendance');
    });
  });
});
