import './setup';
import { http, HttpResponse } from 'msw';
import { expect, it } from 'vitest';
import {
  createTicket,
  fetchTickets,
  toTicket,
  updateTicket,
} from '../../ticketApi';
import { responseTicket } from '../ticketFixture';
import { server, url } from './setup';

it.each(['not-an-id', '', '0', '1.5'])(
  'rejects invalid project ID %j',
  async (projectId) => {
    await expect(createTicket({ projectId, title: 'New' })).rejects.toThrow(
      'プロジェクトID',
    );
  },
);

it.each(['not-an-id', '', '0', '1.5'])(
  'rejects invalid assignee ID %j rather than sending null',
  async (assigneeId) => {
    await expect(
      createTicket({ projectId: '1', title: 'New', assigneeId }),
    ).rejects.toThrow('担当者ID');
  },
);

it('maps snake_case, nullable fields, and numeric assignee IDs', () => {
  expect(toTicket({ ...responseTicket, position: 12 })).toEqual({
    id: '1',
    projectId: '1',
    issueKey: 'TICK-1',
    title: 'First ticket',
    description: null,
    status: 'TODO',
    priority: 'MEDIUM',
    assignee: { id: '7', name: 'Tester', avatarUrl: undefined },
    position: 12,
    version: 1,
    createdAt: responseTicket.created_at,
    updatedAt: responseTicket.updated_at,
  });
  expect(
    toTicket({
      ...responseTicket,
      issue_key: null,
      assignee: null,
      created_at: null,
      updated_at: null,
    }),
  ).toMatchObject({
    issueKey: null,
    assignee: null,
    createdAt: null,
    updatedAt: null,
  });
});

it('reads the data envelope and preserves API order', async () => {
  server.use(
    http.get(`${url}/api/tickets`, ({ request }) => {
      expect(request.credentials).toBe('include');
      return HttpResponse.json({
        data: [responseTicket, { ...responseTicket, id: '2', position: 1 }],
      });
    }),
  );
  expect(
    (await fetchTickets()).map((ticket) => [ticket.id, ticket.position]),
  ).toEqual([
    ['1', 0],
    ['2', 1],
  ]);
});

it.each(['not-an-id', '0', '1.5'])(
  'rejects invalid update assignee ID %j',
  async (assigneeId) => {
    await expect(updateTicket('1', { assigneeId })).rejects.toThrow('担当者ID');
  },
);

it.each([401, 403, 422, 500])('rejects HTTP %s', async (status) => {
  server.use(
    http.get(`${url}/api/tickets`, () =>
      HttpResponse.json({ message: 'Error' }, { status }),
    ),
  );
  await expect(fetchTickets()).rejects.toThrow(String(status));
});

it.each([{}, { data: null }, { data: {} }, []])(
  'rejects invalid list envelopes: %j',
  async (body) => {
    server.use(http.get(`${url}/api/tickets`, () => HttpResponse.json(body)));
    await expect(fetchTickets()).rejects.toThrow();
  },
);

it.each([undefined, null, 0, -1, 1.5, '1', Number.MAX_SAFE_INTEGER + 1])(
  'rejects unsafe or missing response version %j',
  (version) => {
    expect(() =>
      toTicket({ ...responseTicket, version } as typeof responseTicket),
    ).toThrow('バージョン');
  },
);
