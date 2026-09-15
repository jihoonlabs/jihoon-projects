import { fetchWithCsrf } from '@/shared/api/fetchWithCsrf';

import type {
  RegisterRequest,
  RegisterResponse,
} from '@/features/auth/types/auth';

export const registerApi = async (
  params: RegisterRequest,
): Promise<RegisterResponse> => {
  const response = await fetchWithCsrf('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      name: params.name.trim(),
      email: params.email.trim(),
      password: params.password,
      password_confirmation: params.passwordConfirmation,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    const errorMessage =
      response.status === 422
        ? (data.errors?.email?.[0] ??
          data.errors?.password?.[0] ??
          data.errors?.name?.[0] ??
          '入力内容を確認してください。')
        : response.status === 429
          ? '登録試行回数が多すぎます。しばらくしてから再度お試しください。'
          : '会員登録処理に失敗しました。';

    throw new Error(errorMessage);
  }

  return data;
};
