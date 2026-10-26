import { deferred, edit, props, ticket } from './setup';
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import TicketModal from '../..';

const assertDraftFieldsUnlockAfterFailedSave = async (
  mode: 'create' | 'edit',
) => {
  const pending = deferred<typeof ticket>();
  const onCreate = vi.fn().mockReturnValue(pending.promise);
  props.onUpdate.mockReturnValue(pending.promise);
  render(
    <TicketModal
      {...props}
      ticket={mode === 'create' ? null : ticket}
      onCreate={onCreate}
    />,
  );
  if (mode === 'edit') await edit();
  const title = screen.getByLabelText('タイトル');
  fireEvent.change(title, { target: { value: 'Submitted draft' } });
  fireEvent.change(screen.getByLabelText('説明'), {
    target: { value: 'Draft description' },
  });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));

  const description = screen.getByLabelText('説明');
  const status = screen.getByLabelText('ステータス');
  const priority = screen.getByLabelText('優先度');
  const assignee = screen.getByLabelText('担当者');
  expect(title).toBeDisabled();
  expect(description).toBeDisabled();
  expect(status).toBeDisabled();
  expect(priority).toBeDisabled();
  expect(assignee).toBeDisabled();
  await userEvent.setup().type(title, ' unsent input');
  await act(async () => pending.reject(new Error('save failed')));
  await screen.findByRole('alert');

  expect(title).toHaveValue('Submitted draft');
  expect(description).toHaveValue('Draft description');
  expect(title).not.toBeDisabled();
  expect(description).not.toBeDisabled();
  expect(status).not.toBeDisabled();
  expect(priority).not.toBeDisabled();
  expect(assignee).not.toBeDisabled();
  expect(screen.getByRole('button', { name: '保存' })).toBeEnabled();
};

it('locks and restores draft fields after a failed ticket creation', () =>
  assertDraftFieldsUnlockAfterFailedSave('create'));

it('locks and restores draft fields after a failed ticket edit', () =>
  assertDraftFieldsUnlockAfterFailedSave('edit'));

it('uses the successful save version for subsequent editing and keeps assignee', async () => {
  props.onUpdate.mockResolvedValue({
    ...ticket,
    title: 'Saved',
    version: 2,
    assignee: null,
  });
  render(<TicketModal {...props} />);
  await edit();
  fireEvent.change(screen.getByLabelText('担当者'), { target: { value: '' } });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  await screen.findByRole('heading', { name: 'チケット詳細' });
  await edit();
  expect(screen.getByLabelText('担当者')).toHaveValue('');
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  await waitFor(() => expect(props.onUpdate).toHaveBeenCalledTimes(2));
  expect(props.onUpdate.mock.calls[1][1]).toEqual(
    expect.objectContaining({ expectedVersion: 2 }),
  );
  expect(props.onUpdate.mock.calls[1][1]).not.toHaveProperty('assigneeId');
});

it('adopts response fields and version together, including a newer canonical snapshot', async () => {
  props.onUpdate.mockResolvedValue({
    ...ticket,
    title: 'Canonical newer title',
    description: 'Server description',
    status: 'DONE',
    priority: 'LOW',
    assignee: null,
    version: 7,
  });
  render(<TicketModal {...props} />);
  await edit();
  fireEvent.change(screen.getByLabelText('タイトル'), {
    target: { value: 'Submitted title' },
  });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  expect(await screen.findByText('Canonical newer title')).toBeInTheDocument();
  await edit();
  expect(screen.getByLabelText('タイトル')).toHaveValue(
    'Canonical newer title',
  );
  expect(screen.getByLabelText('説明')).toHaveValue('Server description');
  expect(screen.getByLabelText('ステータス')).toHaveValue('DONE');
  expect(screen.getByLabelText('優先度')).toHaveValue('LOW');
  expect(screen.getByLabelText('担当者')).toHaveValue('');
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  await waitFor(() => expect(props.onUpdate).toHaveBeenCalledTimes(2));
  expect(props.onUpdate.mock.calls[1][1]).toEqual(
    expect.objectContaining({
      title: 'Canonical newer title',
      expectedVersion: 7,
    }),
  );
});
