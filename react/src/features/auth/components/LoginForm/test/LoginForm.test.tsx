import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { LoginForm } from '../LoginForm';

const { pushMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));

describe('LoginForm 表示・入力検証', () => {
  beforeEach(() => {
    pushMock.mockReset();
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
    expect(pushMock).not.toHaveBeenCalled();
  });
});
