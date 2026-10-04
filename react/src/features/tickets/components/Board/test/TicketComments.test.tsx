import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

it('allows an application admin to delete another user\'s comment without editing it', async () => {
  vi.mocked(api.deleteTicketComment).mockResolvedValue();
  render(<TicketComments ticketId="1" currentUserId={7} currentUserRole="admin" />);

  const otherComment = (await screen.findByText('other comment')).closest('li')!;
  expect(otherComment.querySelectorAll('button')).toHaveLength(1);
  fireEvent.click(otherComment.querySelector('button')!);
  await waitFor(() => expect(api.deleteTicketComment).toHaveBeenCalledWith('1', '11'));
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
