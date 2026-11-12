import { deferred, edit, props, ticket } from './setup';
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import * as api from '../../../../../api/ticketApi';
import TicketModal from '../..';

it('競合後に最新情報を取得しても入力を保持し、保存の自動再試行や入力の自動適用を行わない', async () => {
  props.onUpdate.mockRejectedValueOnce(
    new api.TicketApiError('conflict', 409, 'ticket_conflict'),
  );
  render(<TicketModal {...props} />);
  await edit();
  fireEvent.change(screen.getByLabelText('タイトル'), {
    target: { value: 'My draft' },
  });
  fireEvent.change(screen.getByLabelText('説明'), {
    target: { value: 'Draft description' },
  });
  fireEvent.change(screen.getByLabelText('優先度'), {
    target: { value: 'HIGH' },
  });
  fireEvent.change(screen.getByLabelText('担当者'), { target: { value: '' } });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('入力内容は保持');
  expect(screen.getByRole('button', { name: '保存' })).toBeDisabled();
  expect(api.fetchTicket).toHaveBeenCalledTimes(1);
  vi.mocked(api.fetchTicket).mockResolvedValue({
    ...ticket,
    title: 'Other saved',
    version: 4,
  });
  fireEvent.click(screen.getByRole('button', { name: '最新情報を再取得' }));
  expect(await screen.findByText('タイトル: Other saved')).toBeInTheDocument();
  expect(screen.getByLabelText('タイトル')).toHaveValue('My draft');
  expect(screen.getByLabelText('説明')).toHaveValue('Draft description');
  expect(screen.getByLabelText('優先度')).toHaveValue('HIGH');
  expect(screen.getByLabelText('担当者')).toHaveValue('');
  expect(props.onUpdate).toHaveBeenCalledTimes(1);
  expect(screen.getByRole('button', { name: '保存' })).toBeDisabled();
  fireEvent.click(
    screen.getByRole('button', {
      name: '最新情報で編集し直す（入力を置き換える）',
    }),
  );
  expect(screen.getByLabelText('タイトル')).toHaveValue('Other saved');
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  await waitFor(() => expect(props.onUpdate).toHaveBeenCalledTimes(2));
  expect(props.onUpdate.mock.calls[1][1]).toEqual(
    expect.objectContaining({ expectedVersion: 4 }),
  );
});

it('競合後の再取得に失敗したりアクセス権を失ったりしても、下書きを保持し保存は無効のままにする', async () => {
  props.onUpdate.mockRejectedValue(
    new api.TicketApiError('conflict', 409, 'ticket_conflict'),
  );
  render(<TicketModal {...props} />);
  await edit();
  fireEvent.change(screen.getByLabelText('タイトル'), {
    target: { value: 'Protected draft' },
  });
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  await screen.findByRole('alert');
  vi.mocked(api.fetchTicket)
    .mockRejectedValueOnce(new Error('offline'))
    .mockRejectedValueOnce(new api.TicketApiError('denied', 403));
  fireEvent.click(screen.getByRole('button', { name: '最新情報を再取得' }));
  const conflict = within(screen.getByRole('region', { name: '競合の解決' }));
  expect(await conflict.findByRole('alert')).toHaveTextContent(
    '取得できません',
  );
  fireEvent.click(screen.getByRole('button', { name: '最新情報を再取得' }));
  await waitFor(() =>
    expect(conflict.getByRole('alert')).toHaveTextContent('アクセス権限'),
  );
  expect(screen.getByLabelText('タイトル')).toHaveValue('Protected draft');
  expect(screen.getByRole('button', { name: '保存' })).toBeDisabled();
});

it('終了済みプロジェクトの409を編集バージョンの競合として扱わない', async () => {
  props.onUpdate.mockRejectedValue(new api.TicketApiError('Archived', 409));
  render(<TicketModal {...props} />);
  await edit();
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Archived');
  expect(
    screen.queryByRole('button', { name: '最新情報を再取得' }),
  ).not.toBeInTheDocument();
});

const assertLateSaveIsIgnoredAfterTicketChange = async (
  outcome: 'success' | 'conflict',
) => {
  const pending = deferred<typeof ticket>();
  props.onUpdate.mockReturnValue(pending.promise);
  const view = render(<TicketModal {...props} />);
  await edit();
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  vi.mocked(api.fetchTicket).mockResolvedValue({
    ...ticket,
    id: '2',
    title: 'Second ticket',
  });
  view.rerender(<TicketModal {...props} ticket={{ ...ticket, id: '2' }} />);
  await screen.findByText('Second ticket');
  await act(async () =>
    outcome === 'success'
      ? pending.resolve({ ...ticket, title: 'Late save', version: 2 })
      : pending.reject(
          new api.TicketApiError('conflict', 409, 'ticket_conflict'),
        ),
  );
  expect(screen.getByText('Second ticket')).toBeInTheDocument();
  expect(screen.queryByText('Late save')).not.toBeInTheDocument();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
};

it('チケットを切り替えた後に届く保存成功を無視する', () =>
  assertLateSaveIsIgnoredAfterTicketChange('success'));

it('チケットを切り替えた後に届く保存競合を無視する', () =>
  assertLateSaveIsIgnoredAfterTicketChange('conflict'));

const assertLateConflictRefetchIsIgnoredAfterTicketChange = async (
  outcome: 'success' | 'forbidden',
) => {
  props.onUpdate.mockRejectedValue(
    new api.TicketApiError('conflict', 409, 'ticket_conflict'),
  );
  const view = render(<TicketModal {...props} />);
  await edit();
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  await screen.findByRole('alert');
  const pending = deferred<typeof ticket>();
  vi.mocked(api.fetchTicket)
    .mockReturnValueOnce(pending.promise)
    .mockResolvedValueOnce({ ...ticket, id: '2', title: 'Second ticket' });
  fireEvent.click(screen.getByRole('button', { name: '最新情報を再取得' }));
  view.rerender(<TicketModal {...props} ticket={{ ...ticket, id: '2' }} />);
  await screen.findByText('Second ticket');
  await act(async () =>
    outcome === 'success'
      ? pending.resolve({ ...ticket, title: 'Late reload', version: 9 })
      : pending.reject(new api.TicketApiError('denied', 403)),
  );
  expect(screen.getByText('Second ticket')).toBeInTheDocument();
  expect(screen.queryByText('Late reload')).not.toBeInTheDocument();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
};

it('チケットを切り替えた後に届く競合後の再取得成功を無視する', () =>
  assertLateConflictRefetchIsIgnoredAfterTicketChange('success'));

it('チケットを切り替えた後に届く競合後の再取得の403エラーを無視する', () =>
  assertLateConflictRefetchIsIgnoredAfterTicketChange('forbidden'));
