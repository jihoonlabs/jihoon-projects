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
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useTicketStore } from '../../../store/useTicketStore';
import { TicketBoardView } from '../View';

vi.mock('../../../api/ticketApi', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../../api/ticketApi')>()),
  fetchTickets: vi.fn(),
  updateTicketStatus: vi.fn(),
  createTicket: vi.fn(),
  updateTicket: vi.fn(),
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

it('shows tickets assigned to the signed-in user in the ME filter', async () => {
  const mine = api.toTicket(responseTicket);
  const other = api.toTicket({
    ...responseTicket,
    id: '2',
    title: 'Other ticket',
    assignee: { id: 1, name: 'Other', avatar_url: null },
  });
  vi.mocked(api.fetchTickets).mockResolvedValue([mine, other]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  useAuthStore.setState({
    user: {
      id: 7,
      name: 'Tester',
      email: 'tester@example.com',
      status: 'active',
      createdAt: '2026-09-24T00:00:00.000000Z',
    },
    isAuthenticated: true,
  });

  try {
    render(<TicketBoardView />);
    await waitFor(() =>
      expect(screen.getByText('First ticket')).toBeInTheDocument(),
    );
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'ME' } });
    expect(screen.getByText('First ticket')).toBeInTheDocument();
    expect(screen.queryByText('Other ticket')).not.toBeInTheDocument();
  } finally {
    useAuthStore.setState({ user: null, isAuthenticated: false });
  }
});

it('keeps the create modal open and shows the save error when creation fails', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  vi.mocked(api.createTicket).mockRejectedValue(new Error('create failed'));
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  render(<TicketBoardView />);
  fireEvent.click(screen.getByRole('button', { name: '+ チケット作成' }));
  fireEvent.change(screen.getByLabelText('タイトル'), {
    target: { value: 'New ticket' },
  });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));

  expect(await screen.findByRole('alert')).toHaveTextContent('create failed');
  expect(screen.getByRole('dialog')).toBeInTheDocument();
  expect(screen.getByLabelText('タイトル')).toHaveValue('New ticket');
});

it('keeps the edit modal open and shows the save error when editing fails', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
  vi.mocked(api.updateTicket).mockRejectedValue(new Error('update failed'));
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  render(<TicketBoardView />);
  await screen.findByText('First ticket');
  fireEvent.click(screen.getByRole('button', { name: '編集' }));
  fireEvent.change(screen.getByLabelText('タイトル'), {
    target: { value: 'Updated ticket' },
  });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));

  expect(await screen.findByRole('alert')).toHaveTextContent('update failed');
  expect(screen.getByRole('dialog')).toBeInTheDocument();
  expect(screen.getByLabelText('タイトル')).toHaveValue('Updated ticket');
});
