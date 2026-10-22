import { fireEvent, screen } from '@testing-library/react';
import { beforeEach, vi } from 'vitest';
import * as api from '../../../../../api/ticketApi';
import { responseTicket } from '../../../../../api/test/ticketFixture';

vi.mock('../../../../../api/ticketApi', async (original) => ({
  ...(await original<typeof import('../../../../../api/ticketApi')>()),
  fetchTicket: vi.fn(),
}));
vi.mock('../../../TicketComments', () => ({ default: () => null }));

export const ticket = api.toTicket(responseTicket);
export const props = {
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
export function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
export async function edit() {
  await screen.findByRole('heading', { name: 'チケット詳細' });
  fireEvent.click(screen.getByRole('button', { name: '編集' }));
}
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.fetchTicket).mockResolvedValue(ticket);
  props.onUpdate.mockResolvedValue({ ...ticket, title: 'Saved', version: 2 });
});
