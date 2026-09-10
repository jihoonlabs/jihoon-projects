import { fetchWithCsrf } from '@/shared/api/fetchWithCsrf';

import type {
  AuthResponse,
  LoginRequest,
} from '@/features/auth/types/auth';

export const loginApi = async (
  params: LoginRequest,
): Promise<AuthResponse> => {
  const response = await fetchWithCsrf('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(params),
  });

  const data = await response.json();

  if (!response.ok) {
    const errorMessage =
      response.status === 422
        ? (data.errors?.email?.[0] ??
          'ログイン情報が正しくありません。')
        : 'ログイン処理に失敗しました。';

    throw new Error(errorMessage);
  }

  return data;
};