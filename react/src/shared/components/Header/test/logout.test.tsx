import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, it, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { Header } from '..';
const { push } = vi.hoisted(() => ({ push: vi.fn() }));
vi.mock('next/navigation', () => ({ useRouter: () => ({ push }) }));
const api = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
beforeEach(() => {
  push.mockReset();
  useAuthStore.setState({
    user: {
      id: 1,
      name: 'User',
      email: 'user@example.com',
      status: 'active',
      role: 'user',
      createdAt: '2026-10-12',
    },
    isAuthenticated: true,
    isInitialized: true,
  });
});
it('keeps auth state on a rejected logout, reports failure and permits successful retry', async () => {
  server.use(
    http.post(`${api}/api/auth/logout`, () =>
      HttpResponse.json({}, { status: 500 }),
    ),
  );
  render(<Header />);
  const user = userEvent.setup();
  await user.click(screen.getByRole('button', { name: 'ログアウト' }));
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'ログアウトに失敗',
  );
  expect(useAuthStore.getState().isAuthenticated).toBe(true);
  expect(push).not.toHaveBeenCalled();
  server.use(http.post(`${api}/api/auth/logout`, () => HttpResponse.json({})));
  await user.click(screen.getByRole('button', { name: 'ログアウト' }));
  await waitFor(() => expect(push).toHaveBeenCalledWith('/login'));
  expect(useAuthStore.getState().isAuthenticated).toBe(false);
});
