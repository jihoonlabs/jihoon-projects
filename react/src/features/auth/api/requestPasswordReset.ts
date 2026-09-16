import { fetchWithCsrf } from '@/shared/api/fetchWithCsrf';

import type {
  PasswordResetLinkRequest,
  PasswordResetLinkResponse,
} from '@/features/auth/types/auth';

export const requestPasswordResetApi = async (
  params: PasswordResetLinkRequest,
): Promise<PasswordResetLinkResponse> => {
  const response = await fetchWithCsrf('/api/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({
      email: params.email.trim(),
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    const errorMessage =
      response.status === 422
        ? (data.errors?.email?.[0] ?? 'メールアドレスを確認してください。')
        : response.status === 429
          ? 'パスワード再設定メールの送信回数が多すぎます。しばらくしてから再度お試しください。'
          : 'パスワード再設定メールの送信に失敗しました。';

    throw new Error(errorMessage);
  }

  return data;
};