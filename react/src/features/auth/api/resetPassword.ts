import { fetchWithCsrf } from '@/shared/api/fetchWithCsrf';

import type {
  PasswordResetRequest,
  PasswordResetResponse,
} from '@/features/auth/types/auth';

export const resetPasswordApi = async (
  params: PasswordResetRequest,
): Promise<PasswordResetResponse> => {
  const response = await fetchWithCsrf('/api/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({
      email: params.email.trim(),
      token: params.token,
      password: params.password,
      password_confirmation: params.passwordConfirmation,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    const validationMessage =
      data.errors?.password?.[0] ??
      data.errors?.password_confirmation?.[0] ??
      data.errors?.email?.[0] ??
      data.errors?.token?.[0];

    if (response.status === 422) {
      throw new Error(
        validationMessage ??
          data.message ??
          'メールアドレスまたは再設定トークンを確認してください。',
      );
    }

    if (response.status === 429) {
      throw new Error(
        'パスワード再設定の試行回数が多すぎます。しばらくしてから再度お試しください。',
      );
    }

    throw new Error('パスワードの再設定に失敗しました。');
  }

  return data;
};
