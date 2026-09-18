import { render, screen } from '@testing-library/react';

import userEvent from '@testing-library/user-event';

import { http, HttpResponse } from 'msw';

import { describe, expect, it } from 'vitest';

import { server } from '@/test/mocks/server';

import { ResetPasswordForm } from '../ResetPasswordForm';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

describe('ResetPasswordForm パスワード再設定処理', () => {
  it('再設定成功後、完了メッセージを表示すること', async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_URL}/api/auth/reset-password`, async ({ request }) => {
        expect(await request.json()).toEqual({
          email: 'user@example.com',
          token: 'reset-token',
          password: 'password123',
          password_confirmation: 'password123',
        });

        return HttpResponse.json({
          message: 'パスワードを再設定しました。',
        });
      }),
    );

    render(<ResetPasswordForm email="user@example.com" token="reset-token" />);

    await user.type(screen.getByLabelText('新しいパスワード'), 'password123');

    await user.type(
      screen.getByLabelText('新しいパスワード（確認）'),
      'password123',
    );

    await user.click(
      screen.getByRole('button', { name: 'パスワードを再設定' }),
    );

    expect(await screen.findByRole('status')).toHaveTextContent(
      'パスワードを再設定しました。',
    );
  });

  it('再設定トークンが正しくない場合、エラーを表示すること', async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_URL}/api/auth/reset-password`, () => {
        return HttpResponse.json(
          {
            message: '入力内容に誤りがあります。',
            errors: {
              token: ['再設定トークンが正しくありません。'],
            },
          },
          { status: 422 },
        );
      }),
    );

    render(
      <ResetPasswordForm email="user@example.com" token="invalid-token" />,
    );

    await user.type(screen.getByLabelText('新しいパスワード'), 'password123');

    await user.type(
      screen.getByLabelText('新しいパスワード（確認）'),
      'password123',
    );

    await user.click(
      screen.getByRole('button', { name: 'パスワードを再設定' }),
    );

    expect(await screen.findByRole('alert')).toHaveTextContent(
      '再設定トークンが正しくありません。',
    );

    await user.type(screen.getByLabelText('新しいパスワード'), '4');

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('再設定回数が多すぎる場合、制限メッセージを表示すること', async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_URL}/api/auth/reset-password`, () => {
        return HttpResponse.json({}, { status: 429 });
      }),
    );

    render(<ResetPasswordForm email="user@example.com" token="reset-token" />);

    await user.type(screen.getByLabelText('新しいパスワード'), 'password123');

    await user.type(
      screen.getByLabelText('新しいパスワード（確認）'),
      'password123',
    );

    await user.click(
      screen.getByRole('button', { name: 'パスワードを再設定' }),
    );

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'パスワード再設定の試行回数が多すぎます。しばらくしてから再度お試しください。',
    );
  });
});
