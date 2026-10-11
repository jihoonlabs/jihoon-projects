import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react';
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
  role: 'user',
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

describe('LoginForm request boundaries', () => {
  beforeEach(() => {
    pushMock.mockReset();
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isInitialized: true,
    });
  });

  const fill = async () => {
    const user = userEvent.setup();
    await user.type(
      screen.getByLabelText('メールアドレス'),
      'user@example.com',
    );
    await user.type(screen.getByLabelText('パスワード'), 'password123');
    return user;
  };

  it('submits with Enter while the password is visible, without submitting from the toggle', async () => {
    let requests = 0;
    server.use(
      http.post(`${API_URL}/api/auth/login`, () => {
        requests++;
        return HttpResponse.json({ message: 'OK', user: mockUser });
      }),
    );
    render(<LoginForm />);
    const user = await fill();
    await user.click(screen.getByRole('button', { name: 'パスワードを表示' }));
    expect(screen.getByLabelText('パスワード')).toHaveAttribute('type', 'text');
    expect(
      screen.getByRole('button', { name: 'パスワードを隠す' }),
    ).toHaveAttribute('aria-pressed', 'true');
    expect(requests).toBe(0);
    await user.click(screen.getByRole('button', { name: 'パスワードを隠す' }));
    expect(screen.getByLabelText('パスワード')).toHaveAttribute(
      'type',
      'password',
    );
    await user.click(screen.getByLabelText('パスワード'));
    await user.keyboard('{Enter}');
    await waitFor(() => expect(pushMock).toHaveBeenCalledWith('/tickets'));
    expect(requests).toBe(1);
  });

  it.each([
    [
      () => new HttpResponse('<html>Server failure</html>', { status: 500 }),
      'ログイン処理に失敗',
    ],
    [() => HttpResponse.json({ message: 'OK' }), '応答形式'],
    [
      () =>
        HttpResponse.json({
          message: 'OK',
          user: { ...mockUser, status: 'suspended' },
        }),
      '応答形式',
    ],
    [() => HttpResponse.error(), 'ネットワーク'],
  ])(
    'keeps unauthenticated state for invalid or failed responses',
    async (response, message) => {
      server.use(http.post(`${API_URL}/api/auth/login`, response));
      render(<LoginForm />);
      const user = await fill();
      await user.click(screen.getByRole('button', { name: 'ログイン' }));
      expect(await screen.findByRole('alert')).toHaveTextContent(message);
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
      expect(pushMock).not.toHaveBeenCalled();
      expect(screen.getByLabelText('パスワード')).toHaveValue('password123');
      expect(screen.getByRole('button', { name: 'ログイン' })).toBeEnabled();
    },
  );
});

it('locks repeated submits, exposes loading and permits a retry after failure', async () => {
  pushMock.mockReset();
  useAuthStore.setState({
    user: null,
    isAuthenticated: false,
    isInitialized: true,
  });
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  let requests = 0;
  server.use(
    http.post(`${API_URL}/api/auth/login`, async () => {
      requests++;
      await gate;
      return HttpResponse.json(
        { errors: { email: ['Rejected'] } },
        { status: 422 },
      );
    }),
  );
  render(<LoginForm />);
  fireEvent.change(screen.getByLabelText('メールアドレス'), {
    target: { value: 'user@example.com' },
  });
  fireEvent.change(screen.getByLabelText('パスワード'), {
    target: { value: 'password123' },
  });
  const form = screen
    .getByRole('button', { name: 'ログイン' })
    .closest('form')!;
  act(() => {
    fireEvent.submit(form);
    fireEvent.submit(form);
  });
  await waitFor(() => expect(requests).toBe(1));
  expect(screen.getByRole('status')).toHaveTextContent('ログイン中');
  expect(screen.getByRole('button', { name: 'ログイン中...' })).toBeDisabled();
  expect(screen.getByLabelText('パスワード')).toBeDisabled();
  expect(
    screen.getByRole('button', { name: 'Googleでログイン' }),
  ).toBeDisabled();
  expect(screen.getByRole('button', { name: 'LINEでログイン' })).toBeDisabled();
  await act(async () => release());
  expect(await screen.findByRole('alert')).toHaveTextContent('Rejected');
  expect(screen.getByRole('button', { name: 'ログイン' })).toBeEnabled();
  server.use(
    http.post(`${API_URL}/api/auth/login`, () =>
      HttpResponse.json({ message: 'OK', user: mockUser }),
    ),
  );
  fireEvent.submit(form);
  await waitFor(() => expect(pushMock).toHaveBeenCalledWith('/tickets'));
});
