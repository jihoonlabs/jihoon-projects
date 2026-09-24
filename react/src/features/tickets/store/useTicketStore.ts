import { fetchWithCsrf } from '@/shared/api/fetchWithCsrf';
import { create } from 'zustand';
import type { Ticket, TicketStatus } from '../types/ticket';

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface TicketState {
  tickets: Ticket[];
  isLoading: boolean;
  error: string | null;
  fetchTickets: () => Promise<void>;
  updateStatus: (id: string, status: TicketStatus) => Promise<void>;
  addTicket: (
    ticket: Omit<
      Ticket,
      'id' | 'issueKey' | 'position' | 'createdAt' | 'updatedAt'
    >,
  ) => Promise<void>;
  deleteTicket: (id: string) => Promise<void>;
}

export const useTicketStore = create<TicketState>((set, get) => ({
  tickets: [],
  isLoading: false,
  error: null,

  // Laravel APIからチケット一覧を取得
  fetchTickets: async () => {
    set({ isLoading: true, error: null });

    try {
      const response = await fetch(`${API_URL}/api/tickets`, {
        credentials: 'include',
        headers: {
          Accept: 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('チケットデータの取得に失敗しました。');
      }

      const data = await response.json();
      const ticketList = Array.isArray(data) ? data : data.data || [];

      set({ tickets: ticketList, isLoading: false });
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : '予期しないエラーが発生しました。';

      set({ error: message, isLoading: false });
    }
  },

  // ステータス更新 (Optimistic Update + API連携)
  updateStatus: async (id, status) => {
    const previousTickets = get().tickets;

    set((state) => ({
      tickets: state.tickets.map((ticket) =>
        String(ticket.id) === String(id) ? { ...ticket, status } : ticket,
      ),
    }));

    try {
      const response = await fetchWithCsrf(`/api/tickets/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      });

      if (!response.ok) {
        throw new Error('ステータスの更新に失敗しました。');
      }
    } catch (err: unknown) {
      // エラー発生時は元の状態にロールバック
      set({ tickets: previousTickets });
      console.error('Failed to update ticket status:', err);
    }
  },

  addTicket: async (ticketData) => {
    set({ isLoading: true, error: null });

    try {
      const response = await fetchWithCsrf('/api/tickets', {
        method: 'POST',
        body: JSON.stringify({
          ...ticketData,
          status: ticketData.status || 'TODO',
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create ticket');
      }

      const newTicket = await response.json();

      set((state) => ({
        tickets: [...state.tickets, newTicket],
        isLoading: false,
      }));
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : '予期しないエラーが発生しました。';

      set({ error: message, isLoading: false });
      console.error('Failed to add ticket:', err);
    }
  },

  deleteTicket: async (id) => {
    const previousTickets = get().tickets;

    set((state) => ({
      tickets: state.tickets.filter(
        (ticket) => String(ticket.id) !== String(id),
      ),
    }));

    try {
      const response = await fetchWithCsrf(`/api/tickets/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('チケットの削除に失敗しました。');
      }
    } catch (err: unknown) {
      set({ tickets: previousTickets });
      console.error('Failed to delete ticket:', err);
    }
  },
}));