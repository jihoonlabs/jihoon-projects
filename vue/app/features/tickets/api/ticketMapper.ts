import type { Ticket, TicketResponse } from '../types/ticket';
import { TicketApiError } from './apiErrors';

/**
 * Laravel のチケット応答を画面用の形に変換する。
 * 更新の競合判定に使う version が不正な応答は、後の更新を壊すため受け付けない。
 */
export function toTicket(data: TicketResponse): Ticket {
  if (!Number.isSafeInteger(data.version) || data.version < 1) {
    throw new TicketApiError('チケットのバージョンが不正です。');
  }

  return {
    id: String(data.id),
    projectId: String(data.project_id),
    issueKey: data.issue_key,
    title: data.title,
    description: data.description,
    status: data.status,
    priority: data.priority,
    assignee:
      data.assignee === null
        ? null
        : {
            id: String(data.assignee.id),
            name: data.assignee.name,
            avatarUrl: data.assignee.avatar_url ?? undefined,
          },
    position: data.position,
    version: data.version,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}
