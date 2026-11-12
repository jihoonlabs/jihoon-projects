import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import {
  createTicketComment,
  deleteTicketComment,
  fetchTicketComments,
  updateTicketComment,
} from '../ticketCommentApi';

const url = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const responseComment = {
  id: '10',
  body: 'first comment',
  author: { id: 7, name: 'Tester', avatar_url: null },
  created_at: '2026-09-30T00:00:00.000000Z',
  updated_at: '2026-09-30T00:00:00.000000Z',
};

describe('チケットコメントAPI', () => {
  it('取得したコメントを画面用の形式に変換する', async () => {
    server.use(
      http.get(`${url}/api/tickets/1/comments`, ({ request }) => {
        expect(request.credentials).toBe('include');
        return HttpResponse.json({ data: [responseComment] });
      }),
    );

    await expect(fetchTicketComments('1')).resolves.toEqual([
      {
        id: '10',
        body: 'first comment',
        author: { id: '7', name: 'Tester', avatarUrl: undefined },
        createdAt: responseComment.created_at,
        updatedAt: responseComment.updated_at,
      },
    ]);
  });

  it('コメントの投稿と更新にCSRF保護を適用する', async () => {
    server.use(
      http.post(`${url}/api/tickets/1/comments`, async ({ request }) => {
        expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
        expect(await request.json()).toEqual({ body: 'new comment' });
        return HttpResponse.json(
          { data: { ...responseComment, body: 'new comment' } },
          { status: 201 },
        );
      }),
      http.patch(`${url}/api/tickets/1/comments/10`, async ({ request }) => {
        expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
        expect(await request.json()).toEqual({ body: 'updated comment' });
        return HttpResponse.json({
          data: { ...responseComment, body: 'updated comment' },
        });
      }),
    );

    await expect(
      createTicketComment('1', 'new comment'),
    ).resolves.toMatchObject({ body: 'new comment' });
    await expect(
      updateTicketComment('1', '10', 'updated comment'),
    ).resolves.toMatchObject({ body: 'updated comment' });
  });

  it('コメントを削除する', async () => {
    server.use(
      http.delete(`${url}/api/tickets/1/comments/10`, ({ request }) => {
        expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
        return new HttpResponse(null, { status: 204 });
      }),
    );

    await expect(deleteTicketComment('1', '10')).resolves.toBeUndefined();
  });

  const rejectsListRequestWithStatus = async (status: number) => {
    server.use(
      http.get(`${url}/api/tickets/1/comments`, () =>
        HttpResponse.json({ message: 'Error' }, { status }),
      ),
    );
    await expect(fetchTicketComments('1')).rejects.toThrow(String(status));
  };

  it('コメント一覧の401レスポンスをエラーにする', () =>
    rejectsListRequestWithStatus(401));
  it('コメント一覧の403レスポンスをエラーにする', () =>
    rejectsListRequestWithStatus(403));
  it('コメント一覧の422レスポンスをエラーにする', () =>
    rejectsListRequestWithStatus(422));
  it('コメント一覧の500レスポンスをエラーにする', () =>
    rejectsListRequestWithStatus(500));

  const rejectsInvalidListEnvelope = async (body: Record<string, unknown>) => {
    server.use(
      http.get(`${url}/api/tickets/1/comments`, () => HttpResponse.json(body)),
    );
    await expect(fetchTicketComments('1')).rejects.toThrow();
  };

  it('dataがないコメント一覧レスポンスを拒否する', () =>
    rejectsInvalidListEnvelope({}));
  it('dataがnullのコメント一覧レスポンスを拒否する', () =>
    rejectsInvalidListEnvelope({ data: null }));
  it('dataが配列でなくオブジェクトのコメント一覧レスポンスを拒否する', () =>
    rejectsInvalidListEnvelope({ data: {} }));
});
