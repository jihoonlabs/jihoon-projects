import './setup';
import * as api from '../../../api/ticketApi';
import { useTicketStore } from '../../useTicketStore';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { deferred, state, ticket } from './helpers';
import type { Ticket } from '../../../types/ticket';
import { describe, expect, it, vi } from 'vitest';

describe('セッション切り替え', () => {
  it('ログアウト後に以前のリクエストが失敗しても、削除したカードを復元しない', async () => {
    useTicketStore.setState({ tickets: [ticket('1')] });
    const pending = deferred<void>();
    vi.mocked(api.deleteTicket).mockReturnValue(pending.promise);
    const deletion = state().deleteTicket('1');
    const rejected = expect(deletion).rejects.toThrow('Expired');
    useAuthStore.getState().logout();
    pending.reject(new Error('Expired'));
    await rejected;
    expect(state().tickets).toEqual([]);
    expect(state().error).toBeNull();
  });

  it('ログアウト後に届く古い一覧レスポンスを破棄する', async () => {
    const pending = deferred<Ticket[]>();
    vi.mocked(api.fetchTickets).mockReturnValue(pending.promise);
    const loading = state().fetchTickets();
    useAuthStore.getState().logout();
    pending.resolve([ticket('1')]);
    await loading;
    expect(state().tickets).toEqual([]);
  });

  it('以前のセッションで待機中だった更新をキャンセルする', async () => {
    useTicketStore.setState({ tickets: [ticket('1')] });
    const pending = deferred<Ticket>();
    vi.mocked(api.updateTicket).mockReturnValue(pending.promise);
    const first = state().updateTicket('1', { title: 'First' });
    const second = state().updateTicket('1', { title: 'Second' });
    const rejected = expect(second).rejects.toMatchObject({
      name: 'AbortError',
    });
    useAuthStore.getState().logout();
    pending.resolve(ticket('1'));
    await first;
    await rejected;
    expect(api.updateTicket).toHaveBeenCalledTimes(1);
    expect(state().tickets).toEqual([]);
  });
});
