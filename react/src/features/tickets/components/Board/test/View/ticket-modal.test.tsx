import './setup';
import { renderSelectedProject } from './helpers';
import {
  act,
  fireEvent,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import * as api from '../../../../api/ticketApi';
import { TicketApiError } from '../../../../api/ticketApi';
import { responseTicket } from '../../../../api/test/ticketFixture';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useTicketStore } from '../../../../store/useTicketStore';
import * as projectApi from '@/features/tickets/api/projectApi';

it('作成に失敗したら作成画面を開いたままにして保存エラーを表示する', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  vi.mocked(api.createTicket).mockRejectedValue(new Error('create failed'));
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  fireEvent.click(
    await screen.findByRole('button', { name: '+ チケット作成' }),
  );
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

it('セッション切れの後に再認証しても、チケットの下書きを保って作成を再試行できる', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  vi.mocked(api.createTicket)
    .mockImplementationOnce(async () => {
      useAuthStore.getState().expireSession();
      throw new TicketApiError('session expired', 401);
    })
    .mockResolvedValueOnce(api.toTicket(responseTicket));
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  fireEvent.click(
    await screen.findByRole('button', { name: '+ チケット作成' }),
  );
  fireEvent.change(screen.getByLabelText('タイトル'), {
    target: { value: 'Retry after reauthentication' },
  });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));

  await within(screen.getByRole('dialog')).findByRole('alert');
  expect(useAuthStore.getState().sessionExpired).toBe(true);
  expect(screen.getByLabelText('タイトル')).toHaveValue(
    'Retry after reauthentication',
  );

  act(() => useAuthStore.getState().login(useAuthStore.getState().user!));
  await waitFor(() =>
    expect(screen.getByRole('button', { name: '保存' })).toBeEnabled(),
  );
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  await waitFor(() => expect(api.createTicket).toHaveBeenCalledTimes(2));
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});

it('保存中に背景をクリックしてもダイアログを閉じない', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  let resolveCreate!: (value: ReturnType<typeof api.toTicket>) => void;
  vi.mocked(api.createTicket).mockReturnValue(
    new Promise((resolve) => {
      resolveCreate = resolve;
    }),
  );
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  fireEvent.click(
    await screen.findByRole('button', { name: '+ チケット作成' }),
  );
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

it('編集に失敗したら編集画面を開いたままにして保存エラーを表示する', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
  vi.mocked(api.updateTicket).mockRejectedValue(new Error('update failed'));
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' });
  fireEvent.click(screen.getByRole('button', { name: 'TICK-1 の詳細を開く' }));
  await screen.findByRole('heading', { name: 'チケット詳細' });
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

it('タイトルをキーボードで操作して詳細を開き、閉じたらフォーカスを戻す', async () => {
  const user = userEvent.setup();
  vi.mocked(api.fetchTickets).mockResolvedValue([api.toTicket(responseTicket)]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  const title = await screen.findByRole('button', {
    name: 'TICK-1 の詳細を開く',
  });
  title.focus();
  await user.keyboard('{Enter}');

  const heading = await screen.findByRole('heading', { name: 'チケット詳細' });
  expect(document.activeElement).toBe(heading);
  fireEvent.click(screen.getByRole('button', { name: '閉じる' }));
  await waitFor(() => expect(document.activeElement).toBe(title));
});

it('詳細画面から編集して保存し、更新済みの詳細に戻る', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
  vi.mocked(api.updateTicket).mockResolvedValue({
    ...ticket,
    title: 'Saved title',
    description: 'Saved description',
    priority: 'HIGH',
  });
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' });
  fireEvent.click(screen.getByRole('button', { name: 'TICK-1 の詳細を開く' }));
  fireEvent.click(await screen.findByRole('button', { name: '編集' }));
  fireEvent.change(screen.getByLabelText('タイトル'), {
    target: { value: 'Saved title' },
  });
  fireEvent.change(screen.getByLabelText('説明'), {
    target: { value: 'Saved description' },
  });
  fireEvent.change(screen.getByLabelText('優先度'), {
    target: { value: 'HIGH' },
  });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));

  await waitFor(() =>
    expect(
      screen.getByRole('heading', { name: 'チケット詳細' }),
    ).toBeInTheDocument(),
  );
  expect(screen.getByText('Saved title')).toBeInTheDocument();
  expect(screen.getByText('Saved description')).toBeInTheDocument();
  expect(api.updateTicket).toHaveBeenCalledWith(
    '1',
    expect.objectContaining({ title: 'Saved title', priority: 'HIGH' }),
  );
});

const assertAssigneeCanBeChangedAndRestored = async (
  initialAssignee: string,
) => {
  const ticket = api.toTicket({
    ...responseTicket,
    assignee: initialAssignee
      ? { id: 7, name: 'Tester', avatar_url: null }
      : null,
  });
  vi.mocked(projectApi.fetchProjectMembers).mockResolvedValue([
    {
      id: '7',
      name: 'Tester',
      email: null,
      role: 'member',
      permission: 'write',
    },
    {
      id: '8',
      name: 'Other',
      email: null,
      role: 'member',
      permission: 'write',
    },
  ]);
  vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
  vi.mocked(api.updateTicket).mockImplementation(async (_id, input) => ({
    ...ticket,
    assignee: input.assigneeId
      ? { id: input.assigneeId, name: 'Member' }
      : null,
  }));
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  await renderSelectedProject();
  fireEvent.click(
    await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' }),
  );
  fireEvent.click(await screen.findByRole('button', { name: '編集' }));
  fireEvent.change(screen.getByLabelText('担当者'), {
    target: { value: '8' },
  });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  await screen.findByRole('heading', { name: 'チケット詳細' });

  fireEvent.click(await screen.findByRole('button', { name: '編集' }));
  fireEvent.change(screen.getByLabelText('担当者'), {
    target: { value: initialAssignee },
  });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  await screen.findByRole('heading', { name: 'チケット詳細' });
  expect(api.updateTicket).toHaveBeenLastCalledWith(
    '1',
    expect.objectContaining({ assigneeId: initialAssignee || null }),
  );
  expect(useTicketStore.getState().tickets[0].assignee?.id ?? '').toBe(
    initialAssignee,
  );
};

it('同じ詳細画面で2回保存し、担当者を元のメンバーに戻せる', () =>
  assertAssigneeCanBeChangedAndRestored('7'));

it('同じ詳細画面で2回保存し、担当者を未設定に戻せる', () =>
  assertAssigneeCanBeChangedAndRestored(''));
