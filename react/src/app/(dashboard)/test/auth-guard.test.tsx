import { render, screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { beforeEach, expect, it, vi } from 'vitest';
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
  server.use(
    http.get(`${API_URL}/api/auth/me`, () => HttpResponse.json(user)),
  );

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
