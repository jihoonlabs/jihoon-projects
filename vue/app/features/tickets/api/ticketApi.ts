import { useProtectedApi } from '~/features/auth/api/protectedRequest';
import { ApiError } from '~/shared/api/apiClient';

import type { Ticket, TicketResponse } from '../types/ticket';
import {
  TICKET_ERROR_MESSAGE,
  TicketApiError,
  translateFailure,
} from './apiErrors';
import { toTicket } from './ticketMapper';

const toTicketError = (error: unknown): Error => {
  if (error instanceof ApiError) {
    return new TicketApiError(
      `${TICKET_ERROR_MESSAGE} (${error.status})`,
      error.status,
      error.code,
    );
  }

  return new TicketApiError(TICKET_ERROR_MESSAGE);
};

export function useTicketApi() {
  const api = useProtectedApi();

  return {
    /**
     * アクセスできるプロジェクトのチケットを、API が返す順のまま取得する
     */
    async fetchTickets(signal?: AbortSignal): Promise<Ticket[]> {
      const body = await translateFailure(
        api.getJson<{ data?: TicketResponse[] | null }>('/api/tickets', {
          signal,
        }),
        toTicketError,
      );

      if (!body || !Array.isArray(body.data)) {
        throw new TicketApiError('チケット一覧の応答形式が不正です。');
      }

      return body.data.map(toTicket);
    },
    /**
     * 1 件の最新状態を取得する（詳細モーダルを開くときと、競合のあとに使う）。
     */
    async fetchTicket(id: string, signal?: AbortSignal): Promise<Ticket> {
      const body = await translateFailure(
        api.getJson<{ data?: TicketResponse | null }>(
          `/api/tickets/${encodeURIComponent(id)}`,
          { signal },
        ),
        toTicketError,
      );

      if (!body || !body.data) {
        throw new TicketApiError('チケットの応答形式が不正です。');
      }

      return toTicket(body.data);
    },
  };
}
