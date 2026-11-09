import type { ApiClient } from '~/shared/api/apiClient';

import { sendAccountRequest } from './accountRequest';

export function requestPasswordReset(client: ApiClient, email: string) {
  return sendAccountRequest(
    client,
    '/api/auth/forgot-password',
    { email: email.trim() },
    {
      fields: ['email'],
      invalid: 'メールアドレスを確認してください。',
      tooMany:
        'パスワード再設定メールの送信回数が多すぎます。しばらくしてから再度お試しください。',
      fallback: 'パスワード再設定メールの送信に失敗しました。',
    },
  );
}
