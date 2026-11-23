import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { useAuthStore } from '~/features/auth/store/useAuthStore';
import { deferred } from '~/test/deferred';
import { signInAs } from '~/test/auth/signInAs';
import { apiUrl } from '~/test/mocks/apiUrl';
import { overrideApi } from '~/test/mocks/overrideApi';
import { ticketApi } from '~/test/mocks/tickets/ticketApiHandlers';

import { ticketFixture } from '../../api/test/ticketFixture';
import { useTicketStore } from '../useTicketStore';

const ids = (store: ReturnType<typeof useTicketStore>) =>
  store.tickets.map((ticket) => ticket.id);

const loadedStore = async () => {
  signInAs();
  overrideApi(
    ticketApi.tickets([
      ticketFixture({ id: '1', title: 'One' }),
      ticketFixture({ id: '2', title: 'Two' }),
    ]),
  );
  const store = useTicketStore();
  await store.fetchTickets();

  return store;
};

describe('チケットストアの書き込み', () => {
  it('作成したチケットを一覧へ加えること', async () => {
    const store = await loadedStore();
    overrideApi(
      http.post(apiUrl('/api/tickets'), () =>
        HttpResponse.json(
          { data: ticketFixture({ id: '3' }) },
          { status: 201 },
        ),
      ),
    );

    const created = await store.createTicket({ projectId: '1', title: 'New' });

    expect(created.id).toBe('3');
    expect(ids(store)).toEqual(['1', '2', '3']);
  });

  it('更新したチケットを、一覧の同じ位置で置き換えること', async () => {
    const store = await loadedStore();
    overrideApi(
      http.patch(apiUrl('/api/tickets/1'), () =>
        HttpResponse.json({
          data: ticketFixture({ id: '1', title: 'Renamed', version: 2 }),
        }),
      ),
    );

    await store.updateTicket('1', { expectedVersion: 1, title: 'Renamed' });

    expect(store.tickets.map((ticket) => ticket.title)).toEqual([
      'Renamed',
      'Two',
    ]);
    expect(store.tickets[0]?.version).toBe(2);
  });

  it('削除したチケットを一覧から外すこと', async () => {
    const store = await loadedStore();
    overrideApi(
      http.delete(
        apiUrl('/api/tickets/1'),
        () => new HttpResponse(null, { status: 204 }),
      ),
    );

    await store.deleteTicket('1');

    expect(ids(store)).toEqual(['2']);
  });

  it('失敗したときは、失敗を伝え、一覧を変えないこと', async () => {
    const store = await loadedStore();
    overrideApi(
      http.delete(apiUrl('/api/tickets/1'), () =>
        HttpResponse.json({ message: 'x' }, { status: 500 }),
      ),
    );

    await expect(store.deleteTicket('1')).rejects.toThrow('500');

    expect(ids(store)).toEqual(['1', '2']);
  });

  it('保存の最中にログインし直されたら、遅れて届いた結果を一覧へ反映しないこと', async () => {
    const store = await loadedStore();
    const entered = deferred();
    const gate = deferred();
    let received = 0;
    overrideApi(
      http.post(apiUrl('/api/tickets'), async () => {
        // 要求がサーバー（ハンドラー）へ届いたことを知らせてから、応答を止める
        received += 1;
        entered.resolve();
        await gate.promise;

        return HttpResponse.json(
          { data: ticketFixture({ id: '3' }) },
          { status: 201 },
        );
      }),
    );

    const pending = store
      .createTicket({ projectId: '1', title: 'Late' })
      .catch(() => undefined);
    // 送信前の取り消しで通ってしまわないよう、ハンドラーに届いてから再ログインする
    await entered.promise;
    useAuthStore().signIn(useAuthStore().user!);
    gate.resolve();
    await pending;

    // 送信前の取り消しではなく、届いた要求の応答を捨てたことを確かめる
    expect(received).toBe(1);
    expect(ids(store)).not.toContain('3');
  });
});
