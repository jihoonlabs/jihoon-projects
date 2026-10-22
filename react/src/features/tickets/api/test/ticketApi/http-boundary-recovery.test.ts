import { http, HttpResponse } from 'msw';
import { expect, it } from 'vitest';
import { server } from '@/test/mocks/server';
import { fetchTickets, TicketApiError } from '../../ticketApi';
import { responseTicket } from '../ticketFixture';
import { url } from '../setup';

// Verify the real HTTP boundary, rather than mocking the API client itself.
it('recovers from a temporary list failure on the next request', async () => {
  let requests = 0;
  server.use(
    http.get(`${url}/api/tickets`, () => {
      requests += 1;
      if (requests === 1) {
        return HttpResponse.json(
          { message: 'Temporarily unavailable' },
          { status: 503 },
        );
      }
      return HttpResponse.json({ data: [responseTicket] });
    }),
  );

  await expect(fetchTickets()).rejects.toMatchObject({
    name: 'TicketApiError',
    status: 503,
  } satisfies Partial<TicketApiError>);
  await expect(fetchTickets()).resolves.toMatchObject([
    { issueKey: 'TICK-1' },
  ]);
  expect(requests).toBe(2);
});

it('rejects an invalid list envelope instead of treating it as empty', async () => {
  server.use(
    http.get(`${url}/api/tickets`, () =>
      HttpResponse.json({ data: null }),
    ),
  );

  await expect(fetchTickets()).rejects.toThrow(
    'チケットAPIの応答形式が不正です。',
  );
});
