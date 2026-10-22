import './setup';
import { renderSelectedProject } from './helpers';
import { expect, it, vi } from 'vitest';
import {
  act,
  fireEvent,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import * as api from '../../../../api/ticketApi';
import { TicketApiError } from '../../../../api/ticketApi';
import { responseTicket } from '../../../../api/test/ticketFixture';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useTicketStore } from '../../../../store/useTicketStore';
import * as projectApi from '@/features/tickets/api/projectApi';

it('keeps the create modal open and shows the save error when creation fails', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  vi.mocked(api.createTicket).mockRejectedValue(new Error('create failed'));
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  fireEvent.click(
    await screen.findByRole('button', { name: '+ チケット作成' }),
  );
  fireEvent.change(screen.getByLabelText('タイトル'), {
    target: { value: 'New ticket' },
  });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));

  expect(
    await within(screen.getByRole('dialog')).findByRole('alert'),
  ).toHaveTextContent('create failed');
  expect(screen.getByRole('dialog')).toBeInTheDocument();
  expect(screen.getByLabelText('タイトル')).toHaveValue('New ticket');
});

it('keeps a create draft retryable after session expiry and reauthentication', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  vi.mocked(api.createTicket)
    .mockImplementationOnce(async () => {
      useAuthStore.getState().expireSession();
      throw new TicketApiError('session expired', 401);
    })
    .mockResolvedValueOnce(api.toTicket(responseTicket));
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  fireEvent.click(
    await screen.findByRole('button', { name: '+ チケット作成' }),
  );
  fireEvent.change(screen.getByLabelText('タイトル'), {
    target: { value: 'Retry after reauthentication' },
  });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));

  await within(screen.getByRole('dialog')).findByRole('alert');
  expect(useAuthStore.getState().sessionExpired).toBe(true);
  expect(screen.getByLabelText('タイトル')).toHaveValue(
    'Retry after reauthentication',
  );

  act(() => useAuthStore.getState().login(useAuthStore.getState().user!));
  await waitFor(() =>
    expect(screen.getByRole('button', { name: '保存' })).toBeEnabled(),
  );
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  await waitFor(() => expect(api.createTicket).toHaveBeenCalledTimes(2));
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});

it('keeps the modal open when the backdrop is clicked while saving', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  let resolveCreate!: (value: ReturnType<typeof api.toTicket>) => void;
  vi.mocked(api.createTicket).mockReturnValue(
    new Promise((resolve) => {
      resolveCreate = resolve;
    }),
  );
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  fireEvent.click(
    await screen.findByRole('button', { name: '+ チケット作成' }),
  );
  fireEvent.change(screen.getByLabelText('タイトル'), {
    target: { value: 'New ticket' },
  });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));

  const dialog = screen.getByRole('dialog');
  fireEvent.mouseDown(dialog.parentElement!);
  expect(screen.getByRole('dialog')).toBeInTheDocument();

  await act(async () => {
    resolveCreate(api.toTicket(responseTicket));
  });
  await waitFor(() =>
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
  );
});

it('keeps the edit modal open and shows the save error when editing fails', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
  vi.mocked(api.updateTicket).mockRejectedValue(new Error('update failed'));
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' });
  fireEvent.click(screen.getByRole('button', { name: 'TICK-1 の詳細を開く' }));
  await screen.findByRole('heading', { name: 'チケット詳細' });
  fireEvent.click(screen.getByRole('button', { name: '編集' }));
  fireEvent.change(screen.getByLabelText('タイトル'), {
    target: { value: 'Updated ticket' },
  });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));

  expect(
    await within(screen.getByRole('dialog')).findByRole('alert'),
  ).toHaveTextContent('update failed');
  expect(screen.getByRole('dialog')).toBeInTheDocument();
  expect(screen.getByLabelText('タイトル')).toHaveValue('Updated ticket');
});

it('opens details from the title with the keyboard and restores focus on close', async () => {
  const user = userEvent.setup();
  vi.mocked(api.fetchTickets).mockResolvedValue([api.toTicket(responseTicket)]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  const title = await screen.findByRole('button', {
    name: 'TICK-1 の詳細を開く',
  });
  title.focus();
  await user.keyboard('{Enter}');

  const heading = await screen.findByRole('heading', { name: 'チケット詳細' });
  expect(document.activeElement).toBe(heading);
  fireEvent.click(screen.getByRole('button', { name: '閉じる' }));
  await waitFor(() => expect(document.activeElement).toBe(title));
});

it('saves edits from detail and returns to the refreshed detail view', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
  vi.mocked(api.updateTicket).mockResolvedValue({
    ...ticket,
    title: 'Saved title',
    description: 'Saved description',
    priority: 'HIGH',
  });
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' });
  fireEvent.click(screen.getByRole('button', { name: 'TICK-1 の詳細を開く' }));
  fireEvent.click(await screen.findByRole('button', { name: '編集' }));
  fireEvent.change(screen.getByLabelText('タイトル'), {
    target: { value: 'Saved title' },
  });
  fireEvent.change(screen.getByLabelText('説明'), {
    target: { value: 'Saved description' },
  });
  fireEvent.change(screen.getByLabelText('優先度'), {
    target: { value: 'HIGH' },
  });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));

  await waitFor(() =>
    expect(
      screen.getByRole('heading', { name: 'チケット詳細' }),
    ).toBeInTheDocument(),
  );
  expect(screen.getByText('Saved title')).toBeInTheDocument();
  expect(screen.getByText('Saved description')).toBeInTheDocument();
  expect(api.updateTicket).toHaveBeenCalledWith(
    '1',
    expect.objectContaining({ title: 'Saved title', priority: 'HIGH' }),
  );
});

