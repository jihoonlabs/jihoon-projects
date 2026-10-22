import './setup';
import { http, HttpResponse } from 'msw';
import { expect, it } from 'vitest';
import {
  createTicket,
  deleteTicket,
  fetchTicket,
  moveTicket,
  updateTicket,
  updateTicketStatus,
  toTicket,
} from '../../ticketApi';
import { responseTicket } from '../ticketFixture';
import { server, url } from './setup';

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
    await createTicket({
      projectId: '1',
      title: 'New',
      description: null,
      assigneeId: '7',
    }),
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
    ticket: toTicket({
      ...responseTicket,
      status: 'IN_PROGRESS',
      position: 2,
    }),
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

it('transmits expected_version, adopts response version, and parses conflict code', async () => {
  server.use(
    http.patch(`${url}/api/tickets/1`, async ({ request }) => {
      expect(await request.json()).toEqual({
        title: 'Conditional',
        expected_version: 4,
      });
      return HttpResponse.json({
        data: { ...responseTicket, title: 'Conditional', version: 5 },
      });
    }),
  );
  expect(
    await updateTicket('1', { title: 'Conditional', expectedVersion: 4 }),
  ).toMatchObject({ version: 5 });
  server.use(
    http.patch(`${url}/api/tickets/1`, () =>
      HttpResponse.json({ code: 'ticket_conflict' }, { status: 409 }),
    ),
  );
  await expect(updateTicket('1', { expectedVersion: 4 })).rejects.toMatchObject(
    { status: 409, code: 'ticket_conflict' },
  );
});

it('fetches detail without caching and forwards cancellation', async () => {
  const controller = new AbortController();
  server.use(
    http.get(`${url}/api/tickets/1`, ({ request }) => {
      expect(request.cache).toBe('no-store');
      return HttpResponse.json({ data: responseTicket });
    }),
  );
  expect(await fetchTicket('1', controller.signal)).toMatchObject({
    version: 1,
  });
  controller.abort();
  await expect(fetchTicket('1', controller.signal)).rejects.toThrow();
});
