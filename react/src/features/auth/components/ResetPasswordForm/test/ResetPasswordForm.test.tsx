import { render, screen } from '@testing-library/react';

import userEvent from '@testing-library/user-event';

import { describe, expect, it } from 'vitest';

import { ResetPasswordForm } from '../ResetPasswordForm';

describe('ResetPasswordForm 表示・入力検証', () => {
  it('パスワード再設定フォームが表示されること', () => {
    render(<ResetPasswordForm email="user@example.com" token="reset-token" />);

    expect(
      screen.getByRole('heading', { name: 'パスワード再設定' }),
    ).toBeInTheDocument();

    expect(screen.getByLabelText('新しいパスワード')).toBeInTheDocument();

    expect(
      screen.getByLabelText('新しいパスワード（確認）'),
    ).toBeInTheDocument();

    expect(
      screen.getByRole('button', { name: 'パスワードを再設定' }),
    ).toBeInTheDocument();
  });

  it('再設定リンクが正しくない場合、エラーを表示すること', () => {
    render(<ResetPasswordForm email="user@example.com" token="" />);

    expect(
      screen.getByText(
        '再設定リンクが正しくありません。もう一度メールを送信してください。',
      ),
    ).toBeInTheDocument();

    expect(
      screen.queryByRole('button', { name: 'パスワードを再設定' }),
    ).not.toBeInTheDocument();

    expect(
      screen.getByRole('link', {
        name: '再設定メールをもう一度送信する',
      }),
    ).toHaveAttribute('href', '/forgot-password');
  });

  it('未入力の場合、入力エラーを表示すること', async () => {
    const user = userEvent.setup();

    render(<ResetPasswordForm email="user@example.com" token="reset-token" />);

    await user.click(
      screen.getByRole('button', { name: 'パスワードを再設定' }),
    );

    expect(
      screen.getByText('パスワードを入力してください。'),
    ).toBeInTheDocument();

    expect(
      screen.getByText('確認用のパスワードを入力してください。'),
    ).toBeInTheDocument();

    expect(screen.getByLabelText('新しいパスワード')).toHaveAttribute(
      'aria-invalid',
      'true',
    );

    expect(screen.getByLabelText('新しいパスワード（確認）')).toHaveAttribute(
      'aria-invalid',
      'true',
    );
  });

  it('パスワードを確認用パスワードと同じ値に修正した場合、不一致エラーが消えること', async () => {
    const user = userEvent.setup();

    render(<ResetPasswordForm email="user@example.com" token="reset-token" />);

    const passwordInput = screen.getByLabelText('新しいパスワード');

    await user.type(passwordInput, 'password123');

    await user.type(
      screen.getByLabelText('新しいパスワード（確認）'),
      'different123',
    );

    await user.click(
      screen.getByRole('button', { name: 'パスワードを再設定' }),
    );

    expect(screen.getByText('パスワードが一致しません。')).toBeInTheDocument();

    await user.clear(passwordInput);
    await user.type(passwordInput, 'different123');

    expect(
      screen.queryByText('パスワードが一致しません。'),
    ).not.toBeInTheDocument();
  });

  it('パスワードの表示と非表示を切り替えられること', async () => {
    const user = userEvent.setup();

    render(<ResetPasswordForm email="user@example.com" token="reset-token" />);

    const passwordInput = screen.getByLabelText('新しいパスワード');
    const passwordConfirmationInput =
      screen.getByLabelText('新しいパスワード（確認）');

    expect(passwordInput).toHaveAttribute('type', 'password');
    expect(passwordConfirmationInput).toHaveAttribute('type', 'password');

    await user.click(screen.getByRole('button', { name: 'パスワードを表示' }));

    expect(passwordInput).toHaveAttribute('type', 'text');
    expect(passwordConfirmationInput).toHaveAttribute('type', 'text');

    await user.click(screen.getByRole('button', { name: 'パスワードを隠す' }));

    expect(passwordInput).toHaveAttribute('type', 'password');
    expect(passwordConfirmationInput).toHaveAttribute('type', 'password');
  });
});
