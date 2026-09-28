import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react';
import type { ComponentProps } from 'react';
import { expect, it, vi } from 'vitest';
import * as api from '../../../api/ticketApi';
import { responseTicket } from '../../../api/test/ticketFixture';
import { useTicketStore } from '../../../store/useTicketStore';
import { TicketBoardView } from '../View';

vi.mock('../../../api/ticketApi', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../../api/ticketApi')>()),
  fetchTickets: vi.fn(),
  updateTicketStatus: vi.fn(),
}));
vi.mock('@dnd-kit/core', async (importOriginal) => {
  const original = await importOriginal<typeof import('@dnd-kit/core')>();
  return {
    ...original,
    DndContext: ({
      children,
      onDragEnd,
    }: ComponentProps<typeof original.DndContext>) => (
      <>
        {children}
        {(['DONE', 'IN_REVIEW'] as const).map((status) => (
          <button
            key={status}
            onClick={() =>
              onDragEnd?.({
                active: { id: '1' },
                over: { id: status },
              } as Parameters<NonNullable<typeof onDragEnd>>[0])
            }
          >
            drop {status}
          </button>
        ))}
      </>
    ),
  };
});

it('keeps the final DONE drop while DONE and IN_REVIEW requests are queued', async () => {
  const ticket = api.toTicket(responseTicket);
  let resolve!: (value: typeof ticket) => void;
  const first = new Promise<typeof ticket>((yes) => {
    resolve = yes;
  });
  vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
  vi.mocked(api.updateTicketStatus)
    .mockReturnValueOnce(first)
    .mockImplementation(async (_id, status) => ({ ...ticket, status }));
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  render(<TicketBoardView />);
  await waitFor(() =>
    expect(useTicketStore.getState().tickets).toHaveLength(1),
  );
  fireEvent.click(screen.getByText('drop DONE'));
  fireEvent.click(screen.getByText('drop IN_REVIEW'));
  fireEvent.click(screen.getByText('drop DONE'));
  await act(async () => {
    resolve({ ...ticket, status: 'DONE' });
  });
  await waitFor(() => expect(api.updateTicketStatus).toHaveBeenCalledTimes(3));
  expect(
    vi.mocked(api.updateTicketStatus).mock.calls.map((call) => call[1]),
  ).toEqual(['DONE', 'IN_REVIEW', 'DONE']);
  expect(useTicketStore.getState().tickets[0].status).toBe('DONE');
});
