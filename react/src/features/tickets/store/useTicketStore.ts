import { create } from 'zustand';
import * as api from '../api/ticketApi';
import type { CreateTicketInput, Ticket, TicketStatus, UpdateTicketInput } from '../types/ticket';

interface TicketState {
  tickets: Ticket[];
  isLoading: boolean;
  error: string | null;
  fetchTickets: () => Promise<void>;
  updateStatus: (id: string, status: TicketStatus) => Promise<void>;
  moveTicket: (
    id: string,
    status: TicketStatus,
    position: number,
    boardVersion: number,
  ) => Promise<number>;
  addTicket: (ticket: CreateTicketInput) => Promise<void>;
  updateTicket: (id: string, input: UpdateTicketInput) => Promise<void>;
  deleteTicket: (id: string) => Promise<void>;
}

export const useTicketStore = create<TicketState>((set, get) => {
  let revision = 0;
  let fetchSequence = 0;
  let loading = 0;
  let creating = 0;
  let refreshNeeded = false;
  const pending = new Map<string, Promise<unknown>>();
  const refreshWhenIdle = async () => {
    if (refreshNeeded && pending.size === 0 && creating === 0) {
      refreshNeeded = false;
      await get().fetchTickets();
    }
  };
  const startLoading = () => {
    loading += 1;
    set({ isLoading: true, error: null });
  };
  const stopLoading = () => {
    loading -= 1;
    set({ isLoading: loading > 0 });
  };
  const fail = (error: unknown) =>
    set({
      error:
        error instanceof Error
          ? error.message
          : '予期しないエラーが発生しました。',
    });

  // Serialize writes to the same ticket; unrelated tickets can still progress.
  const write = <T>(id: string, operation: () => Promise<T>): Promise<T> => {
    const previous = pending.get(id);
    const request = previous ? previous.then(operation) : operation();
    pending.set(id, request);
    return request.finally(() => {
      if (pending.get(id) === request) pending.delete(id);
      return refreshWhenIdle();
    });
  };

  return {
    tickets: [],
    isLoading: false,
    error: null,
    fetchTickets: async () => {
      const sequence = ++fetchSequence;
      const startedAt = revision;
      startLoading();
      try {
        const incoming = await api.fetchTickets();
        // An older GET must not overwrite a write or a newer GET.
        if (
          sequence === fetchSequence &&
          startedAt === revision &&
          pending.size === 0 &&
          creating === 0
        ) {
          set({ tickets: incoming });
          refreshNeeded = false;
        } else if (sequence === fetchSequence) {
          refreshNeeded = true;
        }
      } catch (error) {
        if (sequence === fetchSequence && startedAt === revision) fail(error);
      } finally {
        stopLoading();
        await refreshWhenIdle();
      }
    },
    updateStatus: (id, status) =>
      write(id, async () => {
        const before = get().tickets.find((ticket) => ticket.id === id);
        if (!before || before.status === status) return;
        revision += 1;
        set({ error: null });
        try {
          const updated = await api.updateTicketStatus(id, status);
          refreshNeeded = true;
          set((state) => ({
            tickets: state.tickets.map((ticket) =>
              ticket.id === id ? updated : ticket,
            ),
          }));
        } catch (error) {
          // Restore only this ticket, retaining concurrent changes elsewhere.
          set((state) => ({
            tickets: state.tickets.map((ticket) =>
              ticket.id === id ? before : ticket,
            ),
          }));
          fail(error);
        } finally {
          revision += 1;
        }
      }),
    moveTicket: (id, status, position, boardVersion) =>
      write(id, async () => {
        const before = get().tickets;
        const moving = before.find((ticket) => ticket.id === id);
        if (!moving) return boardVersion;

        revision += 1;
        set({ error: null });
        const without = before.filter((ticket) => ticket.id !== id);
        const target = without
          .filter((ticket) => ticket.projectId === moving.projectId && ticket.status === status)
          .sort((a, b) => a.position - b.position);
        const insertAt = Math.min(position, target.length);
        target.splice(insertAt, 0, { ...moving, status });
        const positions = new Map(target.map((ticket, index) => [ticket.id, index]));
        set({
          tickets: without.map((ticket) =>
            positions.has(ticket.id)
              ? { ...ticket, position: positions.get(ticket.id)! }
              : ticket,
          ).concat({ ...moving, status, position: insertAt }),
        });

        try {
          const result = await api.moveTicket(id, status, position, boardVersion);
          refreshNeeded = true;
          return result.boardVersion;
        } catch (error) {
          set({ tickets: before });
          fail(error);
          if (error instanceof api.TicketApiError && error.status === 409) {
            refreshNeeded = true;
          }
          throw error;
        } finally {
          revision += 1;
        }
      }),
    addTicket: async (input) => {
      revision += 1;
      creating += 1;
      startLoading();
      try {
        const ticket = await api.createTicket(input);
        refreshNeeded = true;
        set((state) => ({
          tickets: [...state.tickets, ticket],
        }));
      } catch (error) {
        fail(error);
        throw error;
      } finally {
        revision += 1;
        creating -= 1;
        stopLoading();
        await refreshWhenIdle();
      }
    },
    updateTicket: (id, input) =>
      write(id, async () => {
        const before = get().tickets.find((ticket) => ticket.id === id);
        if (!before) return;
        revision += 1;
        set({ error: null });
        try {
          const updated = await api.updateTicket(id, input);
          if (input.status !== undefined) refreshNeeded = true;
          set((state) => ({
            tickets: state.tickets.map((ticket) =>
              ticket.id === id ? updated : ticket,
            ),
          }));
        } catch (error) {
          fail(error);
          throw error;
        } finally {
          revision += 1;
        }
      }),
    deleteTicket: (id) =>
      write(id, async () => {
        const before = get().tickets.find((ticket) => ticket.id === id);
        if (!before) return;
        revision += 1;
        set((state) => ({
          error: null,
          tickets: state.tickets.filter((ticket) => ticket.id !== id),
        }));
        try {
          await api.deleteTicket(id);
          refreshNeeded = true;
        } catch (error) {
          set((state) => ({ tickets: [...state.tickets, before] }));
          fail(error);
        } finally {
          revision += 1;
        }
      }),
  };
});
