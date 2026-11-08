import { ApiError, useApiClient, type ApiClient } from '~/shared/api/apiClient';

import type { LoginCredentials, LoginResponse, User } from '../types';

export type LoginFailureReason = 'email_not_verified';

/**
 * 画面にそのまま表示できるログイン失敗。メール未認証のときは reason で区別する。
 */
export class LoginError extends Error {
  constructor(
    message: string,
    readonly reason?: LoginFailureReason,
  ) {
    super(message);
    this.name = 'LoginError';
  }
}

const isAbortError = (error: unknown) =>
  error instanceof Error && error.name === 'AbortError';

// Next.js 版と同じ文言で、Laravel の失敗応答を利用者向けのメッセージに変換する
const toLoginError = (error: unknown): LoginError => {
  if (!(error instanceof ApiError)) {
    return new LoginError('ログイン処理に失敗しました。');
  }

  if (error.status === 422) {
    return new LoginError(
      error.fieldErrors.email?.[0] ?? 'ログイン情報が正しくありません。',
    );
  }

  if (error.status === 403 && error.code === 'email_not_verified') {
    return new LoginError(
      error.serverMessage ?? 'メール認証が完了していません。',
      'email_not_verified',
    );
  }

  if (error.status === 429) {
    return new LoginError(
      'ログイン試行回数が多すぎます。しばらくしてから再度お試しください。',
    );
  }

  return new LoginError('ログイン処理に失敗しました。');
};

export function createAuthApi(client: ApiClient) {
  return {
    fetchCurrentUser(signal?: AbortSignal): Promise<User> {
      return client.getJson<User>('/api/auth/me', { signal });
    },

    async login(credentials: LoginCredentials): Promise<User> {
      try {
        const response = await client.sendJson<LoginResponse>(
          'POST',
          '/api/auth/login',
          credentials,
        );

        return response.user;
      } catch (error) {
        if (isAbortError(error)) {
          throw error;
        }

        throw toLoginError(error);
      }
    },

    async logout(): Promise<void> {
      try {
        await client.sendJson('POST', '/api/auth/logout');
      } catch {
        throw new Error('ログアウトに失敗しました。');
      }
    },
  };
}

export type AuthApi = ReturnType<typeof createAuthApi>;

export function useAuthApi(): AuthApi {
  return createAuthApi(useApiClient());
}
