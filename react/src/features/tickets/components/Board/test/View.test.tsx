import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import type { ComponentProps } from 'react';
import { beforeEach, expect, it, vi } from 'vitest';
import * as api from '../../../api/ticketApi';
import { responseTicket } from '../../../api/test/ticketFixture';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useTicketStore } from '../../../store/useTicketStore';
import { TicketBoardView } from '../View';
import * as projectApi from '@/features/tickets/api/projectApi';

vi.mock('../../../api/ticketApi', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../../api/ticketApi')>()),
  fetchTickets: vi.fn(),
  updateTicketStatus: vi.fn(),
  moveTicket: vi.fn(),
  createTicket: vi.fn(),
  updateTicket: vi.fn(),
}));
vi.mock('../../../api/ticketCommentApi', () => ({
  fetchTicketComments: vi.fn().mockResolvedValue([]),
  createTicketComment: vi.fn(),
  updateTicketComment: vi.fn(),
  deleteTicketComment: vi.fn(),
}));
vi.mock('@/features/tickets/api/projectApi', () => ({
  fetchProjects: vi.fn().mockResolvedValue([{ id: '1', name: 'General', projectKey: 'GEN', boardVersion: 3 }]),
  fetchProjectMembers: vi.fn().mockResolvedValue([{ id: '7', name: 'Tester', email: 'tester@example.com', role: 'member', permission: 'write' }]),
  addProjectMember: vi.fn(),
  updateProjectMember: vi.fn(),
  removeProjectMember: vi.fn(),
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

beforeEach(() => {
  vi.mocked(projectApi.fetchProjects).mockResolvedValue([{ id: '1', name: 'General', projectKey: 'GEN', boardVersion: 3 }]);
  vi.mocked(projectApi.fetchProjectMembers).mockResolvedValue([{ id: '7', name: 'Tester', email: 'tester@example.com', role: 'member', permission: 'write' }]);
  useAuthStore.setState({ user: { id: 7, name: 'Tester', email: 'tester@example.com', status: 'active', role: 'user', createdAt: '2026-09-24T00:00:00.000000Z' }, isAuthenticated: true });
});

it('persists a board drop with the selected project version', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
  vi.mocked(api.moveTicket).mockResolvedValue({ ticket, boardVersion: 4 });
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  render(<TicketBoardView />);
  await waitFor(() =>
    expect(useTicketStore.getState().tickets).toHaveLength(1),
  );
  fireEvent.click(screen.getByText('drop DONE'));
  await waitFor(() => expect(api.moveTicket).toHaveBeenCalledWith('1', 'DONE', 0, 3));
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
      role: 'user',
      createdAt: '2026-09-24T00:00:00.000000Z',
    },
    isAuthenticated: true,
  });

  try {
    render(<TicketBoardView />);
    await waitFor(() =>
      expect(screen.getByText('First ticket')).toBeInTheDocument(),
    );
    fireEvent.change(screen.getByRole('combobox', { name: '担当者フィルター' }), {
      target: { value: 'ME' },
    });
    expect(screen.getByText('First ticket')).toBeInTheDocument();
    expect(screen.queryByText('Other ticket')).not.toBeInTheDocument();
  } finally {
    useAuthStore.setState({ user: null, isAuthenticated: false });
  }
});

it('allows manual status changes while search disables dragging', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
  vi.mocked(api.updateTicketStatus).mockResolvedValue({ ...ticket, status: 'DONE' });
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  render(<TicketBoardView />);
  expect(await screen.findByText('First ticket')).toBeInTheDocument();
  fireEvent.change(screen.getByRole('textbox', { name: 'チケット検索' }), {
    target: { value: 'First ticket' },
  });

  const card = screen.getByText('First ticket').closest('[aria-roledescription="sortable"]');
  expect(card).not.toHaveAttribute('aria-disabled', 'true');

  const status = screen.getByRole('combobox', { name: 'First ticket のステータス' });
  expect(status).toBeEnabled();
  fireEvent.change(status, { target: { value: 'DONE' } });

  await waitFor(() =>
    expect(api.updateTicketStatus).toHaveBeenCalledWith('1', 'DONE'),
  );
});

it('exposes accessible names for search and assignee filters', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  render(<TicketBoardView />);

  expect(screen.getByRole('textbox', { name: 'チケット検索' })).toBeInTheDocument();
  expect(
    screen.getByRole('combobox', { name: '担当者フィルター' }),
  ).toBeInTheDocument();
  expect(screen.getByRole('combobox', { name: 'プロジェクト' })).toBeInTheDocument();
});

