import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { LoginForm } from '../LoginForm';
import { useAuthStore } from '@/features/auth/store/useAuthStore';

const { replaceMock } = vi.hoisted(() => ({
  replaceMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    replace: replaceMock,
  }),
}));

describe('LoginForm 表示・入力検証', () => {
  beforeEach(() => {
    replaceMock.mockReset();
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isInitialized: true,
    });
  });

  it('ログインフォームが表示されること', () => {
    render(<LoginForm />);

    expect(
      screen.getByRole('heading', { name: 'タスク管理' }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText('メールアドレス')).toBeInTheDocument();
    expect(screen.getByLabelText('パスワード')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'ログイン' }),
    ).toBeInTheDocument();
  });

  it('未入力の場合、エラーを表示してログインAPIを呼び出さないこと', async () => {
    const user = userEvent.setup();

    render(<LoginForm />);

    await user.click(screen.getByRole('button', { name: 'ログイン' }));

    expect(
      screen.getByText('メールアドレスを入力してください。'),
    ).toBeInTheDocument();
    expect(
      screen.getByText('パスワードを入力してください。'),
    ).toBeInTheDocument();
    expect(replaceMock).not.toHaveBeenCalled();
  });
});
