import * as api from '../../../api/ticketApi';
import { responseTicket } from '../../../api/test/ticketFixture';
import type { Ticket } from '../../../types/ticket';
import { useTicketStore } from '../../useTicketStore';

export const ticket = (
  id: string,
  position = 0,
  status: Ticket['status'] = 'TODO',
): Ticket => ({ ...api.toTicket({ ...responseTicket, position }), id, status });
export const state = () => useTicketStore.getState();
export function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
