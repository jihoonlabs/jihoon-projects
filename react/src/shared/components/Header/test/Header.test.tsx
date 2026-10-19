import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { logoutApi } from '@/features/auth/api/logout';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { Header } from '..';

const { replace } = vi.hoisted(() => ({ replace: vi.fn() }));
vi.mock('next/navigation', () => ({ useRouter: () => ({ replace }) }));
vi.mock('@/features/auth/api/logout', () => ({ logoutApi: vi.fn() }));

beforeEach(() => {
  vi.clearAllMocks();
  useAuthStore.setState({
    user: {
      id: 7,
      name: 'Tester',
      email: 'test@example.com',
      role: 'admin',
      status: 'active',
      createdAt: '',
    },
    isAuthenticated: true,
    isInitialized: true,
  });
});

it('waits for server logout before clearing the session and blocks duplicate requests', async () => {
  let complete!: () => void;
  vi.mocked(logoutApi).mockImplementation(
    () =>
      new Promise<void>((resolve) => {
        complete = resolve;
      }),
  );
  render(<Header />);
  expect(screen.getByText(/管理者/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'ログアウト' }));
  const pending = screen.getByRole('button', { name: 'ログアウト中...' });
  expect(pending).toBeDisabled();
  fireEvent.click(pending);
  expect(logoutApi).toHaveBeenCalledTimes(1);
  expect(useAuthStore.getState().isAuthenticated).toBe(true);
  complete();
  await waitFor(() => expect(replace).toHaveBeenCalledWith('/login'));
  expect(useAuthStore.getState().user).toBeNull();
});

it('keeps the session on failure and allows a retry', async () => {
  vi.mocked(logoutApi)
    .mockRejectedValueOnce(new Error('offline'))
    .mockResolvedValueOnce();
  render(<Header />);
  fireEvent.click(screen.getByRole('button', { name: 'ログアウト' }));
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'ログアウトできませんでした',
  );
  expect(useAuthStore.getState().isAuthenticated).toBe(true);
  expect(replace).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'ログアウト' }));
  await waitFor(() => expect(replace).toHaveBeenCalledWith('/login'));
});
