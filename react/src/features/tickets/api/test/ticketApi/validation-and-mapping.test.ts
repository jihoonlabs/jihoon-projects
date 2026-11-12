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

it('数値でないプロジェクトIDを拒否する', async () => {
  await expect(
    createTicket({ projectId: 'not-an-id', title: 'New' }),
  ).rejects.toThrow('プロジェクトID');
});

it('プロジェクトIDが0の場合は拒否する', async () => {
  await expect(createTicket({ projectId: '0', title: 'New' })).rejects.toThrow(
    'プロジェクトID',
  );
});

it('数値でない担当者IDをnullに変えずに拒否する', async () => {
  await expect(
    createTicket({ projectId: '1', title: 'New', assigneeId: 'not-an-id' }),
  ).rejects.toThrow('担当者ID');
});

it('担当者IDが0の場合はnullに変えずに拒否する', async () => {
  await expect(
    createTicket({ projectId: '1', title: 'New', assigneeId: '0' }),
  ).rejects.toThrow('担当者ID');
});

it('snake_caseの項目、nullを許す項目、数値の担当者IDを変換する', () => {
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

it('レスポンスのdataからチケットを取り出し、APIが返した順序を保つ', async () => {
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

it('更新時に数値でない担当者IDを拒否する', async () => {
  await expect(updateTicket('1', { assigneeId: 'not-an-id' })).rejects.toThrow(
    '担当者ID',
  );
});

it('更新時に担当者IDが0の場合は拒否する', async () => {
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

it('チケット一覧の401レスポンスをエラーにする', () =>
  rejectListFetchWithStatus(401));
it('チケット一覧の403レスポンスをエラーにする', () =>
  rejectListFetchWithStatus(403));
it('チケット一覧の500レスポンスをエラーにする', () =>
  rejectListFetchWithStatus(500));

const rejectListEnvelope = async (body: Record<string, unknown>) => {
  server.use(http.get(`${url}/api/tickets`, () => HttpResponse.json(body)));
  await expect(fetchTickets()).rejects.toThrow();
};

it('dataがないチケット一覧レスポンスを拒否する', () => rejectListEnvelope({}));
it('dataがnullのチケット一覧レスポンスを拒否する', () =>
  rejectListEnvelope({ data: null }));
it('dataが配列でなくオブジェクトのチケット一覧レスポンスを拒否する', () =>
  rejectListEnvelope({ data: {} }));
const rejectsUnsafeVersion = (version: unknown) => {
  expect(() =>
    toTicket({ ...responseTicket, version } as typeof responseTicket),
  ).toThrow('バージョン');
};

it('レスポンスにバージョンがなければ拒否する', () =>
  rejectsUnsafeVersion(undefined));
it('レスポンスのバージョンが0なら拒否する', () => rejectsUnsafeVersion(0));
