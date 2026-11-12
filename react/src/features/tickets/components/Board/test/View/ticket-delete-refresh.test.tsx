import './setup';
import { renderSelectedProject } from './helpers';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import * as api from '../../../../api/ticketApi';
import { responseTicket } from '../../../../api/test/ticketFixture';
import { useTicketStore } from '../../../../store/useTicketStore';
import * as projectApi from '@/features/tickets/api/projectApi';

it('詳細画面で確認してからチケットを削除する', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets)
    .mockResolvedValueOnce([ticket])
    .mockResolvedValue([]);
  vi.mocked(api.deleteTicket).mockResolvedValue(undefined);
  vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' });
  expect(
    screen.queryByRole('button', { name: '削除' }),
  ).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'TICK-1 の詳細を開く' }));
  fireEvent.click(await screen.findByRole('button', { name: '削除' }));

  await waitFor(() => expect(api.deleteTicket).toHaveBeenCalledWith('1'));
  await waitFor(() =>
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
  );
});

it('削除に失敗したら詳細画面を開いたままにしてエラーを表示する', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([api.toTicket(responseTicket)]);
  vi.mocked(api.deleteTicket).mockRejectedValue(new Error('delete failed'));
  vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' });
  fireEvent.click(screen.getByRole('button', { name: 'TICK-1 の詳細を開く' }));
  fireEvent.click(await screen.findByRole('button', { name: '削除' }));

  expect(await screen.findByRole('alert')).toHaveTextContent('delete failed');
  expect(
    screen.getByRole('heading', { name: 'チケット詳細' }),
  ).toBeInTheDocument();
});

it('ボードでドラッグを終えてもチケット詳細を開かない', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets).mockResolvedValue([ticket]);
  vi.mocked(api.moveTicket).mockResolvedValue({ ticket, boardVersion: 4 });
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' });
  fireEvent.click(screen.getByText('drop DONE'));

  await waitFor(() => expect(api.moveTicket).toHaveBeenCalled());
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});

it('プロジェクト再取得に失敗しても、保存済みチケットの作成を失敗として扱わない', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets)
    .mockResolvedValueOnce([])
    .mockResolvedValue([ticket]);
  vi.mocked(api.createTicket).mockClear().mockResolvedValue(ticket);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  await renderSelectedProject();
  fireEvent.click(
    await screen.findByRole('button', { name: '+ チケット作成' }),
  );
  vi.mocked(projectApi.fetchProjects).mockRejectedValueOnce(
    new Error('一覧更新失敗'),
  );
  fireEvent.change(screen.getByLabelText('タイトル'), {
    target: { value: ticket.title },
  });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  await waitFor(() =>
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
  );
  expect(await screen.findByRole('alert')).toHaveTextContent('一覧更新失敗');
  expect(useTicketStore.getState().tickets).toContainEqual(ticket);
  expect(api.createTicket).toHaveBeenCalledTimes(1);
});

it('プロジェクト再取得に失敗しても、削除に成功したチケットの詳細を閉じる', async () => {
  const ticket = api.toTicket(responseTicket);
  vi.mocked(api.fetchTickets)
    .mockResolvedValueOnce([ticket])
    .mockResolvedValue([]);
  vi.mocked(api.deleteTicket).mockResolvedValue(undefined);
  vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  await renderSelectedProject();
  fireEvent.click(
    await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' }),
  );
  const remove = await screen.findByRole('button', { name: '削除' });
  vi.mocked(projectApi.fetchProjects).mockRejectedValueOnce(
    new Error('metadata unavailable'),
  );
  fireEvent.click(remove);
  await waitFor(() =>
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
  );
  expect(screen.getByRole('alert')).toHaveTextContent('metadata unavailable');
  expect(useTicketStore.getState().tickets).toHaveLength(0);
  expect(
    screen.queryByRole('button', { name: 'TICK-1 の詳細を開く' }),
  ).not.toBeInTheDocument();
});
