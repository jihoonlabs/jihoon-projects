import './setup';
import { renderSelectedProject } from './helpers';
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import * as api from '../../../../api/ticketApi';
import { responseTicket } from '../../../../api/test/ticketFixture';
import { useTicketStore } from '../../../../store/useTicketStore';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import * as projectApi from '@/features/tickets/api/projectApi';
import { TicketBoardView } from '../../View';

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

const assertFailedDragRemainsVisibleAfterRevalidation = async (
  projectRefreshFails: boolean,
) => {
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
};

it('keeps the failed drag visible when project refresh succeeds and clears it on retry', () =>
  assertFailedDragRemainsVisibleAfterRevalidation(false));

it('keeps the failed drag visible when project refresh fails and clears it on retry', () =>
  assertFailedDragRemainsVisibleAfterRevalidation(true));

const assertNewerProjectListFailureSurvivesDelayedDrag = async (
  switchProject: boolean,
) => {
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
};

it('keeps a newer project list failure after delayed drag success in the same project', () =>
  assertNewerProjectListFailureSurvivesDelayedDrag(false));

it('keeps a newer project list failure after delayed drag success and project switch', () =>
  assertNewerProjectListFailureSurvivesDelayedDrag(true));

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

it('restores the selected project after a board move and page reload', async () => {
  window.history.replaceState(
    window.history.state,
    '',
    '/tickets?tab=board#kanban',
  );
  const baseTicket = api.toTicket(responseTicket);
  const otherProjectTicket = {
    ...baseTicket,
    id: 'other',
    projectId: '1',
    title: 'General ticket',
  };
  const selectedProjectTicket = {
    ...baseTicket,
    id: '1',
    projectId: '2',
    title: 'Project two ticket',
  };
  vi.mocked(projectApi.fetchProjects).mockResolvedValue([
    { id: '1', name: 'General', projectKey: 'GEN', boardVersion: 3 },
    { id: '2', name: 'Other', projectKey: 'OTH', boardVersion: 8 },
  ]);
  vi.mocked(api.fetchTickets).mockResolvedValue([
    otherProjectTicket,
    selectedProjectTicket,
  ]);
  vi.mocked(api.moveTicket).mockResolvedValue({
    ticket: { ...selectedProjectTicket, status: 'DONE' },
    boardVersion: 9,
  });
  useAuthStore.setState({
    user: { ...useAuthStore.getState().user!, role: 'admin' },
  });
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  const firstPage = render(<TicketBoardView />);
  const projectSelect = await screen.findByRole('combobox', {
    name: 'プロジェクト',
  });
  await screen.findByRole('option', { name: 'Other' });
  fireEvent.change(projectSelect, { target: { value: '2' } });
  expect(await screen.findByText('Project two ticket')).toBeInTheDocument();
  expect(screen.queryByText('General ticket')).not.toBeInTheDocument();
  expect(new URL(window.location.href).searchParams.get('project')).toBe('2');
  expect(new URL(window.location.href).searchParams.get('tab')).toBe('board');
  expect(new URL(window.location.href).hash).toBe('#kanban');

  fireEvent.click(screen.getByText('drop DONE'));
  await waitFor(() =>
    expect(api.moveTicket).toHaveBeenCalledWith('1', 'DONE', 0, 8),
  );

  firstPage.unmount();
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  render(<TicketBoardView />);
  const restoredProjectSelect = await screen.findByRole('combobox', {
    name: 'プロジェクト',
  });

  await waitFor(() => expect(restoredProjectSelect).toHaveValue('2'));
  expect(await screen.findByText('Project two ticket')).toBeInTheDocument();
  expect(screen.queryByText('General ticket')).not.toBeInTheDocument();
});
