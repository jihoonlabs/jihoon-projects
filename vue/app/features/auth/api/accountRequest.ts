import { ApiError, type ApiClient } from '~/shared/api/apiClient';
import { isAbortError } from '~/shared/api/isAbortError';

import type { MessageResponse } from '../types/auth';

/**
 * 画面にそのまま表示できる、アカウント操作の失敗
 */
export class AccountError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AccountError';
  }
}

export interface FailureMessages {
  /** 422 のとき、この順で最初に見つかった項目別メッセージを使う */
  fields: string[];
  invalid: string;
  tooMany: string;
  fallback: string;
  /** 422 で項目別メッセージがないとき、サーバーの文言を使うか */
  useServerMessage?: boolean;
}

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

/**
 * アカウント操作の要求を送り、失敗を画面に表示できる AccountError に変換する。中断はそのまま伝える。
 */
export async function sendAccountRequest(
  client: ApiClient,
  path: string,
  body: Record<string, string>,
  messages: FailureMessages,
  signal?: AbortSignal,
): Promise<MessageResponse> {
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
}
