import { isAbortError } from '~/shared/api/isAbortError';

export const TICKET_ERROR_MESSAGE = 'チケット操作に失敗しました。';
export const PROJECT_ERROR_MESSAGE = 'プロジェクト操作に失敗しました。';

/**
 * 画面にそのまま表示できるチケット API の失敗
 */
export class TicketApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
    readonly code?: string,
  ) {
    super(message);
    this.name = 'TicketApiError';
  }
}

/**
 * 画面にそのまま表示できるプロジェクト API の失敗
 */
export class ProjectApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = 'ProjectApiError';
  }
}

/**
 * 要求の失敗を表示用の失敗に変える。
 * 中断（ログイン状態の変化・画面離脱）は失敗ではないため、そのまま伝える。
 */
export async function translateFailure<T>(
  request: Promise<T>,
  toError: (error: unknown) => Error,
): Promise<T> {
  try {
    return await request;
  } catch (error) {
    if (isAbortError(error)) {
      throw error;
    }

    throw toError(error);
  }
}
