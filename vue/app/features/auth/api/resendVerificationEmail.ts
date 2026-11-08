import type { ApiClient } from '~/shared/api/apiClient';

import { sendAccountRequest } from './accountRequest';

export function resendVerificationEmail(
  client: ApiClient,
  email: string,
  signal?: AbortSignal,
) {
  return sendAccountRequest(
    client,
    '/api/auth/email/verification-notification',
    { email: email.trim() },
    {
      fields: ['email'],
      invalid: 'メールアドレスを確認してください。',
      tooMany:
        '認証メールの再送回数が多すぎます。しばらくしてから再度お試しください。',
      fallback: '認証メールの再送に失敗しました。',
    },
    signal,
  );
}
