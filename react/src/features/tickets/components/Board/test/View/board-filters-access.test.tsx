import './setup';
import { renderSelectedProject } from './helpers';
import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import * as api from '../../../../api/ticketApi';
import { responseTicket } from '../../../../api/test/ticketFixture';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useTicketStore } from '../../../../store/useTicketStore';
import * as projectApi from '@/features/tickets/api/projectApi';

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
      attendanceRole: 'employee',
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
