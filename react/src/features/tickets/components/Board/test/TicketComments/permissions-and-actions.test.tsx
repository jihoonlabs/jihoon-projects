import { mine } from './setup';
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import * as api from '../../../../api/ticketCommentApi';
import TicketComments from '../../TicketComments';

it('shows edit and delete actions only for the signed-in author', async () => {
  render(<TicketComments ticketId="1" currentUserId={7} />);

  const myComment = (await screen.findByText('my comment')).closest('li')!;
  const otherComment = screen.getByText('other comment').closest('li')!;

  expect(within(myComment).getByRole('button', { name: '編集' })).toBeVisible();
  expect(within(myComment).getByRole('button', { name: '削除' })).toBeVisible();
  expect(
    within(otherComment).queryByRole('button', { name: '編集' }),
  ).not.toBeInTheDocument();
  expect(
    within(otherComment).queryByRole('button', { name: '削除' }),
  ).not.toBeInTheDocument();
});

it("allows an application admin to delete another user's comment without editing it", async () => {
  vi.mocked(api.deleteTicketComment).mockResolvedValue();
  render(
    <TicketComments ticketId="1" currentUserId={7} currentUserRole="admin" />,
  );

  const otherComment = (await screen.findByText('other comment')).closest(
    'li',
  )!;
  fireEvent.click(within(otherComment).getByRole('button', { name: '削除' }));
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
  fireEvent.click(within(myComment).getByRole('button', { name: '編集' }));
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
  fireEvent.click(within(myComment).getByRole('button', { name: '削除' }));

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
