import type { ApiClient } from '~/shared/api/apiClient';

import type { PasswordReset } from '../types/auth';

import { sendAccountRequest } from './accountRequest';

export function resetPassword(client: ApiClient, reset: PasswordReset) {
  return sendAccountRequest(
    client,
    '/api/auth/reset-password',
    {
      email: reset.email.trim(),
      token: reset.token,
      password: reset.password,
      password_confirmation: reset.passwordConfirmation,
    },
    {
      fields: ['password', 'password_confirmation', 'email', 'token'],
      invalid: 'メールアドレスまたは再設定トークンを確認してください。',
      tooMany:
        'パスワード再設定の試行回数が多すぎます。しばらくしてから再度お試しください。',
      fallback: 'パスワードの再設定に失敗しました。',
      useServerMessage: true,
    },
  );
}
