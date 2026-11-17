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
