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
    let errorMessage = '会員登録処理に失敗しました。';

    if (response.status === 422) {
      errorMessage =
        data.errors?.email?.[0] ??
        data.errors?.password?.[0] ??
        data.errors?.name?.[0] ??
        '入力内容を確認してください。';
    } else if (response.status === 429) {
      errorMessage =
        '登録試行回数が多すぎます。しばらくしてから再度お試しください。';
    }

    throw new Error(errorMessage);
  }

  return data;
};
