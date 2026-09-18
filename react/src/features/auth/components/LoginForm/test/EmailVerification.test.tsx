import { render, screen } from '@testing-library/react';
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
