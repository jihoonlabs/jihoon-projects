import type { TicketResponse } from '../ticketApi';

export const responseTicket: TicketResponse = {
  id: '1',
  project_id: '1',
  issue_key: 'TICK-1',
  title: 'First ticket',
  description: null,
  status: 'TODO',
  priority: 'MEDIUM',
  assignee: { id: 7, name: 'Tester', avatar_url: null },
  created_at: '2026-09-24T00:00:00.000000Z',
  updated_at: '2026-09-24T00:00:00.000000Z',
};
