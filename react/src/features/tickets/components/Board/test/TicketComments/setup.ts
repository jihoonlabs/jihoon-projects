import { beforeEach, vi } from 'vitest';
import * as api from '../../../../api/ticketCommentApi';

vi.mock('../../../../api/ticketCommentApi', () => ({
  fetchTicketComments: vi.fn(),
  createTicketComment: vi.fn(),
  updateTicketComment: vi.fn(),
  deleteTicketComment: vi.fn(),
}));

export const mine = {
  id: '10',
  body: 'my comment',
  author: { id: '7', name: 'Tester' },
  createdAt: '2026-09-30T00:00:00Z',
  updatedAt: '2026-09-30T00:00:00Z',
};
export const other = {
  ...mine,
  id: '11',
  body: 'other comment',
  author: { id: '8', name: 'Other' },
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.fetchTicketComments).mockResolvedValue([mine, other]);
});

export function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
