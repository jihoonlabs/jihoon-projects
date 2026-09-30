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

describe('Ticket comment API boundary', () => {
  it('fetches and maps comments', async () => {
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

  it('creates and updates comments with CSRF', async () => {
    server.use(
      http.post(`${url}/api/tickets/1/comments`, async ({ request }) => {
        expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
        expect(await request.json()).toEqual({ body: 'new comment' });
        return HttpResponse.json({ data: { ...responseComment, body: 'new comment' } }, { status: 201 });
      }),
      http.patch(`${url}/api/tickets/1/comments/10`, async ({ request }) => {
        expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
        expect(await request.json()).toEqual({ body: 'updated comment' });
        return HttpResponse.json({ data: { ...responseComment, body: 'updated comment' } });
      }),
    );

    await expect(createTicketComment('1', 'new comment')).resolves.toMatchObject({ body: 'new comment' });
    await expect(updateTicketComment('1', '10', 'updated comment')).resolves.toMatchObject({ body: 'updated comment' });
  });

  it('deletes a comment', async () => {
    server.use(
      http.delete(`${url}/api/tickets/1/comments/10`, ({ request }) => {
        expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
        return new HttpResponse(null, { status: 204 });
      }),
    );

    await expect(deleteTicketComment('1', '10')).resolves.toBeUndefined();
  });

  it.each([401, 403, 422, 500])('rejects HTTP %s', async (status) => {
    server.use(
      http.get(`${url}/api/tickets/1/comments`, () =>
        HttpResponse.json({ message: 'Error' }, { status }),
      ),
    );
    await expect(fetchTicketComments('1')).rejects.toThrow(String(status));
  });

  it.each([{}, { data: null }, { data: {} }])('rejects invalid list envelope %j', async (body) => {
    server.use(http.get(`${url}/api/tickets/1/comments`, () => HttpResponse.json(body)));
    await expect(fetchTicketComments('1')).rejects.toThrow();
  });
});
