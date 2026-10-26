import './setup';
import * as api from '../../../api/ticketApi';
import { useTicketStore } from '../../useTicketStore';
import { deferred, state, ticket } from './helpers';
import type { Ticket } from '../../../types/ticket';
import { expect, it, vi } from 'vitest';

it('appends created tickets to their column', async () => {
  useTicketStore.setState({
    tickets: [ticket('1', 4), ticket('2', 90, 'DONE')],
  });
  vi.mocked(api.createTicket).mockResolvedValue(ticket('3', 5));
  await state().addTicket({ projectId: '1', title: 'New' });
  expect(state().tickets.at(-1)).toMatchObject({ id: '3', position: 5 });
  expect(state().isLoading).toBe(false);
});

it('uses the server response for a manual status change', async () => {
  useTicketStore.setState({
    tickets: [ticket('1', 3), ticket('2', 8, 'DONE')],
  });
  const request = deferred<Ticket>();
  vi.mocked(api.updateTicketStatus).mockReturnValue(request.promise);
  const action = state().updateStatus('1', 'DONE');
  expect(state().tickets[0]).toMatchObject({ status: 'TODO', position: 3 });
  request.resolve({ ...ticket('1', 9, 'DONE'), updatedAt: 'server-date' });
  await action;
  expect(state().tickets[0]).toMatchObject({
    position: 9,
    updatedAt: 'server-date',
  });
});

it('applies server-confirmed ticket edits and keeps the current position', async () => {
  useTicketStore.setState({ tickets: [ticket('1', 4)] });
  vi.mocked(api.updateTicket).mockResolvedValue({
    ...ticket('1', 4),
    title: 'Updated',
    priority: 'HIGH',
  });

  await state().updateTicket('1', { title: 'Updated', priority: 'HIGH' });

  expect(api.updateTicket).toHaveBeenCalledWith('1', {
    title: 'Updated',
    priority: 'HIGH',
  });
  expect(state().tickets[0]).toMatchObject({
    title: 'Updated',
    priority: 'HIGH',
    position: 4,
  });
});

it('uses the server position when an edit changes status', async () => {
  useTicketStore.setState({
    tickets: [ticket('1', 4), ticket('2', 8, 'DONE')],
  });
  vi.mocked(api.updateTicket).mockResolvedValue(ticket('1', 9, 'DONE'));

  await state().updateTicket('1', { status: 'DONE' });

  expect(state().tickets[0]).toMatchObject({
    id: '1',
    status: 'DONE',
    position: 9,
  });
});

it('keeps the existing ticket and exposes an edit failure', async () => {
  useTicketStore.setState({ tickets: [ticket('1', 4)] });
  vi.mocked(api.updateTicket).mockRejectedValue(new Error('edit failed'));

  await expect(state().updateTicket('1', { title: 'Updated' })).rejects.toThrow(
    'edit failed',
  );

  expect(state().tickets[0]).toEqual(ticket('1', 4));
  expect(state().error).toBe('edit failed');
});

it('restores failed deletion without discarding a new ticket', async () => {
  useTicketStore.setState({ tickets: [ticket('1', 4)] });
  const request = deferred<void>();
  vi.mocked(api.deleteTicket).mockReturnValue(request.promise);
  const action = state().deleteTicket('1');
  expect(state().tickets).toEqual([]);
  vi.mocked(api.createTicket).mockResolvedValue(ticket('2', 5));
  await state().addTicket({ projectId: '1', title: 'New' });
  request.reject(new Error('DELETE failed'));
  await expect(action).rejects.toThrow('DELETE failed');
  expect(
    state()
      .tickets.map((t) => [t.id, t.position])
      .sort(([a], [b]) => String(a).localeCompare(String(b))),
  ).toEqual([
    ['1', 4],
    ['2', 5],
  ]);
  expect(new Set(state().tickets.map((t) => t.position)).size).toBe(2);
});

it('reserves the original position for failed column moves as well as deletes', async () => {
  useTicketStore.setState({ tickets: [ticket('1')] });
  const request = deferred<Ticket>();
  vi.mocked(api.updateTicketStatus).mockReturnValue(request.promise);
  const move = state().updateStatus('1', 'DONE');
  vi.mocked(api.createTicket).mockResolvedValue(ticket('2', 1));
  await state().addTicket({ projectId: '1', title: 'New' });
  request.reject(new Error('move failed'));
  await move;
  const ordered = [...state().tickets].sort((a, b) => a.position - b.position);
  expect(ordered.map((t) => [t.id, t.position])).toEqual([
    ['1', 0],
    ['2', 1],
  ]);
});

it('keeps state on failed fetch or create and releases loading', async () => {
  useTicketStore.setState({ tickets: [ticket('1', 4)] });
  vi.mocked(api.fetchTickets).mockRejectedValue(new Error('fetch failed'));
  await state().fetchTickets();
  vi.mocked(api.createTicket).mockRejectedValue(new Error('create failed'));
  await expect(
    state().addTicket({ projectId: '1', title: 'New' }),
  ).rejects.toThrow('create failed');
  expect(state().tickets).toEqual([ticket('1', 4)]);
  expect(state().error).toBe('create failed');
  expect(state().isLoading).toBe(false);
});
