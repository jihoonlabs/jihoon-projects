import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { useAuthStore } from '~/features/auth/store/useAuthStore';
import { signInAs } from '~/test/auth/signInAs';
import { apiUrl } from '~/test/mocks/apiUrl';
import { overrideApi } from '~/test/mocks/overrideApi';
import { ticketApi } from '~/test/mocks/tickets/ticketApiHandlers';

import { ticketFixture } from '../../api/test/ticketFixture';
import { useTicketStore } from '../useTicketStore';

const deferred = () => {
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });

  return { gate, release };
};

describe('チケットストア', () => {
  it('取得したチケットを保持し、読み込み中の表示を戻すこと', async () => {
    signInAs();
    overrideApi(ticketApi.tickets([ticketFixture({ id: '1' })]));
    const store = useTicketStore();

    const loading = store.fetchTickets();
    expect(store.isLoading).toBe(true);
    await loading;

    expect(store.tickets.map((ticket) => ticket.id)).toEqual(['1']);
    expect(store.isLoading).toBe(false);
    expect(store.error).toBeNull();
  });

  it('失敗したときは表示用のメッセージを持ち、前の一覧を残すこと', async () => {
    signInAs();
    overrideApi(ticketApi.tickets([ticketFixture({ id: '1' })]));
    const store = useTicketStore();
    await store.fetchTickets();

    overrideApi(ticketApi.ticketsFail(500));
    await store.fetchTickets();

    expect(store.error).toContain('500');
    expect(store.tickets.map((ticket) => ticket.id)).toEqual(['1']);
  });

  it('再取得の成功でエラー表示を消すこと', async () => {
    signInAs();
    overrideApi(ticketApi.ticketsFail(500));
    const store = useTicketStore();
    await store.fetchTickets();
    expect(store.error).not.toBeNull();

    overrideApi(ticketApi.tickets([]));
    await store.fetchTickets();

    expect(store.error).toBeNull();
  });

  it('遅れて届く古い取得結果で新しい結果を上書きしないこと', async () => {
    signInAs();
    const first = deferred();
    let call = 0;
    overrideApi(
      http.get(apiUrl('/api/tickets'), async () => {
        call += 1;
        if (call === 1) {
          await first.gate;
          return HttpResponse.json({ data: [ticketFixture({ id: 'old' })] });
        }

        return HttpResponse.json({ data: [ticketFixture({ id: 'new' })] });
      }),
    );
    const store = useTicketStore();

    const older = store.fetchTickets();
    await store.fetchTickets();
    first.release();
    await older;

    expect(store.tickets.map((ticket) => ticket.id)).toEqual(['new']);
    expect(store.isLoading).toBe(false);
  });

  it('ログアウト後に届いた古い一覧を表示しないこと', async () => {
    signInAs();
    const gate = deferred();
    overrideApi(
      http.get(apiUrl('/api/tickets'), async () => {
        await gate.gate;
        return HttpResponse.json({ data: [ticketFixture({ id: 'stale' })] });
      }),
    );
    const store = useTicketStore();

    const loading = store.fetchTickets();
    useAuthStore().signOut();
    gate.release();
    await loading;

    expect(store.tickets).toEqual([]);
    expect(store.error).toBeNull();
  });

  it('セッション期限切れのあとは取得しないこと', async () => {
    signInAs();
    useAuthStore().expireSession();
    overrideApi(ticketApi.tickets([ticketFixture()]));
    const store = useTicketStore();

    await store.fetchTickets();

    expect(store.tickets).toEqual([]);
    expect(store.isLoading).toBe(false);
  });

  it('reset で一覧・エラー・読み込み中を初期状態に戻すこと', async () => {
    signInAs();
    overrideApi(ticketApi.tickets([ticketFixture()]));
    const store = useTicketStore();
    await store.fetchTickets();

    store.reset();

    expect(store.tickets).toEqual([]);
    expect(store.error).toBeNull();
    expect(store.isLoading).toBe(false);
  });
});
