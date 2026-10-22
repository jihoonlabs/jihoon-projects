import './setup';
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
import { deferred, edit, props, ticket } from './setup';

it.each(['create', 'edit'])(
  'locks draft fields during %s save and restores them after failure',
  async (mode) => {
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

    const fields = ['タイトル', '説明', 'ステータス', '優先度', '担当者'].map(
      (label) => screen.getByLabelText(label),
    );
    const blocked = fields.map((field) => (field as HTMLInputElement).disabled);
    await userEvent.setup().type(title, ' unsent input');
    await act(async () => pending.reject(new Error('save failed')));
    await screen.findByRole('alert');

    expect(blocked).toEqual([true, true, true, true, true]);
    expect(title).toHaveValue('Submitted draft');
    expect(screen.getByLabelText('説明')).toHaveValue('Draft description');
    fields.forEach((field) => expect(field).not.toBeDisabled());
    expect(screen.getByRole('button', { name: '保存' })).toBeEnabled();
  },
);

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
