import { fetchWithCsrf } from '@/shared/api/fetchWithCsrf';

import type {
  VerificationEmailResendRequest,
  VerificationEmailResendResponse,
} from '@/features/auth/types/auth';

export const resendVerificationEmailApi = async (
  params: VerificationEmailResendRequest,
): Promise<VerificationEmailResendResponse> => {
  const response = await fetchWithCsrf(
    '/api/auth/email/verification-notification',
    {
      method: 'POST',
      body: JSON.stringify({
        email: params.email.trim(),
      }),
    },
  );

  const data = await response.json();

  if (!response.ok) {
    const errorMessage =
      response.status === 422
        ? (data.errors?.email?.[0] ?? 'メールアドレスを確認してください。')
        : response.status === 429
          ? '認証メールの再送回数が多すぎます。しばらくしてから再度お試しください。'
          : '認証メールの再送に失敗しました。';

    throw new Error(errorMessage);
  }

  return data;
};