it('filters tickets by the selected project', async () => {
  const otherProjectTicket = api.toTicket({ ...responseTicket, id: '2', project_id: '2', title: 'Other project ticket' });
  vi.mocked(api.fetchTickets).mockResolvedValue([api.toTicket(responseTicket), otherProjectTicket]);
  vi.mocked(projectApi.fetchProjects).mockResolvedValue([{ id: '1', name: 'General', projectKey: 'GEN', boardVersion: 3 }, { id: '2', name: 'Design', projectKey: 'DSN', boardVersion: 3 }]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  render(<TicketBoardView />);
  expect(await screen.findByText('First ticket')).toBeInTheDocument();
  expect(screen.queryByText('Other project ticket')).not.toBeInTheDocument();
  fireEvent.change(screen.getByRole('combobox', { name: 'プロジェクト' }), { target: { value: '2' } });
  expect(await screen.findByText('Other project ticket')).toBeInTheDocument();
  expect(screen.queryByText('First ticket')).not.toBeInTheDocument();
});

it('keeps read members read-only while allowing Ticket details and comments', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([api.toTicket(responseTicket)]);
  vi.mocked(projectApi.fetchProjectMembers).mockResolvedValue([{ id: '7', name: 'Tester', email: 'tester@example.com', role: 'member', permission: 'read' }]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  render(<TicketBoardView />);
  const ticketTitle = await screen.findByText('First ticket');
  expect(ticketTitle.closest('[aria-roledescription="sortable"]')).not.toHaveAttribute('aria-disabled', 'true');
  expect(await screen.findByRole('button', { name: '詳細' })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '+ チケット作成' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'メンバー管理' })).not.toBeInTheDocument();
  expect(screen.queryByRole('combobox', { name: 'First ticket のステータス' })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: '詳細' }));
  expect(await screen.findByRole('heading', { name: 'チケット詳細' })).toBeInTheDocument();
  expect(screen.getByLabelText('タイトル')).toHaveAttribute('readonly');
  expect(screen.getByRole('heading', { name: 'コメント' })).toBeInTheDocument();
});

it('allows a read-only project leader to manage members without Ticket write controls', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([api.toTicket(responseTicket)]);
  vi.mocked(projectApi.fetchProjectMembers).mockResolvedValue([{ id: '7', name: 'Tester', email: 'tester@example.com', role: 'leader', permission: 'read' }]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  render(<TicketBoardView />);
  expect(await screen.findByRole('button', { name: 'メンバー管理' })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '+ チケット作成' })).not.toBeInTheDocument();
});

it('lets a project leader add members and change each member role and permission', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  vi.mocked(projectApi.fetchProjectMembers).mockResolvedValue([{ id: '7', name: 'Tester', email: 'tester@example.com', role: 'leader', permission: 'read' }]);
  vi.mocked(projectApi.addProjectMember).mockResolvedValue({ id: '8', name: 'New member', email: 'new@example.com', role: 'member', permission: 'write' });
  vi.mocked(projectApi.updateProjectMember).mockResolvedValue({ id: '7', name: 'Tester', email: 'tester@example.com', role: 'leader', permission: 'write' });
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  render(<TicketBoardView />);
  fireEvent.click(await screen.findByRole('button', { name: 'メンバー管理' }));
  const dialog = await screen.findByRole('dialog');
  expect(within(dialog).getByText(/Tester/)).toBeInTheDocument();
  fireEvent.change(within(dialog).getByRole('combobox', { name: 'Tester の権限' }), { target: { value: 'write' } });
  await waitFor(() => expect(projectApi.updateProjectMember).toHaveBeenCalledWith('1', '7', { role: 'leader', permission: 'write' }));
  fireEvent.change(within(dialog).getByLabelText('メールアドレス'), { target: { value: 'new@example.com' } });
  fireEvent.click(within(dialog).getByRole('button', { name: 'メンバーを追加' }));
  await waitFor(() => expect(projectApi.addProjectMember).toHaveBeenCalledWith('1', { email: 'new@example.com', role: 'member', permission: 'write' }));
});

it('keeps the create modal open and shows the save error when creation fails', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  vi.mocked(api.createTicket).mockRejectedValue(new Error('create failed'));
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  render(<TicketBoardView />);
  fireEvent.click(await screen.findByRole('button', { name: '+ チケット作成' }));
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

it('keeps the modal open when the backdrop is clicked while saving', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  let resolveCreate!: (value: ReturnType<typeof api.toTicket>) => void;
  vi.mocked(api.createTicket).mockReturnValue(
    new Promise((resolve) => {
      resolveCreate = resolve;
    }),
  );
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  render(<TicketBoardView />);
  fireEvent.click(await screen.findByRole('button', { name: '+ チケット作成' }));
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

  render(<TicketBoardView />);
  await screen.findByText('First ticket');
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
