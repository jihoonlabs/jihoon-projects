import { fetchWithCsrf } from '@/shared/api/fetchWithCsrf';
import { create } from 'zustand';
import type { Ticket, TicketStatus } from '../types/ticket';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

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
  updateTicket: (
    id: string,
    ticketData: Partial<
      Omit<Ticket, 'id' | 'issueKey' | 'createdAt' | 'updatedAt'>
    >,
  ) => Promise<void>;
  deleteTicket: (id: string) => Promise<void>;
}

export const useTicketStore = create<TicketState>((set, get) => ({
  tickets: [],
  isLoading: false,
  error: null,

  // チケット一覧取得 (Laravel TicketResource Standard: { data: Ticket[] })
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

      const result = await response.json();
      const ticketList = Array.isArray(result) ? result : result.data || [];

      set({ tickets: ticketList, isLoading: false });
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : '予期しないエラーが発生しました。';

      set({ error: message, isLoading: false });
    }
  },

  // ステータス更新 (Optimistic Update + API連携)
  updateStatus: async (id, status) => {
    const previousTickets = get().tickets;

    set((state) => ({
      tickets: state.tickets.map((ticket) =>
        ticket.id === id ? { ...ticket, status } : ticket,
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

  // チケット追加 (Laravel TicketResource Standard: { data: Ticket })
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
        throw new Error('チケットの作成に失敗しました。');
      }

      const result = await response.json();
      const newTicket: Ticket = result.data ?? result; // TicketResource data 抽出

      set((state) => ({
        tickets: [...state.tickets, newTicket],
        isLoading: false,
      }));
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : '予期しないエラーが発生しました。';

      set({ error: message, isLoading: false });
      console.error('Failed to add ticket:', err);
    }
  },

  // チケット更新 (추가된 기능: Optimistic Update + API連携)
  updateTicket: async (id, ticketData) => {
    const previousTickets = get().tickets;

    // 1. UI 즉시 반영 (Optimistic Update)
    set((state) => ({
      tickets: state.tickets.map((ticket) =>
        ticket.id === id ? { ...ticket, ...ticketData } : ticket,
      ),
    }));

    try {
      const response = await fetchWithCsrf(`/api/tickets/${id}`, {
        method: 'PUT',
        body: JSON.stringify(ticketData),
      });

      if (!response.ok) {
        throw new Error('チケットの更新に失敗しました。');
      }

      const result = await response.json();
      const updatedTicket: Ticket = result.data ?? result;

      // API 응답 데이터로 최종 상태 동기화
      set((state) => ({
        tickets: state.tickets.map((t) => (t.id === id ? updatedTicket : t)),
      }));
    } catch (err: unknown) {
      // 에러 시 기존 상태로 롤백
      set({ tickets: previousTickets });
      console.error('Failed to update ticket:', err);
    }
  },

  // チケット削除
  deleteTicket: async (id) => {
    const previousTickets = get().tickets;

    set((state) => ({
      tickets: state.tickets.filter((ticket) => ticket.id !== id),
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