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
import { useTicketStore } from '../../../../store/useTicketStore';
import * as projectApi from '@/features/tickets/api/projectApi';

const recoveryMember = {
  id: '7',
  name: 'Tester',
  email: 'tester@example.com',
  role: 'leader' as const,
  permission: 'write' as const,
};

it('recovers member authority on the same project after a failed initial lookup', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  vi.mocked(projectApi.fetchProjectMembers)
    .mockRejectedValueOnce(new Error('membership unavailable'))
    .mockResolvedValueOnce([recoveryMember]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  await renderSelectedProject();
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'membership unavailable',
  );
  expect(
    screen.queryByRole('button', { name: '+ チケット作成' }),
  ).not.toBeInTheDocument();
  fireEvent.click(
    screen.getByRole('button', { name: 'メンバーと権限を再取得' }),
  );
  await screen.findByRole('button', { name: '+ チケット作成' });
  expect(
    screen.getByRole('button', { name: 'メンバー管理' }),
  ).toBeInTheDocument();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(screen.getByRole('combobox', { name: 'プロジェクト' })).toHaveValue(
    '1',
  );
});

it('retains the retry action after another member lookup failure', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  vi.mocked(projectApi.fetchProjectMembers)
    .mockRejectedValueOnce(new Error('first failure'))
    .mockRejectedValueOnce(new Error('retry failure'));
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  await renderSelectedProject();
  await screen.findByText('first failure');
  fireEvent.click(
    screen.getByRole('button', { name: 'メンバーと権限を再取得' }),
  );
  expect(await screen.findByRole('alert')).toHaveTextContent('retry failure');
  expect(
    screen.getByRole('button', { name: 'メンバーと権限を再取得' }),
  ).toBeEnabled();
  expect(
    screen.queryByRole('button', { name: '+ チケット作成' }),
  ).not.toBeInTheDocument();
});

it('ignores a late member response from dialog close after switching projects', async () => {
  let resolveOld!: (members: (typeof recoveryMember)[]) => void;
  const oldResponse = new Promise<(typeof recoveryMember)[]>((resolve) => {
    resolveOld = resolve;
  });
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  vi.mocked(projectApi.fetchProjects).mockResolvedValue([
    { id: '1', name: 'General', projectKey: 'GEN', boardVersion: 3 },
    { id: '2', name: 'Design', projectKey: 'DSN', boardVersion: 3 },
  ]);
  vi.mocked(projectApi.fetchProjectMembers)
    .mockResolvedValueOnce([recoveryMember])
    .mockResolvedValueOnce([recoveryMember])
    .mockReturnValueOnce(oldResponse)
    .mockResolvedValueOnce([
      { ...recoveryMember, role: 'member', permission: 'read' },
    ]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  await renderSelectedProject();
  fireEvent.click(await screen.findByRole('button', { name: 'メンバー管理' }));
  const dialog = await screen.findByRole('dialog');
  await within(dialog).findByRole('combobox', { name: 'Tester の権限' });
  fireEvent.click(within(dialog).getByRole('button', { name: '閉じる' }));
  fireEvent.change(screen.getByRole('combobox', { name: 'プロジェクト' }), {
    target: { value: '2' },
  });
  await waitFor(() =>
    expect(projectApi.fetchProjectMembers).toHaveBeenLastCalledWith('2'),
  );
  await act(async () => {
    resolveOld([recoveryMember]);
    await oldResponse;
  });
  expect(screen.getByRole('combobox', { name: 'プロジェクト' })).toHaveValue(
    '2',
  );
  expect(
    screen.queryByRole('button', { name: '+ チケット作成' }),
  ).not.toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: 'メンバー管理' }),
  ).not.toBeInTheDocument();
});

it('does not clear a project list error when a pending member lookup succeeds', async () => {
  let resolveMembers!: (members: (typeof recoveryMember)[]) => void;
  const membersResponse = new Promise<(typeof recoveryMember)[]>((resolve) => {
    resolveMembers = resolve;
  });
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  vi.mocked(projectApi.fetchProjectMembers).mockReturnValueOnce(
    membersResponse,
  );
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  await renderSelectedProject();
  await waitFor(() =>
    expect(screen.getByRole('combobox', { name: 'プロジェクト' })).toHaveValue(
      '1',
    ),
  );
  fireEvent.click(
    screen.getByRole('button', { name: 'プロジェクト一覧・作成' }),
  );
  vi.mocked(projectApi.fetchProjects).mockRejectedValueOnce(
    new Error('project list unavailable'),
  );
  fireEvent.click(screen.getByRole('button', { name: '一覧を再取得' }));
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'project list unavailable',
  );
  await act(async () => {
    resolveMembers([recoveryMember]);
    await membersResponse;
  });
  expect(screen.getByRole('alert')).toHaveTextContent(
    'project list unavailable',
  );
});
