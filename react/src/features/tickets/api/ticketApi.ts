import { fetchWithCsrf } from '@/shared/api/fetchWithCsrf';
import type {
  CreateTicketInput,
  Ticket,
  TicketPriority,
  TicketStatus,
} from '../types/ticket';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

// Transport contract: Laravel Resource envelopes contain snake_case fields.
export interface TicketResponse {
  id: string;
  issue_key: string | null;
  title: string;
  description: string | null;
  status: TicketStatus;
  priority: TicketPriority;
  assignee: { id: number; name: string; avatar_url: string | null } | null;
  created_at: string | null;
  updated_at: string | null;
}

export function toTicket(data: TicketResponse, position = 0): Ticket {
  return {
    id: String(data.id),
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
    position,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

async function resource<T>(response: Response): Promise<T> {
  if (!response.ok)
    throw new Error(`チケット操作に失敗しました (${response.status})`);
  const result = await response.json();
  if (
    !result ||
    typeof result !== 'object' ||
    !('data' in result) ||
    result.data == null
  ) {
    throw new Error('チケットAPIの応答形式が不正です。');
  }
  return result.data as T;
}

export async function fetchTickets(): Promise<Ticket[]> {
  const data = await resource<TicketResponse[]>(
    await fetch(`${API_URL}/api/tickets`, {
      credentials: 'include',
      headers: { Accept: 'application/json' },
    }),
  );
  if (!Array.isArray(data))
    throw new Error('チケット一覧の応答形式が不正です。');
  return data.map((ticket, index) => toTicket(ticket, index));
}

export async function fetchTicket(id: string): Promise<Ticket> {
  return toTicket(
    await resource<TicketResponse>(
      await fetch(`${API_URL}/api/tickets/${encodeURIComponent(id)}`, {
        credentials: 'include',
        headers: { Accept: 'application/json' },
      }),
    ),
  );
}

export async function createTicket(input: CreateTicketInput): Promise<Ticket> {
  const assigneeId = input.assigneeId == null ? null : Number(input.assigneeId);
  if (
    assigneeId !== null &&
    (!Number.isSafeInteger(assigneeId) || assigneeId <= 0)
  ) {
    throw new Error('担当者IDが不正です。');
  }
  return toTicket(
    await resource<TicketResponse>(
      await fetchWithCsrf('/api/tickets', {
        method: 'POST',
        body: JSON.stringify({
          title: input.title,
          description: input.description,
          status: input.status,
          priority: input.priority,
          assignee_id: assigneeId,
        }),
      }),
    ),
  );
}

export async function updateTicketStatus(
  id: string,
  status: TicketStatus,
): Promise<Ticket> {
  return toTicket(
    await resource<TicketResponse>(
      await fetchWithCsrf(`/api/tickets/${encodeURIComponent(id)}`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      }),
    ),
  );
}

export async function deleteTicket(id: string): Promise<void> {
  const response = await fetchWithCsrf(
    `/api/tickets/${encodeURIComponent(id)}`,
    { method: 'DELETE' },
  );
  if (!response.ok)
    throw new Error(`チケットの削除に失敗しました (${response.status})`);
}
