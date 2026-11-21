import { isTicketApiError } from '../api/apiErrors';
import { WRITE_MESSAGE } from '../constants/ticketMessages';

/**
 * 詳細・再取得の失敗を、画面に出せる文言にする（内部の詳細は出さない）
 */
export function detailError(error: unknown): string {
  if (isTicketApiError(error)) {
    if (error.status === 404) {
      return WRITE_MESSAGE.notFound;
    }

    if (error.status === 403 || error.status === 401) {
      return WRITE_MESSAGE.forbidden;
    }
  }

  return WRITE_MESSAGE.reloadFailed;
}
