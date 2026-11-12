import { act, render, screen, fireEvent } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { useState } from 'react';
import DashboardLayout from '@/app/(dashboard)/layout';
import { useAuthStore } from '../../store/useAuthStore';
import type { User } from '@/features/users/types/user';
const { replace } = vi.hoisted(() => ({ replace: vi.fn() }));
vi.mock('next/navigation', () => ({ useRouter: () => ({ replace }) }));
vi.mock('@/shared/components/Header', () => ({
  Header: () => <header>Private header</header>,
}));
vi.mock('@/shared/components/AppSidebar', () => ({
  AppSidebar: () => <aside>Private navigation</aside>,
}));
vi.mock('../LoginForm/LoginForm', () => ({
  LoginForm: () => <div>Login form</div>,
}));
const user: User = {
  id: 1,
  name: 'User',
  email: 'user@example.com',
  role: 'user',
  status: 'active',
  createdAt: '',
};
function Draft() {
  const [text, setText] = useState('');
  return (
    <input
      aria-label="draft"
      value={text}
      onChange={(event) => setText(event.target.value)}
    />
  );
}
beforeEach(() => {
  replace.mockClear();
  useAuthStore.getState().login(user);
  useAuthStore.getState().initialize();
});
it('セッション失効時は認証が必要な内容を隠し、同じユーザーの再ログイン後に下書きを復元すること', () => {
  render(
    <DashboardLayout>
      <Draft />
    </DashboardLayout>,
  );
  fireEvent.change(screen.getByLabelText('draft'), {
    target: { value: 'Unsaved ticket' },
  });
  act(() => useAuthStore.getState().expireSession());
  expect(screen.getByRole('alert')).toHaveTextContent('有効期限');
  expect(screen.getByLabelText('draft')).not.toBeVisible();
  expect(screen.queryByText('Private header')).not.toBeInTheDocument();
  expect(replace).not.toHaveBeenCalled();
  act(() => useAuthStore.getState().login(user));
  expect(screen.getByLabelText('draft')).toBeVisible();
  expect(screen.getByLabelText('draft')).toHaveValue('Unsaved ticket');
});
it('別のアカウントで再ログインしても以前のアカウントの下書きを復元しないこと', () => {
  render(
    <DashboardLayout>
      <Draft />
    </DashboardLayout>,
  );
  fireEvent.change(screen.getByLabelText('draft'), {
    target: { value: 'Private draft' },
  });
  act(() => useAuthStore.getState().expireSession());
  act(() => useAuthStore.getState().login({ ...user, id: 2 }));
  expect(screen.getByLabelText('draft')).toHaveValue('');
});
it('明示的にログアウトすると内容を取り除いてログイン画面へ遷移すること', () => {
  render(
    <DashboardLayout>
      <Draft />
    </DashboardLayout>,
  );
  act(() => useAuthStore.getState().logout());
  expect(screen.queryByLabelText('draft')).not.toBeInTheDocument();
  expect(replace).toHaveBeenCalledWith('/login');
});
