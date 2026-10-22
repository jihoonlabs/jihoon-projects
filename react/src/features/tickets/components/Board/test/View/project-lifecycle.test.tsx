import './setup';
import { renderSelectedProject } from './helpers';
import { expect, it, vi } from 'vitest';
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import * as api from '../../../../api/ticketApi';
import { responseTicket } from '../../../../api/test/ticketFixture';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useTicketStore } from '../../../../store/useTicketStore';
import { TicketBoardView } from '../../View';
import * as projectApi from '@/features/tickets/api/projectApi';

it('allows a read-only project leader to manage members without Ticket write controls', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([api.toTicket(responseTicket)]);
  vi.mocked(projectApi.fetchProjectMembers).mockResolvedValue([
    {
      id: '7',
      name: 'Tester',
      email: 'tester@example.com',
      role: 'leader',
      permission: 'read',
    },
  ]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  expect(
    await screen.findByRole('button', { name: 'メンバー管理' }),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: '+ チケット作成' }),
  ).not.toBeInTheDocument();
});

it('creates the first project and loads its leader membership before enabling Ticket creation', async () => {
  vi.mocked(projectApi.fetchProjects).mockResolvedValue([]);
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  vi.mocked(projectApi.createProject).mockResolvedValue({
    id: '2',
    name: 'New team',
    projectKey: 'NEW',
    boardVersion: 1,
  });
  vi.mocked(projectApi.fetchProjectMembers).mockResolvedValue([
    {
      id: '7',
      name: 'Tester',
      email: 'tester@example.com',
      role: 'leader',
      permission: 'write',
    },
  ]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  render(<TicketBoardView />);
  expect(
    screen.queryByRole('button', { name: '+ チケット作成' }),
  ).not.toBeInTheDocument();
  fireEvent.click(
    screen.getByRole('button', { name: 'プロジェクト一覧・作成' }),
  );
  fireEvent.change(screen.getByLabelText('プロジェクト名'), {
    target: { value: 'New team' },
  });
  await waitFor(() =>
    expect(
      screen.getByRole('button', { name: 'プロジェクトを作成' }),
    ).toBeEnabled(),
  );
  fireEvent.click(screen.getByRole('button', { name: 'プロジェクトを作成' }));
  expect(await screen.findByRole('status')).toHaveTextContent(
    'New team を作成しました',
  );
  await waitFor(() =>
    expect(screen.getByRole('combobox', { name: 'プロジェクト' })).toHaveValue(
      '2',
    ),
  );
  expect(projectApi.fetchProjectMembers).toHaveBeenCalledWith('2');
  expect(
    await screen.findByRole('button', { name: 'メンバー管理' }),
  ).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: '+ チケット作成' }));
  expect(
    await screen.findByRole('heading', { name: 'チケット作成' }),
  ).toBeInTheDocument();
});

it('keeps archived Project boards read-only even for admins and exposes restoration', async () => {
  const archived = {
    id: '1',
    name: 'General',
    projectKey: 'GEN',
    boardVersion: 3,
    archivedAt: '2026-10-13T00:00:00Z',
  };
  vi.mocked(projectApi.fetchProjects).mockImplementation(async (options) =>
    options?.archived ? [archived] : [],
  );
  vi.mocked(api.fetchTickets).mockResolvedValue([api.toTicket(responseTicket)]);
  useAuthStore.setState({
    user: { ...useAuthStore.getState().user!, role: 'admin' },
  });
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  render(<TicketBoardView />);
  fireEvent.click(
    screen.getByRole('button', { name: 'プロジェクト一覧・作成' }),
  );
  fireEvent.click(
    screen.getByRole('checkbox', { name: '終了したプロジェクトを表示' }),
  );
  await screen.findByRole('option', { name: 'General' });
  fireEvent.click(
    screen.getByRole('button', { name: 'General GEN ボードを開く' }),
  );
  await waitFor(() =>
    expect(screen.getByRole('combobox', { name: 'プロジェクト' })).toHaveValue(
      '1',
    ),
  );
  expect(
    screen.queryByRole('button', { name: '+ チケット作成' }),
  ).not.toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: 'メンバー管理' }),
  ).not.toBeInTheDocument();
  expect(
    screen.queryByRole('combobox', { name: 'First ticket のステータス' }),
  ).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'プロジェクト設定' }));
  expect(
    screen.getByRole('button', { name: 'プロジェクトを復元' }),
  ).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'TICK-1 の詳細を開く' }));
  const detail = await screen.findByRole('dialog');
  expect(
    within(detail).queryByRole('button', { name: '編集' }),
  ).not.toBeInTheDocument();
  expect(
    within(detail).queryByLabelText('コメントを追加'),
  ).not.toBeInTheDocument();
});

