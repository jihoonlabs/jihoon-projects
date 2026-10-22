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
import * as api from '../../../../api/ticketApi';
import { responseTicket } from '../../../../api/test/ticketFixture';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useTicketStore } from '../../../../store/useTicketStore';
import * as projectApi from '@/features/tickets/api/projectApi';

it('persists a board drop with the selected project version', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
  vi.mocked(api.moveTicket).mockResolvedValue({ ticket, boardVersion: 4 });
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  await renderSelectedProject();
  await waitFor(() =>
    expect(useTicketStore.getState().tickets).toHaveLength(1),
  );
  fireEvent.click(screen.getByText('drop DONE'));
  await waitFor(() =>
    expect(api.moveTicket).toHaveBeenCalledWith('1', 'DONE', 0, 3),
  );
});

it.each([false, true])(
  'keeps a failed drag visible after deferred revalidation (project refresh fails: %s) and clears it on retry',
  async (projectRefreshFails) => {
    const ticket = api.toTicket(responseTicket);
    const created = { ...ticket, id: '2', title: 'Concurrent created' };
    vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
    let rejectMove!: (error: Error) => void;
    vi.mocked(api.moveTicket).mockReturnValueOnce(
      new Promise((_resolve, reject) => {
        rejectMove = reject;
      }),
    );
    vi.mocked(api.createTicket).mockResolvedValue(created);
    useTicketStore.setState({ tickets: [], error: null, isLoading: false });
    await renderSelectedProject();
    await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' });
    fireEvent.click(screen.getByText('drop DONE'));
    await waitFor(() => expect(api.moveTicket).toHaveBeenCalled());
    await act(async () => {
      await useTicketStore
        .getState()
        .addTicket({ projectId: '1', title: created.title });
    });
    vi.mocked(api.fetchTickets).mockResolvedValue([ticket, created]);
    if (projectRefreshFails) {
      vi.mocked(projectApi.fetchProjects).mockRejectedValueOnce(
        new Error('project refresh failed'),
      );
    }
    await act(async () => {
      rejectMove(new Error('real drag rejected'));
    });
    await waitFor(() => expect(useTicketStore.getState().error).toBeNull());
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'real drag rejected',
    );
    expect(screen.getByText('Concurrent created')).toBeInTheDocument();
    vi.mocked(api.moveTicket).mockResolvedValueOnce({
      ticket: { ...ticket, status: 'DONE' },
      boardVersion: 4,
    });
    fireEvent.click(screen.getByText('drop DONE'));
    await waitFor(() =>
      expect(screen.queryByRole('alert')).not.toBeInTheDocument(),
    );
  },
);

it.each([false, true])(
  'keeps a newer Project list failure after delayed drag success (switch Project: %s)',
  async (switchProject) => {
    const ticket = api.toTicket(responseTicket);
    vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
    vi.mocked(projectApi.fetchProjects).mockResolvedValue([
      { id: '1', name: 'General', projectKey: 'GEN', boardVersion: 3 },
      { id: '2', name: 'Other', projectKey: 'OTH', boardVersion: 1 },
    ]);
    let resolveMove!: (
      result: Awaited<ReturnType<typeof api.moveTicket>>,
    ) => void;
    vi.mocked(api.moveTicket).mockReturnValueOnce(
      new Promise((resolve) => {
        resolveMove = resolve;
      }),
    );
    useTicketStore.setState({ tickets: [], error: null, isLoading: false });
    await renderSelectedProject();
    await screen.findByRole('combobox', { name: 'First ticket のステータス' });
    fireEvent.click(screen.getByText('drop DONE'));
    await waitFor(() => expect(api.moveTicket).toHaveBeenCalled());

    if (switchProject) {
      fireEvent.change(screen.getByRole('combobox', { name: 'プロジェクト' }), {
        target: { value: '2' },
      });
    }
    fireEvent.click(
      screen.getByRole('button', { name: 'プロジェクト一覧・作成' }),
    );
    vi.mocked(projectApi.fetchProjects).mockRejectedValueOnce(
      new Error('newer project list failure'),
    );
    fireEvent.click(screen.getByRole('button', { name: '一覧を再取得' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'newer project list failure',
    );

    await act(async () => {
      resolveMove({ ticket: { ...ticket, status: 'DONE' }, boardVersion: 4 });
    });
    expect(screen.getByRole('alert')).toHaveTextContent(
      'newer project list failure',
    );
    expect(api.moveTicket).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('combobox', { name: 'プロジェクト' })).toHaveValue(
      switchProject ? '2' : '1',
    );

    fireEvent.click(screen.getByRole('button', { name: '一覧を再取得' }));
    await waitFor(() =>
      expect(screen.queryByRole('alert')).not.toBeInTheDocument(),
    );
  },
);

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
      role: 'user',
      createdAt: '2026-09-24T00:00:00.000000Z',
    },
    isAuthenticated: true,
  });

  try {
    await renderSelectedProject();
    await waitFor(() =>
      expect(screen.getByText('First ticket')).toBeInTheDocument(),
    );
    fireEvent.change(
      screen.getByRole('combobox', { name: '担当者フィルター' }),
      {
        target: { value: 'ME' },
      },
    );
    expect(screen.getByText('First ticket')).toBeInTheDocument();
    expect(screen.queryByText('Other ticket')).not.toBeInTheDocument();
  } finally {
    useAuthStore.setState({ user: null, isAuthenticated: false });
  }
});

