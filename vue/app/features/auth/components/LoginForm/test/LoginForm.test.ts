import { screen, waitFor } from '@testing-library/vue';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { userFixture } from '~/features/users/test/userFixture';
import { attendanceApi } from '~/test/mocks/attendance/attendanceApiHandlers';
import { accountApi } from '~/test/mocks/auth/accountApiHandlers';
import { authApi } from '~/test/mocks/auth/authApiHandlers';
import { signInAs, signedOut } from '~/test/auth/signInAs';
import { enableDemoMode } from '~/test/demoMode';
import { apiUrl } from '~/test/mocks/apiUrl';
import { overrideApi } from '~/test/mocks/overrideApi';
import { expectPath, renderRoute } from '~/test/renderRoute';
import { useNuxtApp } from '#imports';

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
      overrideApi(...attendanceApi.emptyHome());
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
      overrideApi(...attendanceApi.emptyHome());
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
      overrideApi(...attendanceApi.emptyHome());
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

      await user.click(
        screen.getByRole('button', { name: 'パスワードを表示' }),
      );

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

  describe('メール未認証', () => {
    const loginWithUnverifiedEmail = async () => {
      overrideApi(
        authApi.loginFails(403, {
          message: 'メール認証が完了していません。',
          code: 'email_not_verified',
        }),
      );
      const view = await renderRoute('/login');
      await view.user.type(emailInput(), 'user@example.com');
      await view.user.type(passwordInput(), 'password123');
      await view.user.click(submitButton());
      await screen.findByRole('button', { name: '認証メールを再送する' });

      return view;
    };

    it('再送ボタンで入力中のメールアドレスに認証メールを再送し、結果を表示すること', async () => {
      signedOut();
      const { user } = await loginWithUnverifiedEmail();
      const received: { body?: unknown } = {};
      overrideApi(
        accountApi.records(
          '/api/auth/email/verification-notification',
          received,
        ),
      );

      await user.click(
        screen.getByRole('button', { name: '認証メールを再送する' }),
      );

      expect(await screen.findByRole('status')).toHaveTextContent(
        '送信しました。',
      );
      expect(received.body).toEqual({ email: 'user@example.com' });
      expect(
        screen.queryByRole('button', { name: '認証メールを再送する' }),
      ).not.toBeInTheDocument();
    });

    it('再送に失敗したらエラーを表示し、再送ボタンを残すこと', async () => {
      signedOut();
      const { user } = await loginWithUnverifiedEmail();
      overrideApi(
        accountApi.fails('/api/auth/email/verification-notification', 429),
      );

      await user.click(
        screen.getByRole('button', { name: '認証メールを再送する' }),
      );

      expect(await screen.findByRole('alert')).toHaveTextContent(
        '認証メールの再送回数が多すぎます。しばらくしてから再度お試しください。',
      );
      expect(
        screen.getByRole('button', { name: '認証メールを再送する' }),
      ).toBeEnabled();
    });

    it('再送中にメールアドレスを変えたら、遅れて届いた再送結果を表示しないこと', async () => {
      signedOut();
      const { user } = await loginWithUnverifiedEmail();
      // 中断された要求は応答を待つ処理まで届かないことがあるため、未到達でも呼べるようにしておく
      let release: () => void = () => undefined;
      overrideApi(
        http.post(
          apiUrl('/api/auth/email/verification-notification'),
          async () => {
            await new Promise<void>((resolve) => {
              release = resolve;
            });
            return HttpResponse.json({ message: '古い宛先に送信しました。' });
          },
        ),
      );
      await user.click(
        screen.getByRole('button', { name: '認証メールを再送する' }),
      );
      await screen.findByRole('button', { name: '認証メールを再送中...' });

      await user.type(emailInput(), 'x');
      release();

      await waitFor(() => {
        expect(
          screen.queryByRole('button', { name: /認証メールを再送/ }),
        ).not.toBeInTheDocument();
      });
      expect(
        screen.queryByText('古い宛先に送信しました。'),
      ).not.toBeInTheDocument();
    });
  });

  describe('アカウント関連の導線', () => {
    it('パスワード再設定と会員登録の画面へのリンクを表示すること', async () => {
      signedOut();
      await renderRoute('/login');

      expect(
        screen.getByRole('link', { name: 'パスワードをお忘れですか？' }),
      ).toHaveAttribute('href', '/forgot-password');
      expect(
        screen.getByRole('link', { name: '新規会員登録へ' }),
      ).toHaveAttribute('href', '/register');
    });

    it('パスワード再設定のリンクを押すと、再設定の画面へ移ること', async () => {
      signedOut();
      const { user, router } = await renderRoute('/login');
      const link = screen.getByRole('link', { name: 'パスワードをお忘れですか？' });
      const pushes: unknown[] = [];
      const originalPush = router.push.bind(router);
      router.push = ((to: never) => {
        pushes.push(to);
        return originalPush(to).then((r: unknown) => {
          console.log('DIAG push result', String(r));
          return r;
        });
      }) as typeof router.push;
      router.afterEach((to, from, failure) =>
        console.log('DIAG afterEach', from.fullPath, '->', to.fullPath, String(failure)),
      );
      let prevented: boolean | undefined;
      document.addEventListener('click', (e) => { prevented = e.defaultPrevented; }, { once: true });
      const nuxtApp = useNuxtApp() as unknown as Record<string, unknown>;
      console.log('DIAG processingMiddleware before', String(nuxtApp._processingMiddleware), 'router same', nuxtApp.$router === router);
      {
        const fs = await import('node:fs');
        const path = await import('node:path');
        const root = path.resolve(process.cwd(), 'node_modules/@nuxt/test-utils/dist');
        const walk = (dir: string): string[] => fs.readdirSync(dir, { withFileTypes: true }).flatMap((d) => d.isDirectory() ? walk(path.join(dir, d.name)) : [path.join(dir, d.name)]);
        for (const file of walk(root)) {
          if (!/\.m?js$/.test(file)) continue;
          const lines = fs.readFileSync(file, 'utf8').split('\n');
          lines.forEach((l, n) => {
            if (/RouterLink|navigate/.test(l)) console.log('DIAG TU', path.relative(root, file), n + 1, l.slice(0, 220));
          });
        }
      }
      console.log('DIAG link', link.outerHTML);

      await user.click(link);
      await new Promise((r) => setTimeout(r, 300));
      console.log('DIAG pushes', JSON.stringify(pushes), 'prevented', prevented, 'path', router.currentRoute.value.fullPath, 'location', window.location.href);

      await expectPath('/forgot-password');
      expect(
        await screen.findByRole('heading', { name: 'パスワードをお忘れの方' }),
      ).toBeInTheDocument();
    });

    it('公開デモではパスワード再設定と会員登録のリンクを出さないこと', async () => {
      enableDemoMode();
      signedOut();
      await renderRoute('/login');

      expect(
        screen.queryByRole('link', { name: 'パスワードをお忘れですか？' }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole('link', { name: '新規会員登録へ' }),
      ).not.toBeInTheDocument();
    });
  });

  describe('ログイン済みの利用者', () => {
    it('ログイン画面を開くと勤怠画面へ移すこと', async () => {
      signInAs();
      overrideApi(...attendanceApi.emptyHome());

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
