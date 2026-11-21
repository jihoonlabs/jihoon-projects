import { isTicketApiError } from '../api/apiErrors';

/**
 * 詳細・再取得の失敗を、画面に出せる文言にする（内部の詳細は出さない）
 */
export function detailError(error: unknown): string {
  if (isTicketApiError(error)) {
    if (error.status === 404) {
      return 'このチケットは削除されたか、存在しません。';
    }

    if (error.status === 403 || error.status === 401) {
      return 'このチケットへのアクセス権限がありません。';
    }
  }

  return '最新のチケット情報を取得できませんでした。再試行してください。';
}
