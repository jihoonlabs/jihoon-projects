import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { createProject } from '../../../api/projectApi';
import ProjectDirectory from '../ProjectDirectory';

vi.mock('../../../api/projectApi', () => ({ createProject: vi.fn() }));
const projects = [
  { id: '1', name: 'General', projectKey: 'GEN', boardVersion: 1 },
  { id: '2', name: 'Product', projectKey: 'PRD', boardVersion: 1 },
];
beforeEach(() => vi.resetAllMocks());

it('アクセス可能なプロジェクトを表示し、キーで検索してからボードを切り替える', () => {
  const onSelect = vi.fn();
  render(
    <ProjectDirectory
      loading={false}
      projects={projects}
      selectedProjectId="1"
      onSelect={onSelect}
      onCreated={vi.fn()}
    />,
  );
  expect(screen.getByRole('button', { name: /General.*GEN/ })).toHaveAttribute(
    'aria-pressed',
    'true',
  );
  fireEvent.change(screen.getByRole('searchbox'), {
    target: { value: ' prd ' },
  });
  expect(
    screen.queryByRole('button', { name: /General.*GEN/ }),
  ).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /Product.*PRD/ }));
  expect(onSelect).toHaveBeenCalledWith('2');
});

it('作成結果が返るまで重複送信を防ぎ、作成されたプロジェクトを選択する', async () => {
  let complete!: (project: (typeof projects)[0]) => void;
  vi.mocked(createProject).mockImplementation(
    () =>
      new Promise((resolve) => {
        complete = resolve;
      }),
  );
  const onCreated = vi.fn();
  render(
    <ProjectDirectory
      loading={false}
      projects={[]}
      selectedProjectId=""
      onSelect={vi.fn()}
      onCreated={onCreated}
    />,
  );
  fireEvent.change(screen.getByLabelText('プロジェクト名'), {
    target: { value: 'Product' },
  });
  const form = screen
    .getByRole('button', { name: 'プロジェクトを作成' })
    .closest('form')!;
  fireEvent.submit(form);
  fireEvent.submit(form);
  expect(createProject).toHaveBeenCalledTimes(1);
  expect(screen.getByRole('button', { name: '作成中...' })).toBeDisabled();
  complete(projects[1]);
  await waitFor(() => expect(onCreated).toHaveBeenCalledWith(projects[1]));
  expect(screen.getByLabelText('プロジェクト名')).toHaveValue('');
});

it('作成に失敗しても入力を保持し、再試行できる', async () => {
  vi.mocked(createProject)
    .mockRejectedValueOnce(new Error('作成拒否'))
    .mockResolvedValueOnce(projects[1]);
  const onCreated = vi.fn();
  render(
    <ProjectDirectory
      loading={false}
      projects={[]}
      selectedProjectId=""
      onSelect={vi.fn()}
      onCreated={onCreated}
    />,
  );
  fireEvent.change(screen.getByLabelText('プロジェクト名'), {
    target: { value: 'Product' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'プロジェクトを作成' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('作成拒否');
  expect(screen.getByLabelText('プロジェクト名')).toHaveValue('Product');
  expect(onCreated).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'プロジェクトを作成' }));
  await waitFor(() => expect(onCreated).toHaveBeenCalledWith(projects[1]));
});

it('初回のプロジェクト一覧取得が終わるまで作成を受け付けない', () => {
  render(
    <ProjectDirectory
      loading
      projects={[]}
      selectedProjectId=""
      onSelect={vi.fn()}
      onCreated={vi.fn()}
    />,
  );
  fireEvent.change(screen.getByLabelText('プロジェクト名'), {
    target: { value: 'Product' },
  });
  const button = screen.getByRole('button', { name: 'プロジェクトを作成' });
  expect(button).toBeDisabled();
  fireEvent.submit(button.closest('form')!);
  expect(createProject).not.toHaveBeenCalled();
});
