import { http, HttpResponse } from 'msw';

import type {
  ProjectMemberResponse,
  ProjectResponse,
} from '~/features/tickets/types/project';
import type { TicketResponse } from '~/features/tickets/types/ticket';

import { apiUrl } from '../apiUrl';

/**
 * チケット・プロジェクト API の応答。各テストで overrideApi に渡して使う。
 */
export const ticketApi = {
  ticket(ticket: TicketResponse) {
    return http.get(apiUrl(`/api/tickets/${ticket.id}`), () =>
      HttpResponse.json({ data: ticket }),
    );
  },

  updateTicket(id: string, response: TicketResponse | { status: number; code: string }) {
    return http.patch(apiUrl(`/api/tickets/${id}`), () =>
      'data' in response
        ? HttpResponse.json({ data: response })
        : HttpResponse.json(
            { code: response.code, message: 'conflict' },
            { status: response.status },
          ),
    );
  },

  tickets(tickets: TicketResponse[]) {
    return http.get(apiUrl('/api/tickets'), () =>
      HttpResponse.json({ data: tickets }),
    );
  },

  ticketsFail(status: number) {
    return http.get(apiUrl('/api/tickets'), () =>
      HttpResponse.json({ message: 'Error' }, { status }),
    );
  },

  projects(projects: ProjectResponse[]) {
    return http.get(apiUrl('/api/projects'), () =>
      HttpResponse.json({ data: projects }),
    );
  },

  projectsFail(status: number) {
    return http.get(apiUrl('/api/projects'), () =>
      HttpResponse.json({ message: 'Error' }, { status }),
    );
  },

  members(projectId: string, members: ProjectMemberResponse[]) {
    return http.get(apiUrl(`/api/projects/${projectId}/members`), () =>
      HttpResponse.json({ data: members }),
    );
  },

  membersFail(projectId: string, status: number) {
    return http.get(apiUrl(`/api/projects/${projectId}/members`), () =>
      HttpResponse.json({ message: 'Error' }, { status }),
    );
  },
};
