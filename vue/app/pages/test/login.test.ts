import { screen, waitFor } from '@testing-library/vue';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { userFixture } from '~/features/auth/test/userFixture';
import { authApi } from '~/test/auth/authApiHandlers';
import { signInAs, signedOut } from '~/test/auth/signInAs';
import { enableDemoMode } from '~/test/demoMode';
import { apiUrl } from '~/test/msw/apiUrl';
import { overrideApi } from '~/test/msw/overrideApi';
import { expectPath, renderRoute } from '~/test/renderRoute';

const emailInput = () => screen.getByLabelText('メールアドレス');
const passwordInput = () => screen.getByLabelText('パスワード');
const submitButton = () => screen.getByRole('button', { name: 'ログイン' });

describe('ログイン画面', () => {
  describe('入力の検証', () => {
    it('未入力で送信すると両方の項目にエラーを表示し、ログイン要求を送らないこと', async () => {
      signedOut();
      let requested = false;
      overrideApi(
        http.post(apiUrl('/api/auth/login'), () => {
          requested = true;
          return HttpResponse.json({});
        }),
      );
      const { user } = await renderRoute('/login');

      await user.click(submitButton());

      expect(
        screen.getByText('メールアドレスを入力してください。'),
      ).toBeInTheDocument();
      expect(
        screen.getByText('パスワードを入力してください。'),
      ).toBeInTheDocument();
      expect(emailInput()).toHaveAttribute('aria-invalid', 'true');
      expect(emailInput()).toHaveAccessibleDescription(
        'メールアドレスを入力してください。',
      );
      expect(requested).toBe(false);
    });

    it('エラーのある項目を入力し直すと、その項目のエラーだけを消すこと', async () => {
      signedOut();
      const { user } = await renderRoute('/login');
      await user.click(submitButton());

      await user.type(emailInput(), 'u');

      expect(
        screen.queryByText('メールアドレスを入力してください。'),
      ).not.toBeInTheDocument();
      expect(
        screen.getByText('パスワードを入力してください。'),
      ).toBeInTheDocument();
    });
  });

  describe('ログイン成功', () => {
    it('入力内容を送り、勤怠画面に移ってヘッダーに利用者名を表示すること', async () => {
      signedOut();
      let payload: unknown;
      overrideApi(
        http.post(apiUrl('/api/auth/login'), async ({ request }) => {
          payload = await request.json();
          return HttpResponse.json({
            message: 'ログイン成功',
            user: userFixture({ name: '山田 花子', role: 'admin' }),
          });
        }),
      );
      const { user } = await renderRoute('/login');

      await user.type(emailInput(), 'hanako@example.com');
      await user.type(passwordInput(), 'password123');
      await user.click(submitButton());

      await expectPath('/attendance');
      expect(payload).toEqual({
        email: 'hanako@example.com',
        password: 'password123',
      });
      expect(
        await screen.findByRole('heading', { name: '勤怠管理' }),
      ).toBeInTheDocument();
      expect(screen.getByRole('banner')).toHaveTextContent(
        'ようこそ、山田 花子 さん（管理者）',
      );
    });

    it('送信中はボタンを無効にし、送信中であることを表示すること', async () => {
      signedOut();
      let release!: () => void;
      overrideApi(
        http.post(apiUrl('/api/auth/login'), async () => {
          await new Promise<void>((resolve) => {
            release = resolve;
          });
          return HttpResponse.json({
            message: 'ログイン成功',
            user: userFixture(),
          });
        }),
      );
      const { user } = await renderRoute('/login');
      await user.type(emailInput(), 'user@example.com');
      await user.type(passwordInput(), 'password123');

      await user.click(submitButton());

      const pendingButton = await screen.findByRole('button', {
        name: 'ログイン中...',
      });
      expect(pendingButton).toBeDisabled();
      expect(emailInput()).toBeDisabled();
      release();
      await expectPath('/attendance');
    });
  });

  describe('ログイン失敗', () => {
    it('認証情報の誤り（422）ではサーバーのメッセージを表示し、画面に残ること', async () => {
      signedOut();
      overrideApi(
        authApi.loginFails(422, {
          errors: { email: ['メールアドレス及びパスワードが違います。'] },
        }),
      );
      const { user } = await renderRoute('/login');

      await user.type(emailInput(), 'user@example.com');
      await user.type(passwordInput(), 'wrong-password');
      await user.click(submitButton());

      expect(await screen.findByRole('alert')).toHaveTextContent(
        'メールアドレス及びパスワードが違います。',
      );
      await expectPath('/login');
      expect(submitButton()).toBeEnabled();
    });

    it('メール未認証（403）ではメール認証が必要なことを表示すること', async () => {
      signedOut();
      overrideApi(
        authApi.loginFails(403, {
          message: 'メール認証が完了していません。',
          code: 'email_not_verified',
        }),
      );
      const { user } = await renderRoute('/login');

      await user.type(emailInput(), 'user@example.com');
      await user.type(passwordInput(), 'password123');
      await user.click(submitButton());

      expect(await screen.findByRole('alert')).toHaveTextContent(
        'メール認証が完了していません。',
      );
    });

    it('再送信すると前回のエラー表示を消してから結果を表示すること', async () => {
      signedOut();
      overrideApi(authApi.loginFails(429, { message: 'Too Many Attempts.' }));
      const { user } = await renderRoute('/login');
      await user.type(emailInput(), 'user@example.com');
      await user.type(passwordInput(), 'password123');
      await user.click(submitButton());
      await screen.findByRole('alert');
      overrideApi(authApi.loginSucceeds(userFixture()));

      await user.click(submitButton());

      await expectPath('/attendance');
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  describe('遷移元からの通知', () => {
    it('メール認証の完了を表示し、アドレスバーから通知のクエリを消すこと', async () => {
      signedOut();
      await renderRoute('/login?verified=1');

      expect(await screen.findByRole('status')).toHaveTextContent(
        'メールアドレスの認証が完了しました。ログインしてください。',
      );
      await expectPath('/login');
    });

    it('Google 認証の失敗を表示すること', async () => {
      signedOut();
      await renderRoute('/login?error=social_login_failed&provider=google');

      expect(await screen.findByRole('alert')).toHaveTextContent(
        'Google認証に失敗しました。',
      );
    });

    it('提供元が不明なソーシャルログインの失敗は一般的な文言で表示すること', async () => {
      signedOut();
      await renderRoute('/login?error=social_login_failed&provider=unknown');

      expect(await screen.findByRole('alert')).toHaveTextContent(
        'ソーシャルログインに失敗しました。',
      );
    });

    it('利用停止中のアカウントであることを表示すること', async () => {
      signedOut();
      await renderRoute('/login?error=account_unavailable');

      expect(await screen.findByRole('alert')).toHaveTextContent(
        'このアカウントは現在利用できません。',
      );
    });
  });

  describe('ソーシャルログイン', () => {
    it('Google と LINE のリンクが、Vue 版へ戻る指定付きで Laravel の開始 URL を指すこと', async () => {
      signedOut();
      await renderRoute('/login');

      expect(
        screen.getByRole('link', { name: 'Googleでログイン' }),
      ).toHaveAttribute(
        'href',
        'http://localhost:8000/api/auth/google/redirect?client=vue',
      );
      expect(
        screen.getByRole('link', { name: 'LINEでログイン' }),
      ).toHaveAttribute(
        'href',
        'http://localhost:8000/api/auth/line/redirect?client=vue',
      );
    });
  });

  describe('パスワードの表示切り替え', () => {
    it('押すたびにパスワードの表示・非表示を切り替え、押下状態を伝えること', async () => {
      signedOut();
      const { user } = await renderRoute('/login');
      await user.type(passwordInput(), 'password123');

      await user.click(screen.getByRole('button', { name: 'パスワードを表示' }));

      expect(passwordInput()).toHaveAttribute('type', 'text');
      const hideButton = screen.getByRole('button', {
        name: 'パスワードを隠す',
      });
      expect(hideButton).toHaveAttribute('aria-pressed', 'true');

      await user.click(hideButton);

      expect(passwordInput()).toHaveAttribute('type', 'password');
    });
  });

  describe('公開デモ', () => {
    it('一般ユーザーのデモアカウントを入力済みにし、ソーシャルログインを出さないこと', async () => {
      enableDemoMode();
      signedOut();
      await renderRoute('/login');

      expect(emailInput()).toHaveValue('demo@example.com');
      expect(
        screen.getByRole('button', { name: /一般ユーザー/ }),
      ).toHaveAttribute('aria-pressed', 'true');
      expect(
        screen.queryByRole('link', { name: 'Googleでログイン' }),
      ).not.toBeInTheDocument();
    });

    it('管理者を選ぶと管理者のデモアカウントに切り替えること', async () => {
      enableDemoMode();
      signedOut();
      const { user } = await renderRoute('/login');

      await user.click(screen.getByRole('button', { name: /管理者/ }));

      expect(emailInput()).toHaveValue('demo-admin@example.com');
      expect(passwordInput()).toHaveValue('TicketAdmin2026!');
      expect(screen.getByRole('button', { name: /管理者/ })).toHaveAttribute(
        'aria-pressed',
        'true',
      );
    });

    it('ログイン後はチケット画面へ移ること', async () => {
      enableDemoMode();
      signedOut();
      overrideApi(authApi.loginSucceeds(userFixture()));
      const { user } = await renderRoute('/login');

      await user.click(submitButton());

      await expectPath('/tickets');
    });
  });

  describe('ログイン済みの利用者', () => {
    it('ログイン画面を開くと勤怠画面へ移すこと', async () => {
      signInAs();

      await renderRoute('/login');

      await expectPath('/attendance');
      await waitFor(() => {
        expect(
          screen.queryByRole('button', { name: 'ログイン' }),
        ).not.toBeInTheDocument();
      });
    });
  });
});
