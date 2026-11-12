import './setup';
import { expect, it, vi } from 'vitest';
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import * as api from '../../../../api/ticketApi';
import { useTicketStore } from '../../../../store/useTicketStore';
import { TicketBoardView } from '../../View';
import * as projectApi from '@/features/tickets/api/projectApi';

it('全体ボードで閲覧権限のみのプロジェクトを選ぶとチケットを作成できない', async () => {
  vi.mocked(projectApi.fetchProjectMembers).mockResolvedValue([
    {
      id: '7',
      name: 'Tester',
      email: null,
      role: 'member',
      permission: 'read',
    },
  ]);
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  render(<TicketBoardView />);
  fireEvent.click(
    await screen.findByRole('button', { name: '+ チケット作成' }),
  );
  const dialog = screen.getByRole('dialog');
  fireEvent.change(within(dialog).getByLabelText('作成先プロジェクト'), {
    target: { value: '1' },
  });
  fireEvent.change(within(dialog).getByLabelText('タイトル'), {
    target: { value: 'Read-only draft' },
  });
  await within(dialog).findByText(/このプロジェクトは閲覧のみ/);
  expect(within(dialog).getByRole('button', { name: '保存' })).toBeDisabled();
  expect(api.createTicket).not.toHaveBeenCalled();
});

it('作成画面で権限取得に失敗しても、下書きを保って再取得できる', async () => {
  vi.mocked(projectApi.fetchProjectMembers)
    .mockRejectedValueOnce(new Error('lookup failed'))
    .mockResolvedValue([
      {
        id: '7',
        name: 'Tester',
        email: null,
        role: 'member',
        permission: 'write',
      },
    ]);
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  render(<TicketBoardView />);
  fireEvent.click(
    await screen.findByRole('button', { name: '+ チケット作成' }),
  );
  const dialog = screen.getByRole('dialog');
  fireEvent.change(within(dialog).getByLabelText('タイトル'), {
    target: { value: 'Retry preserved draft' },
  });
  fireEvent.change(within(dialog).getByLabelText('作成先プロジェクト'), {
    target: { value: '1' },
  });
  await within(dialog).findByText('lookup failed');
  expect(within(dialog).getByRole('button', { name: '保存' })).toBeDisabled();
  fireEvent.click(
    within(dialog).getByRole('button', { name: 'メンバーと権限を再取得' }),
  );
  await waitFor(() =>
    expect(within(dialog).getByRole('button', { name: '保存' })).toBeEnabled(),
  );
  expect(within(dialog).getByLabelText('タイトル')).toHaveValue(
    'Retry preserved draft',
  );
});

it('全体ボードから既存のプロジェクト作成画面を直接開く', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  render(<TicketBoardView />);
  fireEvent.click(screen.getByRole('button', { name: '+ プロジェクト作成' }));
  expect(await screen.findByLabelText('プロジェクト名')).toHaveFocus();
});
