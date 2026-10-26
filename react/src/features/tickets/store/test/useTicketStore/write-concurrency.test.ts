import './setup';
import * as api from '../../../api/ticketApi';
import { useTicketStore } from '../../useTicketStore';
import { deferred, state, ticket } from './helpers';
import type { Ticket } from '../../../types/ticket';
import { expect, it, vi } from 'vitest';

it('rolls back only the failed ticket while retaining a concurrent success', async () => {
  useTicketStore.setState({ tickets: [ticket('1', 3), ticket('2', 8)] });
  const request = deferred<Ticket>();
  vi.mocked(api.updateTicketStatus).mockImplementation((id) =>
    id === '1' ? request.promise : Promise.resolve(ticket('2', 0, 'DONE')),
  );
  const first = state().updateStatus('1', 'DONE');
  await state().updateStatus('2', 'DONE');
  request.reject(new Error('PATCH failed'));
  await first;
  expect(state().tickets[0]).toMatchObject({ status: 'TODO', position: 3 });
  expect(state().tickets[1]).toMatchObject({ status: 'DONE', position: 0 });
});

it('serializes same-ticket updates and restores the last confirmed state on failure', async () => {
  useTicketStore.setState({ tickets: [ticket('1')] });
  const request = deferred<Ticket>();
  vi.mocked(api.updateTicketStatus)
    .mockReturnValueOnce(request.promise)
    .mockRejectedValueOnce(new Error('second failed'));
  const first = state().updateStatus('1', 'DONE');
  const second = state().updateStatus('1', 'IN_REVIEW');
  expect(api.updateTicketStatus).toHaveBeenCalledTimes(1);
  request.resolve(ticket('1', 0, 'DONE'));
  await Promise.all([first, second]);
  expect(state().tickets[0].status).toBe('DONE');
});

it('preserves a concurrent same-project edit when drag rollback and refresh fail', async () => {
  useTicketStore.setState({ tickets: [ticket('1'), ticket('2', 1)] });
  const request = deferred<Awaited<ReturnType<typeof api.moveTicket>>>();
  vi.mocked(api.moveTicket).mockReturnValue(request.promise);
  vi.mocked(api.fetchTickets).mockRejectedValue(new Error('refresh failed'));
  const failedMove = expect(
    state().moveTicket('1', 'DONE', 0, 3),
  ).rejects.toThrow('drag failed');

  const edited = {
    ...ticket('2', 1),
    title: 'Confirmed edit',
    status: 'IN_REVIEW' as const,
  };
  vi.mocked(api.updateTicket).mockResolvedValue(edited);
  await state().updateTicket('2', {
    title: edited.title,
    status: edited.status,
  });
  request.reject(new Error('drag failed'));
  await failedMove;

  expect(state().tickets.find((item) => item.id === '2')).toEqual(edited);
  expect(state().tickets.find((item) => item.id === '1')).toEqual(ticket('1'));
  expect(api.fetchTickets).toHaveBeenCalledTimes(1);
  expect(state().error).toBe('refresh failed');
});

it('preserves concurrent same-project creation and deletion when drag rollback and refresh fail', async () => {
  useTicketStore.setState({ tickets: [ticket('1'), ticket('2', 1)] });
  const request = deferred<Awaited<ReturnType<typeof api.moveTicket>>>();
  vi.mocked(api.moveTicket).mockReturnValue(request.promise);
  vi.mocked(api.fetchTickets).mockRejectedValue(new Error('refresh failed'));
  const failedMove = expect(
    state().moveTicket('1', 'DONE', 0, 3),
  ).rejects.toThrow('drag failed');

  vi.mocked(api.deleteTicket).mockResolvedValue(undefined);
  await state().deleteTicket('2');
  vi.mocked(api.createTicket).mockResolvedValue(ticket('3', 1));
  await state().addTicket({ projectId: '1', title: 'Created' });
  request.reject(new Error('drag failed'));
  await failedMove;

  expect(
    state()
      .tickets.map((item) => item.id)
      .sort(),
  ).toEqual(['1', '3']);
  expect(api.fetchTickets).toHaveBeenCalledTimes(1);
  expect(state().error).toBe('refresh failed');
});

it('runs a later explicit queued drag after a failed drag without retrying the failed request', async () => {
  useTicketStore.setState({ tickets: [ticket('1')] });
  const first = deferred<Awaited<ReturnType<typeof api.moveTicket>>>();
  vi.mocked(api.moveTicket)
    .mockReturnValueOnce(first.promise)
    .mockResolvedValueOnce({
      ticket: ticket('1', 0, 'IN_REVIEW'),
      boardVersion: 5,
    });
  const failed = state().moveTicket('1', 'DONE', 0, 4);
  const later = state().moveTicket('1', 'IN_REVIEW', 0, 4);
  const completed = Promise.allSettled([failed, later]);
  first.reject(new Error('first drag failed'));
  const results = await completed;
  expect(results[0]).toMatchObject({
    status: 'rejected',
    reason: new Error('first drag failed'),
  });
  expect(api.moveTicket).toHaveBeenCalledTimes(2);
  expect(vi.mocked(api.moveTicket).mock.calls.map((args) => args[1])).toEqual([
    'DONE',
    'IN_REVIEW',
  ]);
  expect(results[1]).toEqual({ status: 'fulfilled', value: 5 });
});

it('keeps a later queued drag conflict rejected without automatically retrying', async () => {
  useTicketStore.setState({ tickets: [ticket('1')] });
  const first = deferred<Awaited<ReturnType<typeof api.moveTicket>>>();
  vi.mocked(api.moveTicket)
    .mockReturnValueOnce(first.promise)
    .mockRejectedValueOnce(new api.TicketApiError('later conflict', 409));
  const failed = state().moveTicket('1', 'DONE', 0, 4);
  const later = state().moveTicket('1', 'IN_REVIEW', 0, 4);
  const completed = Promise.allSettled([failed, later]);
  first.reject(new Error('first drag failed'));
  const results = await completed;
  expect(results[0]).toMatchObject({
    status: 'rejected',
    reason: new Error('first drag failed'),
  });
  expect(results[1]).toMatchObject({
    status: 'rejected',
    reason: { status: 409, message: 'later conflict' },
  });
  expect(api.moveTicket).toHaveBeenCalledTimes(2);
});
