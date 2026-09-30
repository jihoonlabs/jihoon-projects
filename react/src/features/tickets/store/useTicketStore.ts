import { create } from 'zustand';
import * as api from '../api/ticketApi';
import type { CreateTicketInput, Ticket, TicketStatus, UpdateTicketInput } from '../types/ticket';

interface TicketState {
  tickets: Ticket[];
  isLoading: boolean;
  error: string | null;
  fetchTickets: () => Promise<void>;
  updateStatus: (id: string, status: TicketStatus) => Promise<void>;
  addTicket: (ticket: CreateTicketInput) => Promise<void>;
  updateTicket: (id: string, input: UpdateTicketInput) => Promise<void>;
  deleteTicket: (id: string) => Promise<void>;
}

function endPosition(tickets: Ticket[], status: TicketStatus): number {
  return tickets.reduce(
    (end, ticket) =>
      ticket.status === status ? Math.max(end, ticket.position + 1) : end,
    0,
  );
}

// Preserve local order on refresh; new tickets or remote column moves go last.
function mergeTickets(incoming: Ticket[], current: Ticket[]): Ticket[] {
  const existing = new Map(current.map((ticket) => [ticket.id, ticket]));
  const retained = incoming.flatMap((ticket) => {
    const old = existing.get(ticket.id);
    return old && old.status === ticket.status
      ? [{ ...ticket, position: old.position }]
      : [];
  });
  return incoming.map((ticket) => {
    const old = existing.get(ticket.id);
    if (old && old.status === ticket.status)
      return { ...ticket, position: old.position };
    const next = { ...ticket, position: endPosition(retained, ticket.status) };
    retained.push(next);
    return next;
  });
}

export const useTicketStore = create<TicketState>((set, get) => {
  let revision = 0;
  let fetchSequence = 0;
  let loading = 0;
  let creating = 0;
  let refreshNeeded = false;
  const pending = new Map<string, Promise<void>>();
  // Reserve rollback positions while an optimistic move/delete is in flight.
  const reserved = new Map<string, Ticket>();
  const nextPosition = (status: TicketStatus) =>
    endPosition([...get().tickets, ...reserved.values()], status);
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
  const write = (id: string, operation: () => Promise<void>): Promise<void> => {
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
          set({ tickets: mergeTickets(incoming, get().tickets) });
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
        reserved.set(id, before);
        const position = nextPosition(status);
        set((state) => ({
          error: null,
          tickets: state.tickets.map((ticket) =>
            ticket.id === id ? { ...ticket, status, position } : ticket,
          ),
        }));
        try {
          const updated = await api.updateTicketStatus(id, status);
          set((state) => ({
            tickets: state.tickets.map((ticket) =>
              ticket.id === id
                ? { ...updated, position: ticket.position }
                : ticket,
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
          reserved.delete(id);
        }
      }),
    addTicket: async (input) => {
      revision += 1;
      creating += 1;
      startLoading();
      try {
        const ticket = await api.createTicket(input);
        set((state) => ({
          tickets: [
            ...state.tickets,
            { ...ticket, position: nextPosition(ticket.status) },
          ],
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
          set((state) => ({
            tickets: state.tickets.map((ticket) =>
              ticket.id === id
                ? { ...updated, position: ticket.status === updated.status ? ticket.position : nextPosition(updated.status) }
                : ticket,
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
        reserved.set(id, before);
        set((state) => ({
          error: null,
          tickets: state.tickets.filter((ticket) => ticket.id !== id),
        }));
        try {
          await api.deleteTicket(id);
        } catch (error) {
          set((state) => ({ tickets: [...state.tickets, before] }));
          fail(error);
        } finally {
          revision += 1;
          reserved.delete(id);
        }
      }),
  };
});
