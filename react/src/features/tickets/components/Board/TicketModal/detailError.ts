import { TicketApiError } from '@/features/tickets/api/ticketApi';

export function detailError(error: unknown): string {
  if (error instanceof TicketApiError) {
    if (error.status === 404)
      return 'このチケットは削除されたか、存在しません。';
    if (error.status === 403 || error.status === 401)
      return 'このチケットへのアクセス権限がありません。';
  }
  return '最新のチケット情報を取得できませんでした。再試行してください。';
}
