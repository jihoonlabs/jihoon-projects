import { deferred, edit, props, ticket } from './setup';
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import * as api from '../../../../../api/ticketApi';
import TicketModal from '../..';

it('hides stale card data while loading and displays the latest detail', async () => {
  const request = deferred<typeof ticket>();
  vi.mocked(api.fetchTicket).mockReturnValue(request.promise);
  render(<TicketModal {...props} />);
  expect(screen.getByRole('status')).toHaveTextContent('最新情報を取得中');
  expect(screen.queryByText(ticket.title)).not.toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: '編集' }),
  ).not.toBeInTheDocument();
  await act(async () =>
    request.resolve({ ...ticket, title: 'Changed elsewhere', version: 8 }),
  );
  expect(await screen.findByText('Changed elsewhere')).toBeInTheDocument();
  await edit();
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  await waitFor(() =>
    expect(props.onUpdate).toHaveBeenCalledWith(
      '1',
      expect.objectContaining({ expectedVersion: 8 }),
    ),
  );
});

it.each([
  [new Error('offline'), '最新のチケット情報を取得できませんでした'],
  [new api.TicketApiError('deleted', 404), '削除されたか、存在しません'],
  [new api.TicketApiError('forbidden', 403), 'アクセス権限がありません'],
  [new api.TicketApiError('expired', 401), 'アクセス権限がありません'],
])(
  'shows fetch error %s without stale editing and supports retry',
  async (error, message) => {
    vi.mocked(api.fetchTicket).mockRejectedValueOnce(error);
    render(<TicketModal {...props} />);
    expect(await screen.findByRole('alert')).toHaveTextContent(message);
    expect(
      screen.queryByRole('button', { name: '編集' }),
    ).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '再試行' }));
    expect(await screen.findByText(ticket.title)).toBeInTheDocument();
  },
);

it('ignores reversed detail responses and late errors after switching tickets', async () => {
  const first = deferred<typeof ticket>();
  const second = deferred<typeof ticket>();
  vi.mocked(api.fetchTicket)
    .mockReturnValueOnce(first.promise)
    .mockReturnValueOnce(second.promise);
  const view = render(<TicketModal {...props} />);
  const oldSignal = vi.mocked(api.fetchTicket).mock.calls[0][1];
  view.rerender(
    <TicketModal
      {...props}
      ticket={{ ...ticket, id: '2', title: 'Old second' }}
    />,
  );
  expect(oldSignal?.aborted).toBe(true);
  await act(async () =>
    second.resolve({ ...ticket, id: '2', title: 'Latest second' }),
  );
  expect(await screen.findByText('Latest second')).toBeInTheDocument();
  await act(async () => first.resolve({ ...ticket, title: 'Late first' }));
  expect(screen.queryByText('Late first')).not.toBeInTheDocument();
  expect(screen.getByText('Latest second')).toBeInTheDocument();
  const lateError = deferred<typeof ticket>();
  vi.mocked(api.fetchTicket)
    .mockReturnValueOnce(lateError.promise)
    .mockResolvedValueOnce(ticket);
  view.rerender(<TicketModal {...props} ticket={{ ...ticket, id: '3' }} />);
  view.rerender(<TicketModal {...props} />);
  await screen.findByText(ticket.title);
  await act(async () =>
    lateError.reject(new api.TicketApiError('denied', 403)),
  );
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});
