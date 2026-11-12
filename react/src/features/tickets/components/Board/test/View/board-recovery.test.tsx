import './setup';
import { renderSelectedProject } from './helpers';
import { expect, it, vi } from 'vitest';
import { act, fireEvent, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import * as api from '../../../../api/ticketApi';
import { responseTicket } from '../../../../api/test/ticketFixture';
import { useTicketStore } from '../../../../store/useTicketStore';
import * as projectApi from '@/features/tickets/api/projectApi';

it('手動でステータスを更新した後のプロジェクト再取得エラーを処理する', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
  vi.mocked(api.updateTicketStatus).mockResolvedValue({
    ...ticket,
    status: 'DONE',
  });
  vi.mocked(projectApi.fetchProjects)
    .mockResolvedValueOnce([
      { id: '1', name: 'General', projectKey: 'GEN', boardVersion: 3 },
    ])
    .mockRejectedValueOnce(new Error('project refresh failed'));
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  fireEvent.change(
    await screen.findByRole('combobox', { name: 'First ticket のステータス' }),
    {
      target: { value: 'DONE' },
    },
  );

  expect(await screen.findByRole('alert')).toHaveTextContent(
    'project refresh failed',
  );
});

it('手動のステータス更新エラーを表示し続け、再試行できる', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
  vi.mocked(api.updateTicketStatus)
    .mockRejectedValueOnce(new Error('status failed'))
    .mockResolvedValueOnce({ ...ticket, status: 'DONE' });
  vi.mocked(api.fetchTickets)
    .mockResolvedValueOnce([ticket])
    .mockResolvedValue([{ ...ticket, status: 'DONE' }]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  const status = await screen.findByRole('combobox', {
    name: 'First ticket のステータス',
  });
  const user = userEvent.setup();
  await user.selectOptions(status, 'DONE');
  expect(await screen.findByRole('alert')).toHaveTextContent('status failed');
  expect(status).toHaveValue('TODO');

  await user.selectOptions(status, 'DONE');
  await waitFor(() => expect(api.updateTicketStatus).toHaveBeenCalledTimes(2));
  expect(useTicketStore.getState().tickets[0].status).toBe('DONE');
  await waitFor(() =>
    expect(
      screen.getByRole('combobox', { name: 'First ticket のステータス' }),
    ).toHaveValue('DONE'),
  );
});

it('チケット一覧の初回取得に失敗してもボードから再試行できる', async () => {
  vi.mocked(api.fetchTickets)
    .mockRejectedValueOnce(new Error('ticket list unavailable'))
    .mockResolvedValueOnce([api.toTicket(responseTicket)]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  await renderSelectedProject();
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'ticket list unavailable',
  );
  fireEvent.click(screen.getByRole('button', { name: 'チケット一覧を再取得' }));
  await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' });
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

it('再取得に失敗しても既存のチケット一覧を保持し、再試行できる', async () => {
  vi.mocked(api.fetchTickets)
    .mockRejectedValueOnce(new Error('first list failure'))
    .mockRejectedValueOnce(new Error('retry list failure'));
  const ticket = api.toTicket(responseTicket);
  useTicketStore.setState({ tickets: [ticket], error: null, isLoading: false });
  await renderSelectedProject();
  await screen.findByText('first list failure');
  fireEvent.click(screen.getByRole('button', { name: 'チケット一覧を再取得' }));
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'retry list failure',
  );
  expect(
    screen.getByRole('button', { name: 'TICK-1 の詳細を開く' }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole('button', { name: 'チケット一覧を再取得' }),
  ).toBeEnabled();
});

it('チケット一覧の再取得中は処理中と伝え、重複リクエストを受け付けない', async () => {
  let resolveList!: (tickets: ReturnType<typeof api.toTicket>[]) => void;
  const pendingList = new Promise<ReturnType<typeof api.toTicket>[]>(
    (resolve) => {
      resolveList = resolve;
    },
  );
  vi.mocked(api.fetchTickets)
    .mockRejectedValueOnce(new Error('list failed'))
    .mockReturnValueOnce(pendingList);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  await renderSelectedProject();
  await screen.findByText('list failed');
  fireEvent.click(screen.getByRole('button', { name: 'チケット一覧を再取得' }));
  expect(screen.getByText('チケット一覧を更新中...')).toHaveAttribute(
    'role',
    'status',
  );
  expect(
    screen.queryByRole('button', { name: 'チケット一覧を再取得' }),
  ).not.toBeInTheDocument();
  await act(async () => {
    resolveList([api.toTicket(responseTicket)]);
    await pendingList;
  });
  expect(screen.queryByText('チケット一覧を更新中...')).not.toBeInTheDocument();
  expect(
    screen.getByRole('button', { name: 'TICK-1 の詳細を開く' }),
  ).toBeInTheDocument();
});
