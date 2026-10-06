import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as api from '../../api/ticketApi';
import { responseTicket } from '../../api/test/ticketFixture';
import type { Ticket } from '../../types/ticket';
import { useTicketStore } from '../useTicketStore';

vi.mock('../../api/ticketApi', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../api/ticketApi')>()),
  fetchTickets: vi.fn(),
  createTicket: vi.fn(),
  updateTicketStatus: vi.fn(),
  moveTicket: vi.fn(),
  updateTicket: vi.fn(),
  deleteTicket: vi.fn(),
}));
const ticket = (
  id: string,
  position = 0,
  status: Ticket['status'] = 'TODO',
): Ticket => ({ ...api.toTicket({ ...responseTicket, position }), id, status });
const state = () => useTicketStore.getState();
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(api.fetchTickets).mockImplementation(async () => state().tickets);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
});

describe('Ticket state and persisted order', () => {
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
  it('keeps restored deletion before a concurrently created ticket with unique positions', async () => {
    useTicketStore.setState({ tickets: [ticket('1')] });
    const request = deferred<void>();
    vi.mocked(api.deleteTicket).mockReturnValue(request.promise);
    const remove = state().deleteTicket('1');
    vi.mocked(api.createTicket).mockResolvedValue(ticket('2', 1));
    await state().addTicket({ projectId: '1', title: 'New' });
    request.reject(new Error('DELETE failed'));
    await remove;
    const ordered = [...state().tickets].sort(
      (a, b) => a.position - b.position,
    );
    expect(ordered.map((t) => t.id)).toEqual(['1', '2']);
    expect(new Set(ordered.map((t) => t.position)).size).toBe(2);
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
  it('uses server positions as the source of truth on refresh', async () => {
    vi.mocked(api.fetchTickets).mockResolvedValue([
      ticket('1', 0),
      ticket('2', 1),
      ticket('3', 2),
    ]);
    await state().fetchTickets();
    expect(state().tickets.map((t) => t.position)).toEqual([0, 1, 2]);
    useTicketStore.setState({ tickets: [ticket('1', 4), ticket('2', 1)] });
    vi.mocked(api.fetchTickets).mockResolvedValue([ticket('1', 2), ticket('2', 3), ticket('3', 1)]);
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
    expect(state().tickets.map((t) => [t.id, t.position])).toEqual([['1', 0], ['2', 1]]);
  });
  it('appends created tickets to their column', async () => {
    useTicketStore.setState({
      tickets: [ticket('1', 4), ticket('2', 90, 'DONE')],
    });
    vi.mocked(api.createTicket).mockResolvedValue(ticket('3', 5));
    await state().addTicket({ projectId: '1', title: 'New' });
    expect(state().tickets.at(-1)).toMatchObject({ id: '3', position: 5 });
    expect(state().isLoading).toBe(false);
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
    expect(state().tickets.map(({ id, status, position }) => [id, status, position])).toEqual([
      ['2', 'DONE', 0],
      ['1', 'DONE', 1],
    ]);
    expect(api.fetchTickets).toHaveBeenCalledTimes(1);
  });
  it('re-fetches the board after a stale-version move conflict', async () => {
    const freshTickets = [ticket('1', 2), ticket('2', 0, 'DONE')];
    useTicketStore.setState({ tickets: [ticket('1', 0), ticket('2', 1)] });
    vi.mocked(api.moveTicket).mockRejectedValue(new api.TicketApiError('stale', 409));
    vi.mocked(api.fetchTickets).mockResolvedValue(freshTickets);

    await expect(state().moveTicket('1', 'DONE', 1, 4)).rejects.toMatchObject({
      status: 409,
    });

    expect(api.fetchTickets).toHaveBeenCalledTimes(1);
    expect(state().tickets).toEqual(freshTickets);
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

    await expect(
      state().updateTicket('1', { title: 'Updated' }),
    ).rejects.toThrow('edit failed');

    expect(state().tickets[0]).toEqual(ticket('1', 4));
    expect(state().error).toBe('edit failed');
  });

  it('restores failed deletion without discarding a new ticket', async () => {
    useTicketStore.setState({ tickets: [ticket('1', 4)] });
    const request = deferred<void>();
    vi.mocked(api.deleteTicket).mockReturnValue(request.promise);
    const action = state().deleteTicket('1');
    expect(state().tickets).toEqual([]);
    vi.mocked(api.createTicket).mockResolvedValue(ticket('2', 1));
    await state().addTicket({ projectId: '1', title: 'New' });
    request.reject(new Error('DELETE failed'));
    await action;
    expect(
      state()
        .tickets.map((t) => t.id)
        .sort(),
    ).toEqual(['1', '2']);
    expect(state().tickets.find((t) => t.id === '1')?.position).toBe(4);
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
  it('reserves the original position for failed column moves as well as deletes', async () => {
    useTicketStore.setState({ tickets: [ticket('1')] });
    const request = deferred<Ticket>();
    vi.mocked(api.updateTicketStatus).mockReturnValue(request.promise);
    const move = state().updateStatus('1', 'DONE');
    vi.mocked(api.createTicket).mockResolvedValue(ticket('2', 1));
    await state().addTicket({ projectId: '1', title: 'New' });
    request.reject(new Error('move failed'));
    await move;
    const ordered = [...state().tickets].sort(
      (a, b) => a.position - b.position,
    );
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
    await expect(state().addTicket({ projectId: '1', title: 'New' })).rejects.toThrow(
      'create failed',
    );
    expect(state().tickets).toEqual([ticket('1', 4)]);
    expect(state().error).toBe('create failed');
    expect(state().isLoading).toBe(false);
  });
});
