import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import * as api from '../../../api/projectApi';
import type { ProjectMember } from '../../../types/project';
import ProjectMembersDialog from '../ProjectMembersDialog';

vi.mock('../../../api/projectApi', () => ({
  fetchProjectMembers: vi.fn(),
  addProjectMember: vi.fn(),
  updateProjectMember: vi.fn(),
  removeProjectMember: vi.fn(),
  transferProjectLeader: vi.fn(),
}));
const project = {
  id: '1',
  name: 'General',
  projectKey: 'GEN',
  boardVersion: 3,
};
const members: ProjectMember[] = [
  {
    id: '7',
    name: 'Aki',
    email: 'aki@example.com',
    role: 'leader',
    permission: 'write',
  },
  {
    id: '8',
    name: 'Ren',
    email: 'ren@example.com',
    role: 'member',
    permission: 'read',
  },
];
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(api.fetchProjectMembers).mockResolvedValue(members);
});

it('shows roles without direct edits, keeps the leader and adds only ordinary members', async () => {
  vi.mocked(api.addProjectMember).mockResolvedValue(members[1]);
  render(<ProjectMembersDialog project={project} onClose={vi.fn()} />);
  await screen.findByText(/Aki.*リーダー/);
  expect(
    screen.queryByRole('combobox', { name: /役割/ }),
  ).not.toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: 'Aki をメンバーから削除' }),
  ).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('メールアドレス'), {
    target: { value: 'new@example.com' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'メンバーを追加' }));
  await waitFor(() =>
    expect(api.addProjectMember).toHaveBeenCalledWith('1', {
      email: 'new@example.com',
      role: 'member',
      permission: 'write',
    }),
  );
});

it('uses leader transfer and immediately updates parent permissions even if the reload fails', async () => {
  const leader = { ...members[1], role: 'leader' as const };
  vi.mocked(api.transferProjectLeader).mockResolvedValue(leader);
  const changed = vi.fn();
  render(
    <ProjectMembersDialog
      project={project}
      onMembersChanged={changed}
      onClose={vi.fn()}
    />,
  );
  fireEvent.click(
    await screen.findByRole('button', { name: 'Ren をリーダーにする' }),
  );
  expect(api.transferProjectLeader).not.toHaveBeenCalled();
  vi.mocked(api.fetchProjectMembers).mockRejectedValueOnce(
    new Error('offline'),
  );
  fireEvent.click(
    screen.getByRole('button', { name: 'リーダー引き継ぎを確定' }),
  );
  expect(await screen.findByRole('alert')).toHaveTextContent(
    '変更は保存されました',
  );
  expect(changed).toHaveBeenCalledWith([
    { ...members[0], role: 'member' },
    leader,
  ]);
  expect(api.transferProjectLeader).toHaveBeenCalledWith('1', '8');
  expect(screen.getByRole('combobox', { name: 'Aki の権限' })).toBeDisabled();
  fireEvent.click(screen.getByRole('button', { name: 'メンバー一覧を再取得' }));
  await waitFor(() =>
    expect(screen.queryByRole('alert')).not.toBeInTheDocument(),
  );
  expect(api.transferProjectLeader).toHaveBeenCalledTimes(1);
});

it('locks mutation and dismissal while the save is pending', async () => {
  let complete!: (value: ProjectMember) => void;
  vi.mocked(api.updateProjectMember).mockImplementation(
    () =>
      new Promise((resolve) => {
        complete = resolve;
      }),
  );
  const close = vi.fn();
  render(<ProjectMembersDialog project={project} onClose={close} />);
  const permission = await screen.findByRole('combobox', {
    name: 'Ren の権限',
  });
  fireEvent.change(permission, { target: { value: 'write' } });
  fireEvent.click(screen.getByRole('button', { name: '閉じる' }));
  fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' });
  fireEvent.mouseDown(screen.getByRole('dialog').parentElement!);
  expect(close).not.toHaveBeenCalled();
  expect(permission).toBeDisabled();
  complete({ ...members[1], permission: 'write' });
  await waitFor(() =>
    expect(screen.getByRole('button', { name: '閉じる' })).toBeEnabled(),
  );
});

it('renders a read-only member list after management rights change', async () => {
  render(
    <ProjectMembersDialog
      project={project}
      canManage={false}
      onClose={vi.fn()}
    />,
  );
  await screen.findByText(/Aki.*リーダー/);
  expect(
    screen.queryByRole('button', { name: 'メンバーを追加' }),
  ).not.toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: 'Ren をリーダーにする' }),
  ).not.toBeInTheDocument();
  expect(
    within(screen.getByRole('dialog'))
      .getAllByRole('combobox')
      .every((select) => select.hasAttribute('disabled')),
  ).toBe(true);
});
