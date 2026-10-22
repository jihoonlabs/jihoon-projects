import './setup';
import * as api from '../../../api/ticketApi';
import { useTicketStore } from '../../useTicketStore';
import { deferred, state, ticket } from './helpers';
import { expect, it, vi } from 'vitest';

it('keeps another project unchanged while a drag awaits confirmation and refresh fails', async () => {
  const moving = ticket('1');
  const target = ticket('2', 0, 'DONE');
  const otherProject = { ...ticket('3', 0, 'DONE'), projectId: '2' };
  useTicketStore.setState({ tickets: [moving, target, otherProject] });
  const request = deferred<Awaited<ReturnType<typeof api.moveTicket>>>();
  vi.mocked(api.moveTicket).mockReturnValue(request.promise);
  vi.mocked(api.fetchTickets).mockRejectedValue(new Error('refresh failed'));

  const move = state().moveTicket('1', 'DONE', 1, 3);
  const pendingTickets = state().tickets;
  request.resolve({ ticket: ticket('1', 1, 'DONE'), boardVersion: 4 });
  await expect(move).resolves.toBe(4);

  expect(pendingTickets.find((item) => item.id === '3')).toBe(otherProject);
  expect(pendingTickets.find((item) => item.id === '1')?.position).toBe(1);
  expect(state().tickets.find((item) => item.id === '3')).toBe(otherProject);
  expect(state().error).toBe('refresh failed');
});

it('restores a rejected drag without changing another project order', async () => {
  const moving = ticket('1', 2);
  const target = ticket('2', 0, 'DONE');
  const otherProject = { ...ticket('3', 7, 'DONE'), projectId: '2' };
  useTicketStore.setState({ tickets: [moving, target, otherProject] });
  const request = deferred<Awaited<ReturnType<typeof api.moveTicket>>>();
  vi.mocked(api.moveTicket).mockReturnValue(request.promise);
  const move = expect(state().moveTicket('1', 'DONE', 0, 3)).rejects.toThrow(
    'drag failed',
  );
  request.reject(new Error('drag failed'));
  await move;

  expect(state().tickets.find((item) => item.id === '1')).toBe(moving);
  expect(state().tickets.find((item) => item.id === '2')).toBe(target);
  expect(state().tickets.find((item) => item.id === '3')).toBe(otherProject);
  expect(api.fetchTickets).not.toHaveBeenCalled();
});

it('uses server positions as the source of truth on refresh', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([
    ticket('1', 0),
    ticket('2', 1),
    ticket('3', 2),
  ]);
  await state().fetchTickets();
  expect(state().tickets.map((t) => t.position)).toEqual([0, 1, 2]);
  useTicketStore.setState({ tickets: [ticket('1', 4), ticket('2', 1)] });
  vi.mocked(api.fetchTickets).mockResolvedValue([
    ticket('1', 2),
    ticket('2', 3),
    ticket('3', 1),
  ]);
  await state().fetchTickets();
  expect(state().tickets.map((t) => t.position)).toEqual([2, 3, 1]);
});

it('appends remote column changes and removes server-deleted tickets', async () => {
  useTicketStore.setState({
    tickets: [ticket('1', 50), ticket('2', 7, 'DONE'), ticket('3')],
  });
  vi.mocked(api.fetchTickets).mockResolvedValue([
    ticket('1', 0, 'DONE'),
    ticket('2', 1, 'DONE'),
  ]);
  await state().fetchTickets();
  expect(state().tickets.map((t) => [t.id, t.position])).toEqual([
    ['1', 0],
    ['2', 1],
  ]);
});

it('persists a drag move and adopts the server reordering', async () => {
  useTicketStore.setState({ tickets: [ticket('1', 0), ticket('2', 1)] });
  const serverOrder = [ticket('2', 0, 'DONE'), ticket('1', 1, 'DONE')];
  vi.mocked(api.moveTicket).mockResolvedValue({
    ticket: serverOrder[1],
    boardVersion: 5,
  });
  vi.mocked(api.fetchTickets).mockResolvedValue(serverOrder);

  await expect(state().moveTicket('1', 'DONE', 1, 4)).resolves.toBe(5);

  expect(api.moveTicket).toHaveBeenCalledWith('1', 'DONE', 1, 4);
  expect(
    state().tickets.map(({ id, status, position }) => [id, status, position]),
  ).toEqual([
    ['2', 'DONE', 0],
    ['1', 'DONE', 1],
  ]);
  expect(api.fetchTickets).toHaveBeenCalledTimes(1);
});

it('re-fetches the board after a stale-version move conflict', async () => {
  const freshTickets = [ticket('1', 2), ticket('2', 0, 'DONE')];
  useTicketStore.setState({ tickets: [ticket('1', 0), ticket('2', 1)] });
  vi.mocked(api.moveTicket).mockRejectedValue(
    new api.TicketApiError('stale', 409),
  );
  vi.mocked(api.fetchTickets).mockResolvedValue(freshTickets);

  await expect(state().moveTicket('1', 'DONE', 1, 4)).rejects.toMatchObject({
    status: 409,
  });

  expect(api.fetchTickets).toHaveBeenCalledTimes(1);
  expect(state().tickets).toEqual(freshTickets);
});