it('archives the current Project without deleting Tickets and removes it from the active list', async () => {
  const project = {
    id: '1',
    name: 'General',
    projectKey: 'GEN',
    boardVersion: 3,
  };
  vi.mocked(api.fetchTickets).mockResolvedValue([api.toTicket(responseTicket)]);
  useAuthStore.setState({
    user: { ...useAuthStore.getState().user!, role: 'admin' },
  });
  vi.mocked(projectApi.archiveProject).mockResolvedValue({
    ...project,
    archivedAt: '2026-10-13T00:00:00Z',
  });
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  await renderSelectedProject();
  fireEvent.click(
    await screen.findByRole('button', { name: 'プロジェクト設定' }),
  );
  fireEvent.click(screen.getByRole('button', { name: 'プロジェクトを終了' }));
  fireEvent.click(screen.getByRole('button', { name: '終了を確定' }));
  await waitFor(() =>
    expect(screen.getByRole('status')).toHaveTextContent(
      'General を終了しました',
    ),
  );
  expect(screen.getByRole('combobox', { name: 'プロジェクト' })).toHaveValue(
    'ALL',
  );
  expect(useTicketStore.getState().tickets).toHaveLength(1);
});

it('updates leader authority immediately after a successful transfer', async () => {
  const leader = {
    id: '7',
    name: 'Tester',
    email: 'tester@example.com',
    role: 'leader' as const,
    permission: 'write' as const,
  };
  const member = {
    id: '8',
    name: 'Ren',
    email: 'ren@example.com',
    role: 'member' as const,
    permission: 'write' as const,
  };
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  vi.mocked(projectApi.fetchProjectMembers).mockResolvedValue([leader, member]);
  vi.mocked(projectApi.transferProjectLeader).mockResolvedValue({
    ...member,
    role: 'leader',
  });
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  await renderSelectedProject();
  fireEvent.click(await screen.findByRole('button', { name: 'メンバー管理' }));
  fireEvent.click(
    await screen.findByRole('button', { name: 'Ren をリーダーにする' }),
  );
  vi.mocked(projectApi.fetchProjectMembers).mockResolvedValue([
    { ...leader, role: 'member' },
    { ...member, role: 'leader' },
  ]);
  fireEvent.click(
    screen.getByRole('button', { name: 'リーダー引き継ぎを確定' }),
  );
  expect(
    await screen.findByText(
      '管理権限が変更されました。現在はメンバー一覧の閲覧のみ可能です。',
    ),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: 'プロジェクト設定' }),
  ).not.toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: 'メンバー管理' }),
  ).not.toBeInTheDocument();
  expect(
    screen.getByRole('button', { name: '+ チケット作成' }),
  ).toBeInTheDocument();
});

it('does not resurrect an archived Project when an older Project refresh arrives late', async () => {
  const project = {
    id: '1',
    name: 'General',
    projectKey: 'GEN',
    boardVersion: 3,
  };
  const ticket = { ...api.toTicket(responseTicket), status: 'DONE' as const };
  vi.mocked(api.fetchTickets).mockResolvedValue([api.toTicket(responseTicket)]);
  vi.mocked(api.updateTicketStatus).mockResolvedValue(ticket);
  vi.mocked(projectApi.archiveProject).mockResolvedValue({
    ...project,
    archivedAt: '2026-10-13T00:00:00Z',
  });
  useAuthStore.setState({
    user: { ...useAuthStore.getState().user!, role: 'admin' },
  });
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  await renderSelectedProject();
  const status = await screen.findByRole('combobox', {
    name: 'First ticket のステータス',
  });
  let oldRefresh!: (value: (typeof project)[]) => void;
  vi.mocked(projectApi.fetchProjects).mockReturnValueOnce(
    new Promise((resolve) => {
      oldRefresh = resolve;
    }),
  );
  vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
  fireEvent.change(status, { target: { value: 'DONE' } });
  await waitFor(() => expect(oldRefresh).toBeDefined());
  fireEvent.click(screen.getByRole('button', { name: 'プロジェクト設定' }));
  fireEvent.click(screen.getByRole('button', { name: 'プロジェクトを終了' }));
  fireEvent.click(screen.getByRole('button', { name: '終了を確定' }));
  await waitFor(() =>
    expect(screen.getByRole('combobox', { name: 'プロジェクト' })).toHaveValue(
      'ALL',
    ),
  );
  await act(async () => {
    oldRefresh([project]);
  });
  expect(screen.getByRole('combobox', { name: 'プロジェクト' })).toHaveValue(
    'ALL',
  );
  expect(
    screen.queryByRole('button', { name: '+ チケット作成' }),
  ).not.toBeInTheDocument();
});
