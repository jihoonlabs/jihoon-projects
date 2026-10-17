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

it('allows a valid Sanctum session after /api/auth/me initializes the auth store', async () => {
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

it('redirects to login when /api/auth/me rejects an unauthenticated session', async () => {
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

it('does not let an obsolete initial session response erase a newer successful login', async () => {
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

it('does not let an obsolete session success restore a session after logout', async () => {
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
  'aborts initial session lookup before %s sends a credential-changing request',
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
