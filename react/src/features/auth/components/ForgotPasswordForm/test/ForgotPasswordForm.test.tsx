import { render, screen } from '@testing-library/react';

import userEvent from '@testing-library/user-event';

import { describe, expect, it } from 'vitest';

import { ForgotPasswordForm } from '../ForgotPasswordForm';

describe('ForgotPasswordForm 表示・入力検証', () => {
  it('パスワード再設定メール送信フォームが表示されること', () => {
    render(<ForgotPasswordForm />);

    expect(
      screen.getByRole('heading', { name: 'パスワードをお忘れの方' }),
    ).toBeInTheDocument();

    expect(screen.getByLabelText('メールアドレス')).toBeInTheDocument();

    expect(
      screen.getByRole('button', { name: '再設定メールを送信' }),
    ).toBeInTheDocument();
  });

  it('未入力の場合、入力エラーを表示すること', async () => {
    const user = userEvent.setup();

    render(<ForgotPasswordForm />);

    await user.click(
      screen.getByRole('button', { name: '再設定メールを送信' }),
    );

    expect(
      screen.getByText('メールアドレスを入力してください。'),
    ).toBeInTheDocument();

    expect(screen.getByLabelText('メールアドレス')).toHaveAttribute(
      'aria-invalid',
      'true',
    );
  });
});
