import { render, screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { beforeEach, expect, it, vi } from 'vitest';
import { loginApi } from '@/features/auth/api/login';
import { logoutApi } from '@/features/auth/api/logout';
import { AuthInitializer } from '@/features/auth/AuthInitializer';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import type { User } from '@/features/users/types/user';
import { server } from '@/test/mocks/server';
import DashboardLayout from '../layout';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

const { replaceMock } = vi.hoisted(() => ({
  replaceMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: replaceMock }),
  usePathname: () => '/tickets',
}));

const user: User = {
  id: 7,
  name: 'Session User',
  email: 'session@example.com',
  status: 'active',
  role: 'user',
  createdAt: '2026-09-30T00:00:00.000Z',
};

beforeEach(() => {
  replaceMock.mockReset();
  useAuthStore.setState({
    user: null,
    isAuthenticated: false,
    isInitialized: false,
  });
});

it('有効なSanctumセッションを/api/auth/meで確認すると認証が必要な画面を表示すること', async () => {
  server.use(http.get(`${API_URL}/api/auth/me`, () => HttpResponse.json(user)));

  render(
    <>
      <AuthInitializer />
      <DashboardLayout>
        <p>Protected Ticket board</p>
      </DashboardLayout>
    </>,
  );

  expect(await screen.findByText('Protected Ticket board')).toBeInTheDocument();
  expect(replaceMock).not.toHaveBeenCalled();
  expect(useAuthStore.getState().user).toEqual(user);
});

it('/api/auth/meが未認証を示す401を返すとログイン画面へ遷移すること', async () => {
  server.use(
    http.get(`${API_URL}/api/auth/me`, () =>
      HttpResponse.json({}, { status: 401 }),
    ),
  );

  render(
    <>
      <AuthInitializer />
      <DashboardLayout>
        <p>Protected Ticket board</p>
      </DashboardLayout>
    </>,
  );

  await waitFor(() => expect(replaceMock).toHaveBeenCalledWith('/login'));
  expect(screen.queryByText('Protected Ticket board')).not.toBeInTheDocument();
  expect(useAuthStore.getState().isAuthenticated).toBe(false);
});

it('セッションの初回確認の401応答が遅れて届いても、後から成立したログイン状態を維持すること', async () => {
  let deliver!: () => void;
  const pending = new Promise<void>((resolve) => {
    deliver = resolve;
  });
  let started = false;
  server.use(
    http.get(`${API_URL}/api/auth/me`, async () => {
      started = true;
      await pending;
      return HttpResponse.json({}, { status: 401 });
    }),
  );
  render(<AuthInitializer />);
  await waitFor(() => expect(started).toBe(true));
  useAuthStore.getState().login(user);
  deliver();
  await waitFor(() => expect(useAuthStore.getState().isInitialized).toBe(true));
  expect(useAuthStore.getState().user).toEqual(user);
  expect(useAuthStore.getState().isAuthenticated).toBe(true);
});

it('ログアウト後に初回のセッション確認が成功しても、ログイン状態を復元しないこと', async () => {
  let deliver!: () => void;
  const pending = new Promise<void>((resolve) => {
    deliver = resolve;
  });
  let started = false;
  server.use(
    http.get(`${API_URL}/api/auth/me`, async () => {
      started = true;
      await pending;
      return HttpResponse.json(user);
    }),
  );
  render(<AuthInitializer />);
  await waitFor(() => expect(started).toBe(true));
  useAuthStore.getState().logout();
  deliver();
  await waitFor(() => expect(useAuthStore.getState().isInitialized).toBe(true));
  expect(useAuthStore.getState().isAuthenticated).toBe(false);
});

it.each(['login', 'logout'])(
  '%sの認証状態を変更するリクエストを送信する前に、セッションの初回確認を中断すること',
  async (action) => {
    let initialSignal: AbortSignal | undefined;
    server.use(
      http.get(`${API_URL}/api/auth/me`, async ({ request }) => {
        initialSignal = request.signal;
        await new Promise<void>((resolve) =>
          request.signal.addEventListener('abort', () => resolve(), {
            once: true,
          }),
        );
        return HttpResponse.json(user);
      }),
      http.post(`${API_URL}/api/auth/${action}`, () => {
        expect(initialSignal?.aborted).toBe(true);
        return HttpResponse.json({ message: 'OK', user });
      }),
    );
    render(<AuthInitializer />);
    await waitFor(() => expect(initialSignal).toBeDefined());
    if (action === 'login')
      await loginApi({ email: 'session@example.com', password: 'password123' });
    else await logoutApi();
    expect(initialSignal?.aborted).toBe(true);
    await waitFor(() =>
      expect(useAuthStore.getState().isInitialized).toBe(true),
    );
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  },
);
