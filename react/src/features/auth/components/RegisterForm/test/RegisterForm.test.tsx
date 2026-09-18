import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { RegisterForm } from '../RegisterForm';

const { pushMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));

describe('RegisterForm 表示・入力検証', () => {
  beforeEach(() => {
    pushMock.mockReset();
  });

  it('会員登録フォームが表示されること', () => {
    render(<RegisterForm />);

    expect(
      screen.getByRole('heading', { name: '会員登録' }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText('名前')).toBeInTheDocument();
    expect(screen.getByLabelText('メールアドレス')).toBeInTheDocument();
    expect(screen.getByLabelText('パスワード')).toBeInTheDocument();
    expect(screen.getByLabelText('パスワード確認')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'メールアドレスで登録' }),
    ).toBeInTheDocument();
  });

  it('未入力の場合、エラーを表示して会員登録APIを呼び出さないこと', async () => {
    const user = userEvent.setup();

    render(<RegisterForm />);

    await user.click(
      screen.getByRole('button', { name: 'メールアドレスで登録' }),
    );

    expect(screen.getByText('名前を入力してください。')).toBeInTheDocument();
    expect(
      screen.getByText('メールアドレスを入力してください。'),
    ).toBeInTheDocument();
    expect(
      screen.getByText('パスワードを入力してください。'),
    ).toBeInTheDocument();
    expect(
      screen.getByText('確認用のパスワードを入力してください。'),
    ).toBeInTheDocument();

    expect(pushMock).not.toHaveBeenCalled();
  });
});
