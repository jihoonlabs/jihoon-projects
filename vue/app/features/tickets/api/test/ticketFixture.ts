import type { TicketResponse } from '../../types/ticket';

/**
 * Laravel の TicketResource と同じ形のチケット
 */
export function ticketFixture(
  overrides: Partial<TicketResponse> = {},
): TicketResponse {
  return {
    id: '1',
    project_id: '1',
    issue_key: 'TICK-1',
    title: 'First ticket',
    description: null,
    status: 'TODO',
    position: 0,
    version: 1,
    priority: 'MEDIUM',
    assignee: { id: 7, name: 'Tester', avatar_url: null },
    created_at: '2026-11-01T00:00:00+00:00',
    updated_at: '2026-11-01T00:00:00+00:00',
    ...overrides,
  };
}
