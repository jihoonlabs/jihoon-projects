import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { server } from '@/test/mocks/server';

import { RegisterForm } from '../RegisterForm';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

const { pushMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));

describe('RegisterForm 会員登録処理', () => {
  beforeEach(() => {
    pushMock.mockReset();
  });

  it('会員登録成功後、ログイン画面へ遷移すること', async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_URL}/api/auth/register`, async ({ request }) => {
        expect(await request.json()).toEqual({
          name: 'テストユーザー',
          email: 'user@example.com',
          password: 'password123',
          password_confirmation: 'password123',
        });

        return HttpResponse.json({
          message: '会員登録が完了しました。',
          user: {
            id: 1,
            name: 'テストユーザー',
            email: 'user@example.com',
            status: 'active',
            createdAt: '2026-09-17T00:00:00.000Z',
          },
        });
      }),
    );

    render(<RegisterForm />);

    await user.type(screen.getByLabelText('名前'), 'テストユーザー');
    await user.type(
      screen.getByLabelText('メールアドレス'),
      'user@example.com',
    );
    await user.type(screen.getByLabelText('パスワード'), 'password123');
    await user.type(screen.getByLabelText('パスワード確認'), 'password123');
    await user.click(
      screen.getByRole('button', { name: 'メールアドレスで登録' }),
    );

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith('/login?registered=1');
    });
  });

  it('メールアドレスが登録済みの場合、エラーメッセージを表示すること', async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_URL}/api/auth/register`, () => {
        return HttpResponse.json(
          {
            errors: {
              email: ['このメールアドレスは既に使用されています。'],
            },
          },
          { status: 422 },
        );
      }),
    );

    render(<RegisterForm />);

    await user.type(screen.getByLabelText('名前'), 'テストユーザー');
    await user.type(
      screen.getByLabelText('メールアドレス'),
      'user@example.com',
    );
    await user.type(screen.getByLabelText('パスワード'), 'password123');
    await user.type(screen.getByLabelText('パスワード確認'), 'password123');
    await user.click(
      screen.getByRole('button', { name: 'メールアドレスで登録' }),
    );

    expect(
      await screen.findByText('このメールアドレスは既に使用されています。'),
    ).toBeInTheDocument();
    expect(pushMock).not.toHaveBeenCalled();
  });

  it('登録試行回数が多すぎる場合、制限メッセージを表示すること', async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_URL}/api/auth/register`, () => {
        return HttpResponse.json({}, { status: 429 });
      }),
    );

    render(<RegisterForm />);

    await user.type(screen.getByLabelText('名前'), 'テストユーザー');
    await user.type(
      screen.getByLabelText('メールアドレス'),
      'user@example.com',
    );
    await user.type(screen.getByLabelText('パスワード'), 'password123');
    await user.type(screen.getByLabelText('パスワード確認'), 'password123');
    await user.click(
      screen.getByRole('button', { name: 'メールアドレスで登録' }),
    );

    expect(
      await screen.findByText(
        '登録試行回数が多すぎます。しばらくしてから再度お試しください。',
      ),
    ).toBeInTheDocument();
    expect(pushMock).not.toHaveBeenCalled();
  });
});
