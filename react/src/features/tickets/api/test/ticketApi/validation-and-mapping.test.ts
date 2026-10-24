import { http, HttpResponse } from 'msw';
import { expect, it } from 'vitest';
import {
  createTicket,
  fetchTickets,
  toTicket,
  updateTicket,
} from '../../ticketApi';
import { responseTicket } from '../ticketFixture';
import { server } from '@/test/mocks/server';
import { url } from '../setup';

it('rejects a non-numeric project ID', async () => {
  await expect(
    createTicket({ projectId: 'not-an-id', title: 'New' }),
  ).rejects.toThrow('プロジェクトID');
});

it('rejects zero as a project ID', async () => {
  await expect(createTicket({ projectId: '0', title: 'New' })).rejects.toThrow(
    'プロジェクトID',
  );
});

it('rejects a non-numeric assignee ID instead of sending null', async () => {
  await expect(
    createTicket({ projectId: '1', title: 'New', assigneeId: 'not-an-id' }),
  ).rejects.toThrow('担当者ID');
});

it('rejects zero as an assignee ID instead of sending null', async () => {
  await expect(
    createTicket({ projectId: '1', title: 'New', assigneeId: '0' }),
  ).rejects.toThrow('担当者ID');
});

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

it('rejects a non-numeric update assignee ID', async () => {
  await expect(updateTicket('1', { assigneeId: 'not-an-id' })).rejects.toThrow(
    '担当者ID',
  );
});

it('rejects zero as an update assignee ID', async () => {
  await expect(updateTicket('1', { assigneeId: '0' })).rejects.toThrow(
    '担当者ID',
  );
});

const rejectListFetchWithStatus = async (status: number) => {
  server.use(
    http.get(`${url}/api/tickets`, () =>
      HttpResponse.json({ message: 'Error' }, { status }),
    ),
  );
  await expect(fetchTickets()).rejects.toThrow(String(status));
};

it('rejects an unauthorized ticket list response', () =>
  rejectListFetchWithStatus(401));
it('rejects a forbidden ticket list response', () =>
  rejectListFetchWithStatus(403));
it('rejects a server-error ticket list response', () =>
  rejectListFetchWithStatus(500));

const rejectListEnvelope = async (body: Record<string, unknown>) => {
  server.use(http.get(`${url}/api/tickets`, () => HttpResponse.json(body)));
  await expect(fetchTickets()).rejects.toThrow();
};

it('rejects a ticket list response without a data envelope', () =>
  rejectListEnvelope({}));
it('rejects a ticket list response with null data', () =>
  rejectListEnvelope({ data: null }));
it('rejects a ticket list response with an object instead of a list', () =>
  rejectListEnvelope({ data: {} }));
const rejectsUnsafeVersion = (version: unknown) => {
  expect(() =>
    toTicket({ ...responseTicket, version } as typeof responseTicket),
  ).toThrow('バージョン');
};

it('rejects a missing response version', () => rejectsUnsafeVersion(undefined));
it('rejects zero as a response version', () => rejectsUnsafeVersion(0));
