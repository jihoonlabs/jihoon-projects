import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import {
  createTicket,
  deleteTicket,
  fetchTicket,
  fetchTickets,
  moveTicket,
  toTicket,
  updateTicket,
  updateTicketStatus,
} from '../ticketApi';
import { responseTicket } from './ticketFixture';

const url = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

describe('Ticket API boundary', () => {
  it.each(['not-an-id', '', '0', '1.5'])(
    'rejects invalid project ID %j',
    async (projectId) => {
      await expect(createTicket({ projectId, title: 'New' })).rejects.toThrow('プロジェクトID');
    },
  );
  it.each(['not-an-id', '', '0', '1.5'])(
    'rejects invalid assignee ID %j rather than sending null',
    async (assigneeId) => {
      await expect(createTicket({ projectId: '1', title: 'New', assigneeId })).rejects.toThrow(
        '担当者ID',
      );
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
  it('maps detail and PATCH responses through the same boundary', async () => {
    server.use(
      http.get(`${url}/api/tickets/1`, () =>
        HttpResponse.json({ data: responseTicket }),
      ),
      http.patch(`${url}/api/tickets/1`, async ({ request }) => {
        expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
        expect(await request.json()).toEqual({ status: 'DONE' });
        return HttpResponse.json({
          data: { ...responseTicket, status: 'DONE', updated_at: 'new-date' },
        });
      }),
    );
    expect(await fetchTicket('1')).toMatchObject({ issueKey: 'TICK-1' });
    expect(await updateTicketStatus('1', 'DONE')).toMatchObject({
      status: 'DONE',
      updatedAt: 'new-date',
    });
  });
  it('sends assignee_id rather than the display object and preserves server defaults', async () => {
    server.use(
      http.post(`${url}/api/tickets`, async ({ request }) => {
        expect(request.credentials).toBe('include');
        expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
        expect(await request.json()).toEqual({
          project_id: 1,
          title: 'New',
          description: null,
          assignee_id: 7,
        });
        return HttpResponse.json(
          { data: { ...responseTicket, title: 'New' } },
          { status: 201 },
        );
      }),
    );
    expect(
      await createTicket({ projectId: '1', title: 'New', description: null, assigneeId: '7' }),
    ).toMatchObject({ title: 'New', issueKey: 'TICK-1' });
  });
  it('sends editable ticket fields through PATCH', async () => {
    server.use(
      http.patch(`${url}/api/tickets/1`, async ({ request }) => {
        expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
        expect(await request.json()).toEqual({
          title: 'Updated',
          description: 'Details',
          status: 'IN_REVIEW',
          priority: 'HIGH',
          assignee_id: 7,
        });
        return HttpResponse.json({
          data: {
            ...responseTicket,
            title: 'Updated',
            description: 'Details',
            status: 'IN_REVIEW',
            priority: 'HIGH',
          },
        });
      }),
    );

    await expect(
      updateTicket('1', {
        title: 'Updated',
        description: 'Details',
        status: 'IN_REVIEW',
        priority: 'HIGH',
        assigneeId: '7',
      }),
    ).resolves.toMatchObject({
      title: 'Updated',
      description: 'Details',
      status: 'IN_REVIEW',
      priority: 'HIGH',
    });
  });

  it.each(['not-an-id', '0', '1.5'])(
    'rejects invalid update assignee ID %j',
    async (assigneeId) => {
      await expect(updateTicket('1', { assigneeId })).rejects.toThrow(
        '担当者ID',
      );
    },
  );

  it('does not interpret DELETE message as a Ticket', async () => {
    server.use(
      http.delete(`${url}/api/tickets/1`, () =>
        HttpResponse.json({ message: 'Deleted' }),
      ),
    );
    await expect(deleteTicket('1')).resolves.toBeUndefined();
  });
  it('sends a versioned move and maps the authoritative board version', async () => {
    server.use(
      http.patch(`${url}/api/tickets/1/move`, async ({ request }) => {
        expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
        expect(await request.json()).toEqual({
          status: 'IN_PROGRESS',
          position: 2,
          board_version: 4,
        });
        return HttpResponse.json({
          data: { ...responseTicket, status: 'IN_PROGRESS', position: 2 },
          board_version: 5,
        });
      }),
    );

    await expect(moveTicket('1', 'IN_PROGRESS', 2, 4)).resolves.toEqual({
      ticket: toTicket({ ...responseTicket, status: 'IN_PROGRESS', position: 2 }),
      boardVersion: 5,
    });
  });
  it('preserves a stale board conflict as a 409 API error', async () => {
    server.use(
      http.patch(`${url}/api/tickets/1/move`, () =>
        HttpResponse.json({ message: 'stale' }, { status: 409 }),
      ),
    );

    await expect(moveTicket('1', 'DONE', 0, 4)).rejects.toMatchObject({
      status: 409,
    });
  });
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
});
