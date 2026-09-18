import { create } from 'zustand';

export type TicketStatus = 'TODO' | 'IN_PROGRESS' | 'DONE';
export type TicketPriority = 'LOW' | 'MEDIUM' | 'HIGH';

export interface Ticket {
  id: string;
  title: string;
  description: string;
  status: TicketStatus;
  priority: TicketPriority;
  assignee: string;
  createdAt: string;
}

interface TicketState {
  tickets: Ticket[];
  addTicket: (ticket: Omit<Ticket, 'id' | 'createdAt'>) => void;
  updateStatus: (id: string, status: TicketStatus) => void;
  deleteTicket: (id: string) => void;
}

// 初期モックデータ (초기 가짜 데이터)
const initialTickets: Ticket[] = [
  {
    id: 'TICK-1',
    title: 'Next.js 15 App Router 環境構築',
    description: 'Route GroupおよびMiddlewareを用いた認証構造の作成',
    status: 'DONE',
    priority: 'HIGH',
    assignee: 'P.jh',
    createdAt: '2026-09-01',
  },
  {
    id: 'TICK-2',
    title: 'Laravel API 連動準備',
    description: 'HttpOnly CookieベースのJWT認証APIとの結合テスト',
    status: 'IN_PROGRESS',
    priority: 'HIGH',
    assignee: 'P.jh',
    createdAt: '2026-09-01',
  },
  {
    id: 'TICK-3',
    title: 'S3 画像アップロード機能の実装',
    description: 'AWS S3 Presigned URLを活用した非同期アップロード機能',
    status: 'TODO',
    priority: 'MEDIUM',
    assignee: 'P.jh',
    createdAt: '2026-09-01',
  },
];

export const useTicketStore = create<TicketState>((set) => ({
  tickets: initialTickets,

  addTicket: (ticketData) =>
    set((state) => ({
      tickets: [
        ...state.tickets,
        {
          ...ticketData,
          id: `TICK-${state.tickets.length + 1}`,
          createdAt: new Date().toISOString().split('T')[0],
        },
      ],
    })),

  updateStatus: (id, status) =>
    set((state) => ({
      tickets: state.tickets.map((ticket) =>
        ticket.id === id ? { ...ticket, status } : ticket,
      ),
    })),

  deleteTicket: (id) =>
    set((state) => ({
      tickets: state.tickets.filter((ticket) => ticket.id !== id),
    })),
}));
