import { cancelSessionRestore } from './me';
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
  // 遅い初期GETのSet-Cookieが、新しい認証セッションを上書きしないよう中断する。
  cancelSessionRestore();
  let response: Response;
  try {
    response = await fetchWithCsrf('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  } catch (error) {
    throw new LoginApiError(
      error instanceof TypeError
        ? 'ネットワークに接続できません。接続を確認して再度お試しください。'
        : error instanceof Error
          ? error.message
          : 'ログイン処理に失敗しました。',
    );
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const errorCode =
      response.status === 403 && data?.code === 'email_not_verified'
        ? data?.code
        : undefined;

    let errorMessage = 'ログイン処理に失敗しました。';

    if (response.status === 422) {
      errorMessage =
        data?.errors?.email?.[0] ?? 'ログイン情報が正しくありません。';
    } else if (errorCode === 'email_not_verified') {
      errorMessage = data?.message ?? 'メール認証が完了していません。';
    } else if (response.status === 429) {
      errorMessage =
        'ログイン試行回数が多すぎます。しばらくしてから再度お試しください。';
    }

    throw new LoginApiError(errorMessage, errorCode);
  }

  // 不正な成功応答を認証済み状態として採用しない。
  const user = data?.user;
  if (
    !user ||
    !Number.isSafeInteger(user.id) ||
    user.id <= 0 ||
    typeof user.name !== 'string' ||
    !(user.email === null || typeof user.email === 'string') ||
    user.status !== 'active' ||
    !['user', 'admin'].includes(user.role) ||
    typeof user.createdAt !== 'string'
  ) {
    throw new LoginApiError(
      'ログインAPIの応答形式が不正です。再度お試しください。',
    );
  }
  return data;
};
