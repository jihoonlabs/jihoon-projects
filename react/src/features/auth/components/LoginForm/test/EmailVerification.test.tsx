import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { server } from '@/test/mocks/server';

import { LoginForm } from '../LoginForm';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

const { pushMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));

describe('LoginForm メール認証処理', () => {
  beforeEach(() => {
    pushMock.mockReset();

    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isInitialized: false,
    });
  });

  it('メール未認証の場合、エラーと認証メール再送ボタンを表示すること', async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_URL}/api/auth/login`, () => {
        return HttpResponse.json(
          {
            message: 'メール認証が完了していません。',
            code: 'email_not_verified',
          },
          { status: 403 },
        );
      }),
    );

    render(<LoginForm />);

    await user.type(
      screen.getByLabelText('メールアドレス'),
      'user@example.com',
    );
    await user.type(screen.getByLabelText('パスワード'), 'password123');
    await user.click(screen.getByRole('button', { name: 'ログイン' }));

    expect(
      await screen.findByText('メール認証が完了していません。'),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: '認証メールを再送する' }),
    ).toBeInTheDocument();

    expect(pushMock).not.toHaveBeenCalled();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  it.each([
    [false, false],
    [false, true],
    [true, false],
    [true, true],
  ])(
    'keeps newer login recovery after delayed resend (failure: %s, email change: %s)',
    async (fails, changeEmail) => {
      const user = userEvent.setup();
      let release!: () => void;
      let started = false;
      let resendSignal: AbortSignal | undefined;
      let loginCount = 0;
      const pending = new Promise<void>((resolve) => {
        release = resolve;
      });
      server.use(
        http.post(`${API_URL}/api/auth/login`, () => {
          loginCount += 1;
          return HttpResponse.json(
            {
              message:
                loginCount === 2
                  ? 'New login needs verification'
                  : 'First account needs verification',
              code: 'email_not_verified',
            },
            { status: 403 },
          );
        }),
        http.post(
          `${API_URL}/api/auth/email/verification-notification`,
          async ({ request }) => {
            resendSignal = request.signal;
            expect(await request.json()).toEqual({
              email: 'first@example.com',
            });
            started = true;
            await pending;
            return fails
              ? HttpResponse.json({}, { status: 429 })
              : HttpResponse.json({
                  message: 'First account resend completed',
                });
          },
        ),
      );
      render(<LoginForm />);
      const email = screen.getByLabelText('メールアドレス');
      await user.type(email, 'first@example.com');
      await user.type(screen.getByLabelText('パスワード'), 'password123');
      await user.click(screen.getByRole('button', { name: 'ログイン' }));
      await user.click(
        await screen.findByRole('button', { name: '認証メールを再送する' }),
      );
      await waitFor(() => expect(started).toBe(true));

      if (changeEmail) {
        await user.clear(email);
        await user.type(email, 'second@example.com');
      }
      await user.click(screen.getByRole('button', { name: 'ログイン' }));
      expect(await screen.findByRole('alert')).toHaveTextContent(
        'New login needs verification',
      );
      expect(resendSignal?.aborted).toBe(true);
      await act(async () => {
        release();
      });
      await screen.findByRole('button', { name: '認証メールを再送する' });

      expect(screen.getByRole('alert')).toHaveTextContent(
        'New login needs verification',
      );
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
      expect(email).toHaveValue(
        changeEmail ? 'second@example.com' : 'first@example.com',
      );
      expect(pushMock).not.toHaveBeenCalled();
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    },
  );

  it('認証メールの再送に成功した場合、成功メッセージを表示すること', async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_URL}/api/auth/login`, () => {
        return HttpResponse.json(
          {
            message: 'メール認証が完了していません。',
            code: 'email_not_verified',
          },
          { status: 403 },
        );
      }),
      http.post(
        `${API_URL}/api/auth/email/verification-notification`,
        async ({ request }) => {
          expect(await request.json()).toEqual({
            email: 'user@example.com',
          });

          return HttpResponse.json({
            message: '認証メールを再送しました。',
          });
        },
      ),
    );

    render(<LoginForm />);

    await user.type(
      screen.getByLabelText('メールアドレス'),
      'user@example.com',
    );
    await user.type(screen.getByLabelText('パスワード'), 'password123');
    await user.click(screen.getByRole('button', { name: 'ログイン' }));

    const resendButton = await screen.findByRole('button', {
      name: '認証メールを再送する',
    });

    await user.click(resendButton);

    const successMessage = await screen.findByRole('status');

    expect(successMessage).toHaveTextContent('認証メールを再送しました。');
    expect(
      screen.queryByRole('button', { name: '認証メールを再送する' }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText('メール認証が完了していません。'),
    ).not.toBeInTheDocument();
  });

  it('認証メールの再送回数が多すぎる場合、制限メッセージを表示すること', async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_URL}/api/auth/login`, () => {
        return HttpResponse.json(
          {
            message: 'メール認証が完了していません。',
            code: 'email_not_verified',
          },
          { status: 403 },
        );
      }),
      http.post(`${API_URL}/api/auth/email/verification-notification`, () => {
        return HttpResponse.json({}, { status: 429 });
      }),
    );

    render(<LoginForm />);

    await user.type(
      screen.getByLabelText('メールアドレス'),
      'user@example.com',
    );
    await user.type(screen.getByLabelText('パスワード'), 'password123');
    await user.click(screen.getByRole('button', { name: 'ログイン' }));

    const resendButton = await screen.findByRole('button', {
      name: '認証メールを再送する',
    });

    await user.click(resendButton);

    expect(
      await screen.findByText(
        '認証メールの再送回数が多すぎます。しばらくしてから再度お試しください。',
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: '認証メールを再送する' }),
    ).toBeInTheDocument();
  });
});