it.each(['7', ''])(
  'restores the initial assignee %s after two saves in the same detail',
  async (initialAssignee) => {
    const ticket = api.toTicket({
      ...responseTicket,
      assignee: initialAssignee
        ? { id: 7, name: 'Tester', avatar_url: null }
        : null,
    });
    vi.mocked(projectApi.fetchProjectMembers).mockResolvedValue([
      {
        id: '7',
        name: 'Tester',
        email: null,
        role: 'member',
        permission: 'write',
      },
      {
        id: '8',
        name: 'Other',
        email: null,
        role: 'member',
        permission: 'write',
      },
    ]);
    vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
    vi.mocked(api.updateTicket).mockImplementation(async (_id, input) => ({
      ...ticket,
      assignee: input.assigneeId
        ? { id: input.assigneeId, name: 'Member' }
        : null,
    }));
    useTicketStore.setState({ tickets: [], error: null, isLoading: false });
    await renderSelectedProject();
    fireEvent.click(
      await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' }),
    );
    for (const assignee of ['8', initialAssignee]) {
      fireEvent.click(await screen.findByRole('button', { name: '編集' }));
      fireEvent.change(screen.getByLabelText('担当者'), {
        target: { value: assignee },
      });
      fireEvent.click(screen.getByRole('button', { name: '保存' }));
      await screen.findByRole('heading', { name: 'チケット詳細' });
    }
    expect(api.updateTicket).toHaveBeenLastCalledWith(
      '1',
      expect.objectContaining({ assigneeId: initialAssignee || null }),
    );
    expect(useTicketStore.getState().tickets[0].assignee?.id ?? '').toBe(
      initialAssignee,
    );
  },
);

it('deletes a ticket from detail only after confirmation', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets)
    .mockResolvedValueOnce([ticket])
    .mockResolvedValue([]);
  vi.mocked(api.deleteTicket).mockResolvedValue(undefined);
  vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' });
  expect(
    screen.queryByRole('button', { name: '削除' }),
  ).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'TICK-1 の詳細を開く' }));
  fireEvent.click(await screen.findByRole('button', { name: '削除' }));

  await waitFor(() => expect(api.deleteTicket).toHaveBeenCalledWith('1'));
  await waitFor(() =>
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
  );
});

it('keeps detail open and reports a failed delete', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([api.toTicket(responseTicket)]);
  vi.mocked(api.deleteTicket).mockRejectedValue(new Error('delete failed'));
  vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' });
  fireEvent.click(screen.getByRole('button', { name: 'TICK-1 の詳細を開く' }));
  fireEvent.click(await screen.findByRole('button', { name: '削除' }));

  expect(await screen.findByRole('alert')).toHaveTextContent('delete failed');
  expect(
    screen.getByRole('heading', { name: 'チケット詳細' }),
  ).toBeInTheDocument();
});

it('does not open a ticket detail from a drag completion on the board', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
  vi.mocked(api.moveTicket).mockResolvedValue({ ticket, boardVersion: 4 });
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' });
  fireEvent.click(screen.getByText('drop DONE'));

  await waitFor(() => expect(api.moveTicket).toHaveBeenCalled());
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});

it('does not turn a saved Ticket into a failed creation when Project refresh fails', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets)
    .mockResolvedValueOnce([])
    .mockResolvedValue([ticket]);
  vi.mocked(api.createTicket).mockClear().mockResolvedValue(ticket);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  await renderSelectedProject();
  fireEvent.click(
    await screen.findByRole('button', { name: '+ チケット作成' }),
  );
  vi.mocked(projectApi.fetchProjects).mockRejectedValueOnce(
    new Error('一覧更新失敗'),
  );
  fireEvent.change(screen.getByLabelText('タイトル'), {
    target: { value: ticket.title },
  });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  await waitFor(() =>
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
  );
  expect(await screen.findByRole('alert')).toHaveTextContent('一覧更新失敗');
  expect(useTicketStore.getState().tickets).toContainEqual(ticket);
  expect(api.createTicket).toHaveBeenCalledTimes(1);
});

it('closes a successfully deleted Ticket even when the Project refresh fails', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets)
    .mockResolvedValueOnce([ticket])
    .mockResolvedValue([]);
  vi.mocked(api.deleteTicket).mockResolvedValue(undefined);
  vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  await renderSelectedProject();
  fireEvent.click(
    await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' }),
  );
  const remove = await screen.findByRole('button', { name: '削除' });
  vi.mocked(projectApi.fetchProjects).mockRejectedValueOnce(
    new Error('metadata unavailable'),
  );
  fireEvent.click(remove);
  await waitFor(() =>
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
  );
  expect(screen.getByRole('alert')).toHaveTextContent('metadata unavailable');
  expect(useTicketStore.getState().tickets).toHaveLength(0);
  expect(
    screen.queryByRole('button', { name: 'TICK-1 の詳細を開く' }),
  ).not.toBeInTheDocument();
});
