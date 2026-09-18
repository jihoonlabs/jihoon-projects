import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useAuthStore } from '@/features/auth/store/useAuthStore';
import type { User } from '@/features/users/types/user';
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

const mockUser: User = {
  id: 1,
  email: 'user@example.com',
  name: 'Test User',
  status: 'active',
  createdAt: '2026-09-17T00:00:00.000Z',
};

describe('LoginForm ログイン処理', () => {
  beforeEach(() => {
    pushMock.mockReset();

    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isInitialized: false,
    });
  });

  it('ログイン成功後、ユーザー情報を保存してチケット一覧へ遷移すること', async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_URL}/api/auth/login`, async ({ request }) => {
        expect(await request.json()).toEqual({
          email: 'user@example.com',
          password: 'password123',
        });

        return HttpResponse.json({
          message: 'ログインしました。',
          user: mockUser,
        });
      }),
    );

    render(<LoginForm />);

    await user.type(
      screen.getByLabelText('メールアドレス'),
      'user@example.com',
    );
    await user.type(screen.getByLabelText('パスワード'), 'password123');
    await user.click(screen.getByRole('button', { name: 'ログイン' }));

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith('/tickets');
    });

    expect(useAuthStore.getState().user).toEqual(mockUser);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });

  it('ログイン情報が正しくない場合、エラーメッセージを表示すること', async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_URL}/api/auth/login`, () => {
        return HttpResponse.json(
          {
            errors: {
              email: ['メールアドレスまたはパスワードが正しくありません。'],
            },
          },
          { status: 422 },
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
      await screen.findByText(
        'メールアドレスまたはパスワードが正しくありません。',
      ),
    ).toBeInTheDocument();

    expect(pushMock).not.toHaveBeenCalled();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  it('ログイン試行回数が多すぎる場合、制限メッセージを表示すること', async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_URL}/api/auth/login`, () => {
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

    expect(
      await screen.findByText(
        'ログイン試行回数が多すぎます。しばらくしてから再度お試しください。',
      ),
    ).toBeInTheDocument();

    expect(pushMock).not.toHaveBeenCalled();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
});
