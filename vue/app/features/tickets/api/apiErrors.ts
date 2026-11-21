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

/**
 * 他の人が先に更新したため保存できなかった（Laravel の ticket_conflict / 409）
 */
export class TicketConflictError extends TicketApiError {
  constructor() {
    super(
      'このチケットは他の人が更新しています。最新の内容を読み込んでから、もう一度編集してください。',
      409,
      'ticket_conflict',
    );
    this.name = 'TicketConflictError';
  }
}

/**
 * チケット API の失敗かを、名前で判定する。
 * クラスの同一性（instanceof）に頼らないのは、同じモジュールが別の経路で二重に読み込まれる
 * 環境（テスト）でも、store が投げた失敗を画面側で見分けられるようにするため。
 */
export function isTicketApiError(error: unknown): error is TicketApiError {
  return (
    error instanceof Error &&
    (error.name === 'TicketApiError' || error.name === 'TicketConflictError')
  );
}
