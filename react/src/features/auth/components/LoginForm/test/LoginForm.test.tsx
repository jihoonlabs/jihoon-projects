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

  it('目のアイコンから入力値を保ったままパスワードを表示・非表示にできること', async () => {
    const user = userEvent.setup();
    render(<LoginForm />);
    const password = screen.getByLabelText('パスワード');
    await user.type(password, 'example123');
    const toggle = screen.getByRole('button', { name: 'パスワードを表示' });
    expect(password).toHaveAttribute('type', 'password');
    expect(toggle).toHaveAttribute('aria-pressed', 'false');
    expect(toggle.querySelector('svg')).toHaveAttribute('aria-hidden', 'true');
    expect(toggle).toHaveAttribute('type', 'button');
    await user.click(toggle);
    expect(password).toHaveAttribute('type', 'text');
    expect(password).toHaveValue('example123');
    expect(
      screen.getByRole('button', { name: 'パスワードを隠す' }),
    ).toHaveAttribute('aria-pressed', 'true');
    await user.click(toggle);
    expect(password).toHaveAttribute('type', 'password');
    expect(password).toHaveValue('example123');
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('ブランドアイコンを表示してもソーシャルログインボタンの名前が変わらないこと', () => {
    render(<LoginForm />);
    const googleButton = screen.getByRole('button', {
      name: 'Googleでログイン',
    });
    expect(googleButton).toHaveAttribute('type', 'button');
    expect(googleButton).toBeEnabled();
    expect(googleButton.querySelector('img')).toHaveAttribute('alt', '');
    expect(googleButton.querySelector('img')).toHaveAttribute(
      'aria-hidden',
      'true',
    );

    const lineButton = screen.getByRole('button', { name: 'LINEでログイン' });
    expect(lineButton).toHaveAttribute('type', 'button');
    expect(lineButton).toBeEnabled();
    expect(lineButton.querySelector('img')).toHaveAttribute('alt', '');
    expect(lineButton.querySelector('img')).toHaveAttribute(
      'aria-hidden',
      'true',
    );
  });
});
