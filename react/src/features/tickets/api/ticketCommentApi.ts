import { fetchWithCsrf } from '@/shared/api/fetchWithCsrf';
import type { TicketComment } from '../types/ticket';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface TicketCommentResponse {
  id: string;
  body: string;
  author: { id: number; name: string; avatar_url: string | null };
  created_at: string | null;
  updated_at: string | null;
}

function toComment(data: TicketCommentResponse): TicketComment {
  return {
    id: String(data.id),
    body: data.body,
    author: {
      id: String(data.author.id),
      name: data.author.name,
      avatarUrl: data.author.avatar_url ?? undefined,
    },
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

async function data<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`コメント操作に失敗しました (${response.status})`);
  }
  const result = await response.json();
  if (!result || typeof result !== 'object' || !('data' in result)) {
    throw new Error('コメントAPIの応答形式が不正です。');
  }
  return result.data as T;
}

export async function fetchTicketComments(ticketId: string): Promise<TicketComment[]> {
  const comments = await data<TicketCommentResponse[]>(
    await fetch(`${API_URL}/api/tickets/${encodeURIComponent(ticketId)}/comments`, {
      credentials: 'include',
      headers: { Accept: 'application/json' },
    }),
  );
  if (!Array.isArray(comments)) throw new Error('コメント一覧の応答形式が不正です。');
  return comments.map(toComment);
}

export async function createTicketComment(ticketId: string, body: string): Promise<TicketComment> {
  return toComment(await data<TicketCommentResponse>(
    await fetchWithCsrf(`/api/tickets/${encodeURIComponent(ticketId)}/comments`, {
      method: 'POST',
      body: JSON.stringify({ body }),
    }),
  ));
}

export async function updateTicketComment(ticketId: string, commentId: string, body: string): Promise<TicketComment> {
  return toComment(await data<TicketCommentResponse>(
    await fetchWithCsrf(`/api/tickets/${encodeURIComponent(ticketId)}/comments/${encodeURIComponent(commentId)}`, {
      method: 'PATCH',
      body: JSON.stringify({ body }),
    }),
  ));
}

export async function deleteTicketComment(ticketId: string, commentId: string): Promise<void> {
  const response = await fetchWithCsrf(
    `/api/tickets/${encodeURIComponent(ticketId)}/comments/${encodeURIComponent(commentId)}`,
    { method: 'DELETE' },
  );
  if (!response.ok) throw new Error(`コメントの削除に失敗しました (${response.status})`);
}
