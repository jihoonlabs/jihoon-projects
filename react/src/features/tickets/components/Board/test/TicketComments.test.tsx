import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import * as api from '../../../api/ticketCommentApi';
import TicketComments from '../TicketComments';

vi.mock('../../../api/ticketCommentApi', () => ({
  fetchTicketComments: vi.fn(),
  createTicketComment: vi.fn(),
  updateTicketComment: vi.fn(),
  deleteTicketComment: vi.fn(),
}));

const mine = {
  id: '10',
  body: 'my comment',
  author: { id: '7', name: 'Tester' },
  createdAt: '2026-09-30T00:00:00Z',
  updatedAt: '2026-09-30T00:00:00Z',
};
const other = {
  ...mine,
  id: '11',
  body: 'other comment',
  author: { id: '8', name: 'Other' },
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.fetchTicketComments).mockResolvedValue([mine, other]);
});

it('shows edit and delete actions only for the signed-in author', async () => {
  render(<TicketComments ticketId="1" currentUserId={7} />);

  const myComment = (await screen.findByText('my comment')).closest('li')!;
  const otherComment = screen.getByText('other comment').closest('li')!;

  expect(myComment.querySelectorAll('button')).toHaveLength(2);
  expect(otherComment.querySelectorAll('button')).toHaveLength(0);
});

it("allows an application admin to delete another user's comment without editing it", async () => {
  vi.mocked(api.deleteTicketComment).mockResolvedValue();
  render(
    <TicketComments ticketId="1" currentUserId={7} currentUserRole="admin" />,
  );

  const otherComment = (await screen.findByText('other comment')).closest(
    'li',
  )!;
  expect(otherComment.querySelectorAll('button')).toHaveLength(1);
  fireEvent.click(otherComment.querySelector('button')!);
  await waitFor(() =>
    expect(api.deleteTicketComment).toHaveBeenCalledWith('1', '11'),
  );
  expect(screen.queryByText('other comment')).not.toBeInTheDocument();
});

it('creates a trimmed comment and appends the server response', async () => {
  vi.mocked(api.createTicketComment).mockResolvedValue({
    ...mine,
    id: '12',
    body: 'new comment',
  });
  render(<TicketComments ticketId="1" currentUserId={7} />);

  await screen.findByText('my comment');
  fireEvent.change(screen.getByLabelText('コメントを追加'), {
    target: { value: '  new comment  ' },
  });
  fireEvent.click(screen.getByRole('button', { name: '送信' }));

  await waitFor(() =>
    expect(api.createTicketComment).toHaveBeenCalledWith('1', 'new comment'),
  );
  expect(await screen.findByText('new comment')).toBeInTheDocument();
});

it('edits an owned comment', async () => {
  vi.mocked(api.updateTicketComment).mockResolvedValue({
    ...mine,
    body: 'updated',
  });
  render(<TicketComments ticketId="1" currentUserId={7} />);

  const myComment = (await screen.findByText('my comment')).closest('li')!;
  fireEvent.click(myComment.querySelectorAll('button')[0]);
  fireEvent.change(screen.getByLabelText('コメント編集'), {
    target: { value: ' updated ' },
  });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));

  await waitFor(() =>
    expect(api.updateTicketComment).toHaveBeenCalledWith('1', '10', 'updated'),
  );
  expect(await screen.findByText('updated')).toBeInTheDocument();
});

it('deletes an owned comment', async () => {
  vi.mocked(api.deleteTicketComment).mockResolvedValue();
  render(<TicketComments ticketId="1" currentUserId={7} />);

  const myComment = (await screen.findByText('my comment')).closest('li')!;
  fireEvent.click(myComment.querySelectorAll('button')[1]);

  await waitFor(() =>
    expect(api.deleteTicketComment).toHaveBeenCalledWith('1', '10'),
  );
  expect(screen.queryByText('my comment')).not.toBeInTheDocument();
});

it('keeps content and shows an error when creation fails', async () => {
  vi.mocked(api.createTicketComment).mockRejectedValue(
    new Error('create failed'),
  );
  render(<TicketComments ticketId="1" currentUserId={7} />);

  await screen.findByText('my comment');
  const input = screen.getByLabelText('コメントを追加');
  fireEvent.change(input, { target: { value: 'keep me' } });
  fireEvent.click(screen.getByRole('button', { name: '送信' }));

  expect(await screen.findByRole('alert')).toHaveTextContent('create failed');
  expect(input).toHaveValue('keep me');
});

it('keeps archived comments visible without mutation controls, including for admins', async () => {
  render(
    <TicketComments
      ticketId="1"
      currentUserId={7}
      currentUserRole="admin"
      readOnly
    />,
  );
  expect(await screen.findByText('my comment')).toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: '編集' }),
  ).not.toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: '削除' }),
  ).not.toBeInTheDocument();
  expect(screen.queryByLabelText('コメントを追加')).not.toBeInTheDocument();
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}

