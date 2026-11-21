import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { signInAs } from '~/test/auth/signInAs';
import { apiUrl } from '~/test/mocks/apiUrl';
import { overrideApi } from '~/test/mocks/overrideApi';

import { TicketApiError } from '../apiErrors';
import { useTicketApi } from '../ticketApi';
import { ticketFixture } from './ticketFixture';

describe('チケット 1 件の取得 API', () => {
  it('取得したチケットを画面用の形で返すこと', async () => {
    signInAs();
    overrideApi(
      http.get(apiUrl('/api/tickets/5'), () =>
        HttpResponse.json({ data: ticketFixture({ id: '5', version: 3 }) }),
      ),
    );

    const ticket = await useTicketApi().fetchTicket('5');

    expect(ticket).toMatchObject({ id: '5', projectId: '1', version: 3 });
  });

  it('ID を URL 用に変換して送ること', async () => {
    signInAs();
    let path = '';
    overrideApi(
      http.get(apiUrl('/api/tickets/:id'), ({ request }) => {
        path = new URL(request.url).pathname;

        return HttpResponse.json({ data: ticketFixture() });
      }),
    );

    await useTicketApi().fetchTicket('a/b');

    expect(path).toBe('/api/tickets/a%2Fb');
  });

  it('失敗したら、状態コードを持つ表示用の失敗にすること', async () => {
    signInAs();
    overrideApi(
      http.get(apiUrl('/api/tickets/5'), () =>
        HttpResponse.json({ message: 'Not found' }, { status: 404 }),
      ),
    );

    const failure = await useTicketApi()
      .fetchTicket('5')
      .catch((error: unknown) => error);

    expect(failure).toBeInstanceOf(TicketApiError);
    expect(failure).toMatchObject({ status: 404 });
    expect((failure as Error).message).not.toContain('Not found');
  });

  it('応答にチケットがなければ、形式の不正として失敗にすること', async () => {
    signInAs();
    overrideApi(
      http.get(apiUrl('/api/tickets/5'), () =>
        HttpResponse.json({ data: null }),
      ),
    );

    await expect(useTicketApi().fetchTicket('5')).rejects.toThrow('形式');
  });
});
