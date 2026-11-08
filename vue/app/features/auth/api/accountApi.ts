import { ApiError, useApiClient, type ApiClient } from '~/shared/api/apiClient';

import type { MessageResponse, PasswordReset, Registration } from '../types';

/**
 * 画面にそのまま表示できる、アカウント操作の失敗
 */
export class AccountError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AccountError';
  }
}

interface FailureMessages {
  /** 422 のとき、この順で最初に見つかった項目別メッセージを使う */
  fields: string[];
  invalid: string;
  tooMany: string;
  fallback: string;
  /** 422 で項目別メッセージがないとき、サーバーの文言を使うか */
  useServerMessage?: boolean;
}

const isAbortError = (error: unknown) =>
  error instanceof Error && error.name === 'AbortError';

// Next.js 版と同じ文言で、Laravel の失敗応答を利用者向けのメッセージに変換する
const toAccountError = (
  error: unknown,
  messages: FailureMessages,
): AccountError => {
  if (!(error instanceof ApiError)) {
    return new AccountError(messages.fallback);
  }

  if (error.status === 422) {
    const fieldMessage = messages.fields
      .map((field) => error.fieldErrors[field]?.[0])
      .find((message): message is string => Boolean(message));
    const serverMessage = messages.useServerMessage
      ? error.serverMessage
      : undefined;

    return new AccountError(fieldMessage ?? serverMessage ?? messages.invalid);
  }

  if (error.status === 429) {
    return new AccountError(messages.tooMany);
  }

  return new AccountError(messages.fallback);
};

export function createAccountApi(client: ApiClient) {
  const send = async (
    path: string,
    body: Record<string, string>,
    messages: FailureMessages,
    signal?: AbortSignal,
  ): Promise<MessageResponse> => {
    try {
      return await client.sendJson<MessageResponse>('POST', path, body, {
        signal,
      });
    } catch (error) {
      if (isAbortError(error)) {
        throw error;
      }

      throw toAccountError(error, messages);
    }
  };

  return {
    register(registration: Registration) {
      return send(
        '/api/auth/register',
        {
          name: registration.name.trim(),
          email: registration.email.trim(),
          password: registration.password,
          password_confirmation: registration.passwordConfirmation,
        },
        {
          fields: ['email', 'password', 'name'],
          invalid: '入力内容を確認してください。',
          tooMany:
            '登録試行回数が多すぎます。しばらくしてから再度お試しください。',
          fallback: '会員登録処理に失敗しました。',
        },
      );
    },

    requestPasswordReset(email: string) {
      return send(
        '/api/auth/forgot-password',
        { email: email.trim() },
        {
          fields: ['email'],
          invalid: 'メールアドレスを確認してください。',
          tooMany:
            'パスワード再設定メールの送信回数が多すぎます。しばらくしてから再度お試しください。',
          fallback: 'パスワード再設定メールの送信に失敗しました。',
        },
      );
    },

    resetPassword(reset: PasswordReset) {
      return send(
        '/api/auth/reset-password',
        {
          email: reset.email.trim(),
          token: reset.token,
          password: reset.password,
          password_confirmation: reset.passwordConfirmation,
        },
        {
          fields: ['password', 'password_confirmation', 'email', 'token'],
          invalid: 'メールアドレスまたは再設定トークンを確認してください。',
          tooMany:
            'パスワード再設定の試行回数が多すぎます。しばらくしてから再度お試しください。',
          fallback: 'パスワードの再設定に失敗しました。',
          useServerMessage: true,
        },
      );
    },

    resendVerificationEmail(email: string, signal?: AbortSignal) {
      return send(
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
    },
  };
}

export type AccountApi = ReturnType<typeof createAccountApi>;

export function useAccountApi(): AccountApi {
  return createAccountApi(useApiClient());
}