it('blocks submission while the initial list is pending instead of losing a new comment to an older GET', async () => {
  const list = deferred<(typeof mine)[]>();
  vi.mocked(api.fetchTicketComments).mockReturnValueOnce(list.promise);
  render(<TicketComments ticketId="1" currentUserId={7} />);
  expect(screen.getByRole('status')).toHaveTextContent('コメントを取得中');
  expect(
    screen.queryByText('コメントはまだありません。'),
  ).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('コメントを追加'), {
    target: { value: 'draft while loading' },
  });
  const send = screen.getByRole('button', { name: '送信' });
  expect(send).toBeDisabled();
  fireEvent.submit(send.closest('form')!);
  expect(api.createTicketComment).not.toHaveBeenCalled();
  list.resolve([mine]);
  await screen.findByText('my comment');
  await waitFor(() => expect(send).toBeEnabled());
  expect(screen.getByLabelText('コメントを追加')).toHaveValue(
    'draft while loading',
  );
});

it('retries a failed list without presenting it as empty or clearing the draft', async () => {
  vi.mocked(api.fetchTicketComments).mockRejectedValueOnce(
    new Error('list failed'),
  );
  render(<TicketComments ticketId="1" currentUserId={7} />);
  expect(await screen.findByRole('alert')).toHaveTextContent('list failed');
  expect(
    screen.queryByText('コメントはまだありません。'),
  ).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('コメントを追加'), {
    target: { value: 'keep draft' },
  });
  expect(screen.getByRole('button', { name: '送信' })).toBeDisabled();
  fireEvent.click(screen.getByRole('button', { name: 'コメントを再取得' }));
  await screen.findByText('my comment');
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(screen.getByLabelText('コメントを追加')).toHaveValue('keep draft');
  expect(screen.getByRole('button', { name: '送信' })).toBeEnabled();
});

it('preserves the next draft typed while a previous comment is being sent and rejects duplicate submit events', async () => {
  const post = deferred<typeof mine>();
  vi.mocked(api.createTicketComment).mockReturnValueOnce(post.promise);
  render(<TicketComments ticketId="1" currentUserId={7} />);
  await screen.findByText('my comment');
  const input = screen.getByLabelText('コメントを追加');
  fireEvent.change(input, { target: { value: 'first draft' } });
  const form = input.closest('form')!;
  fireEvent.submit(form);
  fireEvent.submit(form);
  expect(api.createTicketComment).toHaveBeenCalledTimes(1);
  fireEvent.change(input, { target: { value: 'next draft' } });
  post.resolve({ ...mine, id: '12', body: 'first draft' });
  await screen.findByText('first draft');
  expect(input).toHaveValue('next draft');
});

it('isolates a new ticket from the previous ticket draft and late post response', async () => {
  const post = deferred<typeof mine>();
  vi.mocked(api.createTicketComment).mockReturnValueOnce(post.promise);
  const view = render(<TicketComments ticketId="1" currentUserId={7} />);
  await screen.findByText('my comment');
  fireEvent.change(screen.getByLabelText('コメントを追加'), {
    target: { value: 'old ticket draft' },
  });
  fireEvent.click(screen.getByRole('button', { name: '送信' }));
  vi.mocked(api.fetchTicketComments).mockResolvedValueOnce([]);
  view.rerender(<TicketComments ticketId="2" currentUserId={7} />);
  await screen.findByText('コメントはまだありません。');
  expect(screen.getByLabelText('コメントを追加')).toHaveValue('');
  await act(async () => {
    post.resolve({ ...mine, id: '12', body: 'old ticket draft' });
    await post.promise;
  });
  await waitFor(() =>
    expect(screen.queryByText('old ticket draft')).not.toBeInTheDocument(),
  );
  expect(screen.queryByText('my comment')).not.toBeInTheDocument();
});

it('locks the edit field during save so changes cannot disappear after the response', async () => {
  const edit = deferred<typeof mine>();
  vi.mocked(api.updateTicketComment).mockReturnValueOnce(edit.promise);
  render(<TicketComments ticketId="1" currentUserId={7} />);
  const item = (await screen.findByText('my comment')).closest('li')!;
  fireEvent.click(item.querySelectorAll('button')[0]);
  const input = screen.getByLabelText('コメント編集');
  fireEvent.change(input, { target: { value: 'saved edit' } });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  expect(input).toBeDisabled();
  edit.reject(new Error('edit failed'));
  expect(await screen.findByRole('alert')).toHaveTextContent('edit failed');
  expect(input).toBeEnabled();
  expect(input).toHaveValue('saved edit');
});

it('ignores a previous ticket list response after switching tickets', async () => {
  const oldList = deferred<(typeof mine)[]>();
  vi.mocked(api.fetchTicketComments).mockReturnValueOnce(oldList.promise);
  const view = render(<TicketComments ticketId="1" currentUserId={7} />);
  vi.mocked(api.fetchTicketComments).mockResolvedValueOnce([other]);
  view.rerender(<TicketComments ticketId="2" currentUserId={7} />);
  await screen.findByText('other comment');
  await act(async () => {
    oldList.resolve([mine]);
    await oldList.promise;
  });
  expect(screen.queryByText('my comment')).not.toBeInTheDocument();
  expect(screen.getByText('other comment')).toBeInTheDocument();
});
