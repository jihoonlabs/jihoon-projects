import { isTicketApiError } from '../api/apiErrors';

/**
 * 保存・削除の失敗として画面に出す文言。
 * API が返した文言や内部の例外メッセージは使わず、定数の文言に状態コードだけを添える
 * （文言を変えるときは constants/ticketMessages.ts だけを直せばよい）。
 */
export function writeFailureMessage(error: unknown, message: string): string {
  if (isTicketApiError(error) && error.status !== undefined) {
    return `${message} (${error.status})`;
  }

  return message;
}
