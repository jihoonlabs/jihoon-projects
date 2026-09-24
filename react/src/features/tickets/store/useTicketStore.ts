import { create } from 'zustand';
import type { Ticket, TicketStatus } from '../types/ticket';

interface TicketState {
  tickets: Ticket[];
  isLoading: boolean;
  error: string | null;
  fetchTickets: () => Promise<void>;
  updateStatus: (id: string, status: TicketStatus) => Promise<void>;
  addTicket: (ticket: Omit<Ticket, 'id' | 'issueKey' | 'position' | 'createdAt' | 'updatedAt'>) => void;
  deleteTicket: (id: string) => void;
}

export const useTicketStore = create<TicketState>((set, get) => ({
  tickets: [],
  isLoading: false,
  error: null,

  // Laravel APIからチケット一覧を取得
  fetchTickets: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch('http://127.0.0.1:8000/api/tickets', {
        headers: {
          'Accept': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('チケットデータの取得に失敗しました。');
      }

      const data = await response.json();
      const ticketList = Array.isArray(data) ? data : data.data || [];

      set({ tickets: ticketList, isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  // ステータス更新 (Optimistic Update + API連携)
  updateStatus: async (id, status) => {
    const previousTickets = get().tickets;
set((state) => ({
      tickets: state.tickets.map((t) =>
        String(t.id) === String(id) ? { ...t, status } : t
      ),
    }));

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/tickets/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ status }),
      });

      if (!response.ok) {
        throw new Error('ステータスの更新に失敗しました。');
      }
    } catch (err) {
      // エラー発生時は元の状態にロールバック
      set({ tickets: previousTickets });
      console.error('Failed to update ticket status:', err);
    }
  },

  addTicket: (ticketData) =>
    set((state) => ({
      tickets: [
        ...state.tickets,
        {
          ...ticketData,
          id: String(Date.now()),
          issueKey: `KAN-${state.tickets.length + 101}`,
          position: state.tickets.length,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      ],
    })),

  deleteTicket: (id) =>
    set((state) => ({
      tickets: state.tickets.filter((ticket) => ticket.id !== id),
    })),
}));