import './setup';
import * as api from '../../../api/ticketApi';
import { useTicketStore } from '../../useTicketStore';
import { deferred, state, ticket } from './helpers';
import type { Ticket } from '../../../types/ticket';
import { expect, it, vi } from 'vitest';

it('revalidates discarded GETs after a write and includes unrelated server tickets', async () => {
  useTicketStore.setState({ tickets: [ticket('1')] });
  const request = deferred<Ticket>();
  vi.mocked(api.updateTicketStatus).mockReturnValue(request.promise);
  vi.mocked(api.fetchTickets).mockResolvedValue([
    ticket('1', 0, 'DONE'),
    ticket('new'),
  ]);
  const write = state().updateStatus('1', 'DONE');
  await state().fetchTickets();
  request.resolve(ticket('1', 0, 'DONE'));
  await write;
  expect(api.fetchTickets).toHaveBeenCalledTimes(2);
  expect(state().tickets.map((t) => t.id)).toEqual(['1', 'new']);
  expect(state().tickets[0].status).toBe('DONE');
});

it('does not duplicate a ticket when GET sees an in-flight creation', async () => {
  useTicketStore.setState({ tickets: [ticket('1')] });
  const request = deferred<Ticket>();
  vi.mocked(api.createTicket).mockReturnValue(request.promise);
  const create = state().addTicket({ projectId: '1', title: 'New' });
  vi.mocked(api.fetchTickets).mockResolvedValue([ticket('1'), ticket('2')]);
  await state().fetchTickets();
  request.resolve(ticket('2'));
  await create;
  expect(state().tickets.map((t) => t.id)).toEqual(['1', '2']);
});

it('ignores stale GET responses that overlap a mutation', async () => {
  useTicketStore.setState({ tickets: [ticket('1')] });
  const request = deferred<Ticket[]>();
  vi.mocked(api.fetchTickets)
    .mockReturnValueOnce(request.promise)
    .mockResolvedValue([ticket('1', 0, 'DONE'), ticket('new')]);
  const fetch = state().fetchTickets();
  vi.mocked(api.updateTicketStatus).mockResolvedValue(ticket('1', 0, 'DONE'));
  await state().updateStatus('1', 'DONE');
  request.resolve([ticket('1')]);
  await fetch;
  expect(state().tickets[0].status).toBe('DONE');
  expect(state().tickets.map((t) => t.id)).toEqual(['1', 'new']);
  expect(api.fetchTickets).toHaveBeenCalledTimes(2);
});

it('reports failed revalidation without retrying indefinitely', async () => {
  useTicketStore.setState({ tickets: [ticket('1')] });
  const request = deferred<Ticket>();
  vi.mocked(api.updateTicketStatus).mockReturnValue(request.promise);
  vi.mocked(api.fetchTickets)
    .mockResolvedValueOnce([ticket('1')])
    .mockRejectedValueOnce(new Error('refresh failed'));
  const write = state().updateStatus('1', 'DONE');
  await state().fetchTickets();
  request.resolve(ticket('1', 0, 'DONE'));
  await write;
  expect(api.fetchTickets).toHaveBeenCalledTimes(2);
  expect(state().tickets[0].status).toBe('DONE');
  expect(state().error).toBe('refresh failed');
  expect(state().isLoading).toBe(false);
});

it('waits for queued writes before revalidating once', async () => {
  useTicketStore.setState({ tickets: [ticket('1')] });
  const first = deferred<Ticket>();
  const second = deferred<Ticket>();
  vi.mocked(api.updateTicketStatus)
    .mockReturnValueOnce(first.promise)
    .mockReturnValueOnce(second.promise);
  vi.mocked(api.fetchTickets)
    .mockResolvedValueOnce([ticket('1')])
    .mockResolvedValue([ticket('1', 0, 'IN_REVIEW'), ticket('new')]);
  const a = state().updateStatus('1', 'DONE');
  const b = state().updateStatus('1', 'IN_REVIEW');
  await state().fetchTickets();
  first.resolve(ticket('1', 0, 'DONE'));
  await a;
  expect(api.fetchTickets).toHaveBeenCalledTimes(1);
  second.resolve(ticket('1', 0, 'IN_REVIEW'));
  await b;
  expect(api.fetchTickets).toHaveBeenCalledTimes(2);
  expect(state().tickets[0].status).toBe('IN_REVIEW');
  expect(state().tickets.map((t) => t.id)).toContain('new');
});
