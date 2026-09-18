import { render, screen } from '@testing-library/react';

import userEvent from '@testing-library/user-event';

import { http, HttpResponse } from 'msw';

import { describe, expect, it } from 'vitest';

import { server } from '@/test/mocks/server';

import { ForgotPasswordForm } from '../ForgotPasswordForm';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

describe('ForgotPasswordForm 再設定メール送信処理', () => {
  it('送信成功後、完了メッセージを表示すること', async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_URL}/api/auth/forgot-password`, async ({ request }) => {
        expect(await request.json()).toEqual({
          email: 'user@example.com',
        });

        return HttpResponse.json({
          message: 'パスワード再設定メールを送信しました。',
        });
      }),
    );

    render(<ForgotPasswordForm />);

    await user.type(
      screen.getByLabelText('メールアドレス'),
      'user@example.com',
    );

    await user.click(
      screen.getByRole('button', { name: '再設定メールを送信' }),
    );

    expect(await screen.findByRole('status')).toHaveTextContent(
      'パスワード再設定メールを送信しました。',
    );
  });

  it('送信回数が多すぎる場合、制限メッセージを表示すること', async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_URL}/api/auth/forgot-password`, () => {
        return HttpResponse.json({}, { status: 429 });
      }),
    );

    render(<ForgotPasswordForm />);

    await user.type(
      screen.getByLabelText('メールアドレス'),
      'user@example.com',
    );

    await user.click(
      screen.getByRole('button', { name: '再設定メールを送信' }),
    );

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'パスワード再設定メールの送信回数が多すぎます。しばらくしてから再度お試しください。',
    );
  });
});