it('allows manual status changes while search disables dragging', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
  vi.mocked(api.updateTicketStatus).mockResolvedValue({
    ...ticket,
    status: 'DONE',
  });
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  expect(await screen.findByText('First ticket')).toBeInTheDocument();
  fireEvent.change(screen.getByRole('textbox', { name: 'チケット検索' }), {
    target: { value: 'First ticket' },
  });

  const card = screen
    .getByText('First ticket')
    .closest('[aria-roledescription="sortable"]');
  expect(card).not.toHaveAttribute('aria-disabled', 'true');

  const status = screen.getByRole('combobox', {
    name: 'First ticket のステータス',
  });
  expect(status).toBeEnabled();
  fireEvent.change(status, { target: { value: 'DONE' } });

  await waitFor(() =>
    expect(api.updateTicketStatus).toHaveBeenCalledWith('1', 'DONE'),
  );
});

it('exposes accessible names for search and assignee filters', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();

  expect(
    screen.getByRole('textbox', { name: 'チケット検索' }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole('combobox', { name: '担当者フィルター' }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole('combobox', { name: 'プロジェクト' }),
  ).toBeInTheDocument();
});

it('filters tickets by the selected project', async () => {
  const otherProjectTicket = api.toTicket({
    ...responseTicket,
    id: '2',
    project_id: '2',
    title: 'Other project ticket',
  });
  vi.mocked(api.fetchTickets).mockResolvedValue([
    api.toTicket(responseTicket),
    otherProjectTicket,
  ]);
  vi.mocked(projectApi.fetchProjects).mockResolvedValue([
    { id: '1', name: 'General', projectKey: 'GEN', boardVersion: 3 },
    { id: '2', name: 'Design', projectKey: 'DSN', boardVersion: 3 },
  ]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  expect(await screen.findByText('First ticket')).toBeInTheDocument();
  expect(screen.queryByText('Other project ticket')).not.toBeInTheDocument();
  fireEvent.change(screen.getByRole('combobox', { name: 'プロジェクト' }), {
    target: { value: '2' },
  });
  expect(await screen.findByText('Other project ticket')).toBeInTheDocument();
  expect(screen.queryByText('First ticket')).not.toBeInTheDocument();
});

it('keeps read members read-only while allowing Ticket details and comments', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([api.toTicket(responseTicket)]);
  vi.mocked(projectApi.fetchProjectMembers).mockResolvedValue([
    {
      id: '7',
      name: 'Tester',
      email: 'tester@example.com',
      role: 'member',
      permission: 'read',
    },
  ]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  const ticketTitle = await screen.findByRole('button', {
    name: 'TICK-1 の詳細を開く',
  });
  expect(
    ticketTitle.closest('[aria-roledescription="sortable"]'),
  ).not.toHaveAttribute('aria-disabled', 'true');
  expect(
    await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' }),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: '編集' }),
  ).not.toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: '削除' }),
  ).not.toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: '+ チケット作成' }),
  ).not.toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: 'メンバー管理' }),
  ).not.toBeInTheDocument();
  expect(
    screen.queryByRole('combobox', { name: 'First ticket のステータス' }),
  ).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'TICK-1 の詳細を開く' }));
  expect(
    await screen.findByRole('heading', { name: 'チケット詳細' }),
  ).toBeInTheDocument();
  expect(
    within(screen.getByRole('dialog')).getByText('First ticket'),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: '編集' }),
  ).not.toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: '削除' }),
  ).not.toBeInTheDocument();
  expect(screen.getByRole('heading', { name: 'コメント' })).toBeInTheDocument();
});
