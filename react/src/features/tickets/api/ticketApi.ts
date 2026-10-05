import { fetchWithCsrf } from '@/shared/api/fetchWithCsrf';
import type {
  CreateTicketInput,
  Ticket,
  TicketPriority,
  TicketStatus,
  UpdateTicketInput,
} from '../types/ticket';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

// Transport contract: Laravel Resource envelopes contain snake_case fields.
export interface TicketResponse {
  id: string;
  project_id: string;
  issue_key: string | null;
  title: string;
  description: string | null;
  status: TicketStatus;
  position: number;
  priority: TicketPriority;
  assignee: { id: number; name: string; avatar_url: string | null } | null;
  created_at: string | null;
  updated_at: string | null;
}

export function toTicket(data: TicketResponse): Ticket {
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
  return data.map(toTicket);
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
  const projectId = Number(input.projectId);
  if (!Number.isSafeInteger(projectId) || projectId <= 0) {
    throw new Error('プロジェクトIDが不正です。');
  }
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
          project_id: projectId,
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

export async function updateTicket(
  id: string,
  input: UpdateTicketInput,
): Promise<Ticket> {
  const assigneeId =
    input.assigneeId === undefined
      ? undefined
      : input.assigneeId === null
        ? null
        : Number(input.assigneeId);

  if (
    assigneeId !== undefined &&
    assigneeId !== null &&
    (!Number.isSafeInteger(assigneeId) || assigneeId <= 0)
  ) {
    throw new Error('担当者IDが不正です。');
  }

  const body = {
    ...(input.title !== undefined ? { title: input.title } : {}),
    ...(input.description !== undefined
      ? { description: input.description }
      : {}),
    ...(input.status !== undefined ? { status: input.status } : {}),
    ...(input.priority !== undefined ? { priority: input.priority } : {}),
    ...(assigneeId !== undefined ? { assignee_id: assigneeId } : {}),
  };

  return toTicket(
    await resource<TicketResponse>(
      await fetchWithCsrf(`/api/tickets/${encodeURIComponent(id)}`, {
        method: 'PATCH',
        body: JSON.stringify(body),
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


export interface MoveTicketResult {
  ticket: Ticket;
  boardVersion: number;
}

export async function moveTicket(
  id: string,
  status: TicketStatus,
  position: number,
  boardVersion: number,
): Promise<MoveTicketResult> {
  const response = await fetchWithCsrf(`/api/tickets/${encodeURIComponent(id)}/move`, {
    method: 'PATCH',
    body: JSON.stringify({
      status,
      position,
      board_version: boardVersion,
    }),
  });

  if (response.status === 409) {
    throw new Error('ボードが更新されています。最新の状態を再取得します。');
  }
  if (!response.ok) {
    throw new Error(`チケットの移動に失敗しました (${response.status})`);
  }

  const result = await response.json();
  if (
    !result ||
    typeof result !== 'object' ||
    !('data' in result) ||
    !('board_version' in result) ||
    typeof result.board_version !== 'number'
  ) {
    throw new Error('チケット移動APIの応答形式が不正です。');
  }

  return {
    ticket: toTicket(result.data as TicketResponse),
    boardVersion: result.board_version,
  };
}
