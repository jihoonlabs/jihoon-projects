import { fetchWithCsrf } from '@/shared/api/fetchWithCsrf';

import type { LoginRequest, LoginResponse } from '@/features/auth/types/auth';

export class LoginApiError extends Error {
  constructor(
    message: string,
    public readonly code?: string,
  ) {
    super(message);
    this.name = 'LoginApiError';
  }
}

export const loginApi = async (
  params: LoginRequest,
): Promise<LoginResponse> => {
  const response = await fetchWithCsrf('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(params),
  });

  const data = await response.json();

  if (!response.ok) {
    const errorCode =
      response.status === 403 && data.code === 'email_not_verified'
        ? data.code
        : undefined;

    let errorMessage = 'ログイン処理に失敗しました。';

    if (response.status === 422) {
      errorMessage =
        data.errors?.email?.[0] ?? 'ログイン情報が正しくありません。';
    } else if (errorCode === 'email_not_verified') {
      errorMessage = data.message ?? 'メール認証が完了していません。';
    } else if (response.status === 429) {
      errorMessage =
        'ログイン試行回数が多すぎます。しばらくしてから再度お試しください。';
    }

    throw new LoginApiError(errorMessage, errorCode);
  }

  return data;
};
