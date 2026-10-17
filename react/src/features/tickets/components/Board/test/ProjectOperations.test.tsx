import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import * as api from '../../../api/projectApi';
import ProjectOperations from '../ProjectOperations';

vi.mock('../../../api/projectApi', () => ({
  archiveProject: vi.fn(),
  renameProject: vi.fn(),
  restoreProject: vi.fn(),
}));
const project = {
  id: '1',
  name: 'General',
  projectKey: 'GEN',
  boardVersion: 3,
  archivedAt: null,
};
beforeEach(() => vi.resetAllMocks());

it('renames through the existing API while retaining the Project key', async () => {
  const changed = { ...project, name: 'Renamed' };
  vi.mocked(api.renameProject).mockResolvedValue(changed);
  const onChanged = vi.fn();
  render(
    <ProjectOperations
      project={project}
      canRename
      onChanged={onChanged}
      onPendingChange={vi.fn()}
    />,
  );
  fireEvent.change(screen.getByLabelText('プロジェクト名を変更'), {
    target: { value: 'Renamed' },
  });
  fireEvent.click(screen.getByRole('button', { name: '名前を保存' }));
  await waitFor(() => expect(onChanged).toHaveBeenCalledWith(changed));
  expect(api.renameProject).toHaveBeenCalledWith('1', 'Renamed');
});

it('requires explicit archive confirmation and preserves rejected operations for retry', async () => {
  vi.mocked(api.archiveProject).mockRejectedValue(
    new Error('未完了のチケットがあります'),
  );
  const onChanged = vi.fn();
  render(
    <ProjectOperations
      project={project}
      canRename={false}
      onChanged={onChanged}
      onPendingChange={vi.fn()}
    />,
  );
  expect(
    screen.queryByLabelText('プロジェクト名を変更'),
  ).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'プロジェクトを終了' }));
  expect(api.archiveProject).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: '終了を確定' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('未完了');
  expect(onChanged).not.toHaveBeenCalled();
  vi.mocked(api.archiveProject).mockResolvedValue({
    ...project,
    archivedAt: '2026-10-13T00:00:00Z',
  });
  fireEvent.click(screen.getByRole('button', { name: '終了を確定' }));
  await waitFor(() =>
    expect(onChanged).toHaveBeenCalledWith(
      expect.objectContaining({ archivedAt: '2026-10-13T00:00:00Z' }),
    ),
  );
});

it('restores archived Projects and blocks a duplicate request until it completes', async () => {
  let complete!: (value: typeof project) => void;
  vi.mocked(api.restoreProject).mockImplementation(
    () =>
      new Promise((resolve) => {
        complete = resolve;
      }),
  );
  const onChanged = vi.fn();
  const pending = vi.fn();
  render(
    <ProjectOperations
      project={{ ...project, archivedAt: '2026-10-13T00:00:00Z' }}
      canRename={false}
      onChanged={onChanged}
      onPendingChange={pending}
    />,
  );
  const restore = screen.getByRole('button', { name: 'プロジェクトを復元' });
  fireEvent.click(restore);
  fireEvent.click(restore);
  expect(api.restoreProject).toHaveBeenCalledTimes(1);
  expect(restore).toBeDisabled();
  complete(project);
  await waitFor(() => expect(onChanged).toHaveBeenCalledWith(project));
  expect(pending.mock.calls).toEqual([[true], [false]]);
});
