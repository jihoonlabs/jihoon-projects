import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import * as api from '../../../../api/ticketApi';
import { responseTicket } from '../../../../api/test/ticketFixture';
import TicketModal from '..';

vi.mock('../../../../api/ticketApi', async (original) => ({
  ...(await original<typeof import('../../../../api/ticketApi')>()),
  fetchTicket: vi.fn(),
}));
vi.mock('../../TicketComments', () => ({ default: () => null }));
const ticket = api.toTicket(responseTicket);
const props = {
  ticket,
  currentUserId: 7,
  projectId: '1',
  projectMembers: [
    {
      id: '7',
      name: 'Tester',
      email: 'tester@example.test',
      role: 'member' as const,
      permission: 'write' as const,
    },
  ],
  onClose: vi.fn(),
  onCreate: vi.fn(),
  onDelete: vi.fn(),
  onUpdate: vi
    .fn()
    .mockResolvedValue({ ...ticket, title: 'Saved', version: 2 }),
};
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
async function edit() {
  await screen.findByRole('heading', { name: 'チケット詳細' });
  fireEvent.click(screen.getByRole('button', { name: '編集' }));
}
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.fetchTicket).mockResolvedValue(ticket);
  props.onUpdate.mockResolvedValue({ ...ticket, title: 'Saved', version: 2 });
});

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

it('preserves all input on conflict and refetch, with no automatic retry or rebase', async () => {
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

it('keeps conflict drafts when reloading fails or loses access, without re-enabling save', async () => {
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

it('does not treat an archived-project 409 as an edit version conflict', async () => {
  props.onUpdate.mockRejectedValue(new api.TicketApiError('Archived', 409));
  render(<TicketModal {...props} />);
  await edit();
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Archived');
  expect(
    screen.queryByRole('button', { name: '最新情報を再取得' }),
  ).not.toBeInTheDocument();
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

it.each(['success', 'conflict'])(
  'ignores late save %s after changing Ticket',
  async (outcome) => {
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
  },
);

it.each(['success', 'forbidden'])(
  'ignores late conflict refetch %s after changing Ticket',
  async (outcome) => {
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
  },
);

it('keeps Tab and Shift+Tab inside loading, detail and edit dialogs', async () => {
  const request = deferred<typeof ticket>();
  vi.mocked(api.fetchTicket).mockReturnValueOnce(request.promise);
  render(
    <>
      <button>Before modal</button>
      <TicketModal {...props} />
      <button>After modal</button>
    </>,
  );
  const user = userEvent.setup();
  const close = screen.getByRole('button', { name: '閉じる' });
  close.focus();
  await user.tab();
  expect(screen.getByRole('dialog')).toContainElement(
    document.activeElement as HTMLElement,
  );
  await user.tab({ shift: true });
  expect(screen.getByRole('dialog')).toContainElement(
    document.activeElement as HTMLElement,
  );
  await act(async () => request.resolve(ticket));
  await screen.findByRole('heading', { name: 'チケット詳細' });
  const first = screen.getByRole('region', { name: '説明本文' });
  first.focus();
  await user.tab({ shift: true });
  expect(screen.getByRole('button', { name: '削除' })).toHaveFocus();
  await user.tab();
  expect(first).toHaveFocus();
  await user.click(screen.getByRole('button', { name: '編集' }));
  const title = screen.getByRole('textbox', { name: 'タイトル' });
  title.focus();
  await user.tab({ shift: true });
  expect(screen.getByRole('button', { name: '保存' })).toHaveFocus();
  await user.tab();
  expect(title).toHaveFocus();
});
