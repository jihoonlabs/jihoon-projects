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
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import type { ProjectMember } from '@/features/tickets/types/project';

const recoveryMember: ProjectMember = {
  id: '7',
  name: 'Tester',
  email: 'tester@example.com',
  role: 'leader',
  permission: 'write',
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

it('ignores a pending retry failure after switching projects', async () => {
  let rejectRetry!: (reason: Error) => void;
  const retryResponse = new Promise<(typeof recoveryMember)[]>((_, reject) => {
    rejectRetry = reject;
  });
  vi.mocked(projectApi.fetchProjects).mockResolvedValue([
    { id: '1', name: 'General', projectKey: 'GEN', boardVersion: 3 },
    { id: '2', name: 'Design', projectKey: 'DSN', boardVersion: 3 },
  ]);
  vi.mocked(projectApi.fetchProjectMembers)
    .mockRejectedValueOnce(new Error('first failure'))
    .mockReturnValueOnce(retryResponse)
    .mockResolvedValueOnce([{ ...recoveryMember, permission: 'read' }]);
  await renderSelectedProject();
  await screen.findByText('first failure');
  fireEvent.click(
    screen.getByRole('button', { name: 'メンバーと権限を再取得' }),
  );
  await waitFor(() =>
    expect(projectApi.fetchProjectMembers).toHaveBeenCalledTimes(2),
  );
  fireEvent.change(screen.getByRole('combobox', { name: 'プロジェクト' }), {
    target: { value: '2' },
  });
  await waitFor(() =>
    expect(projectApi.fetchProjectMembers).toHaveBeenLastCalledWith('2'),
  );
  await act(async () => {
    rejectRetry(new Error('old retry failure'));
    await retryResponse.catch(() => undefined);
  });
  expect(screen.queryByText('old retry failure')).not.toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: '+ チケット作成' }),
  ).not.toBeInTheDocument();
});

it('ignores an old session member response while the new session lookup is pending', async () => {
  let resolveOld!: (members: (typeof recoveryMember)[]) => void;
  const oldResponse = new Promise<(typeof recoveryMember)[]>((resolve) => {
    resolveOld = resolve;
  });
  let resolveNew!: (members: (typeof recoveryMember)[]) => void;
  const newResponse = new Promise<(typeof recoveryMember)[]>((resolve) => {
    resolveNew = resolve;
  });
  vi.mocked(projectApi.fetchProjectMembers)
    .mockReturnValueOnce(oldResponse)
    .mockReturnValueOnce(newResponse);
  await renderSelectedProject();
  await waitFor(() =>
    expect(projectApi.fetchProjectMembers).toHaveBeenCalledTimes(1),
  );
  act(() => {
    useAuthStore.setState((state) => ({
      sessionRevision: state.sessionRevision + 1,
    }));
  });
  await waitFor(() =>
    expect(projectApi.fetchProjectMembers).toHaveBeenCalledTimes(2),
  );
  await act(async () => {
    resolveOld([recoveryMember]);
    await oldResponse;
  });
  expect(
    screen.queryByRole('button', { name: 'メンバー管理' }),
  ).not.toBeInTheDocument();
  await act(async () => {
    resolveNew([{ ...recoveryMember, permission: 'read' }]);
    await newResponse;
  });
  expect(
    screen.queryByRole('button', { name: '+ チケット作成' }),
  ).not.toBeInTheDocument();
});

it('discards a member dialog refresh started before same-account reauthentication', async () => {
  const addedMember: ProjectMember = {
    id: '8',
    name: 'New member',
    email: 'new@example.com',
    role: 'member',
    permission: 'read',
  };
  let resolveDialogRefresh!: (members: ProjectMember[]) => void;
  const dialogRefresh = new Promise<ProjectMember[]>((resolve) => {
    resolveDialogRefresh = resolve;
  });
  let resolveBoardLookup!: (members: ProjectMember[]) => void;
  const boardLookup = new Promise<ProjectMember[]>((resolve) => {
    resolveBoardLookup = resolve;
  });
  vi.mocked(projectApi.fetchProjectMembers)
    .mockResolvedValueOnce([recoveryMember])
    .mockResolvedValueOnce([recoveryMember])
    .mockReturnValueOnce(dialogRefresh)
    .mockReturnValueOnce(boardLookup);
  vi.mocked(projectApi.addProjectMember).mockResolvedValue(addedMember);

  await renderSelectedProject();
  fireEvent.click(await screen.findByRole('button', { name: 'メンバー管理' }));
  const dialog = within(screen.getByRole('dialog'));
  const email = dialog.getByRole('textbox', { name: 'メールアドレス' });
  await waitFor(() => expect(email).toBeEnabled());
  fireEvent.change(email, { target: { value: addedMember.email } });
  fireEvent.click(dialog.getByRole('button', { name: 'メンバーを追加' }));
  await waitFor(() =>
    expect(projectApi.fetchProjectMembers).toHaveBeenCalledTimes(3),
  );
  // 基準: 再ログイン前は write 権限で生成ボタンが表示されていること。
  // これがないと、後段の「非表示」単言が常に成立してしまう。
  expect(
    await screen.findByRole('button', { name: '+ チケット作成' }),
  ).toBeInTheDocument();

  const auth = useAuthStore.getState();
  const user = auth.user!;
  act(() => auth.expireSession());
  act(() => auth.login(user));
  await waitFor(() =>
    expect(projectApi.fetchProjectMembers).toHaveBeenCalledTimes(4),
  );
  // 新セッションのプロジェクト一覧の更新が終わってから、古い応答を完了させる。
  await waitFor(() =>
    expect(projectApi.fetchProjects).toHaveBeenCalledTimes(2),
  );

  // 新セッションの read 応答を先に完了させる。
  await act(async () => {
    resolveBoardLookup([{ ...recoveryMember, permission: 'read' }]);
    await boardLookup;
  });
  expect(
    await screen.findByRole('button', { name: 'メンバー管理' }),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: '+ チケット作成' }),
  ).not.toBeInTheDocument();

  // その後で、再ログイン前に始まった write 応答を完了させても権限は上書きされない。
  await act(async () => {
    resolveDialogRefresh([recoveryMember, addedMember]);
    await dialogRefresh;
  });
  expect(
    screen.getByRole('button', { name: 'メンバー管理' }),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: '+ チケット作成' }),
  ).not.toBeInTheDocument();
});
