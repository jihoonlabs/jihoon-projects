import { deferred, edit, props, ticket } from './setup';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import TicketModal from '../..';

async function enterEditBeforeDeleteFails() {
  const pendingDelete = deferred<void>();
  props.onDelete.mockReturnValue(pendingDelete.promise);
  const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true);
  render(<TicketModal {...props} />);
  fireEvent.click(await screen.findByRole('button', { name: '削除' }));
  confirm.mockRestore();
  expect(screen.getByRole('button', { name: '閉じる' })).toBeDisabled();
  expect(screen.getByRole('button', { name: '編集' })).toBeEnabled();
  await edit();
  expect(screen.getByRole('button', { name: '保存中...' })).toBeDisabled();
  await act(async () => pendingDelete.reject(new Error('delete failed')));
  expect(await screen.findByRole('alert')).toHaveTextContent('delete failed');
  await waitFor(() =>
    expect(screen.getByRole('button', { name: '保存' })).toBeEnabled(),
  );
}

it('shows the new save error after a pending delete fails in edit mode', async () => {
  await enterEditBeforeDeleteFails();
  const pendingSave = deferred<typeof ticket>();
  props.onUpdate.mockReturnValueOnce(pendingSave.promise);
  fireEvent.click(screen.getByRole('button', { name: '保存' }));

  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: '保存中...' })).toBeDisabled();
  await act(async () => pendingSave.reject(new Error('update failed')));

  await waitFor(() =>
    expect(screen.getByRole('alert')).toHaveTextContent('update failed'),
  );
  expect(screen.queryByText('delete failed')).not.toBeInTheDocument();
  expect(props.onUpdate).toHaveBeenCalledTimes(1);
});

it('clears the delete error when the later save succeeds', async () => {
  await enterEditBeforeDeleteFails();
  props.onUpdate.mockResolvedValueOnce({
    ...ticket,
    title: 'Saved after delete failure',
    version: 2,
  });
  fireEvent.change(screen.getByLabelText('タイトル'), {
    target: { value: 'Saved after delete failure' },
  });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));

  expect(
    await screen.findByText('Saved after delete failure'),
  ).toBeInTheDocument();
  expect(
    screen.getByRole('heading', { name: 'チケット詳細' }),
  ).toBeInTheDocument();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(props.onUpdate).toHaveBeenCalledTimes(1);
});
