export type TicketStatus =
  'BACKLOG' | 'TODO' | 'IN_PROGRESS' | 'IN_REVIEW' | 'DONE';

export type TicketPriority = 'HIGHEST' | 'HIGH' | 'MEDIUM' | 'LOW' | 'LOWEST';

export interface UserSummary {
  id: string;
  name: string;
  avatarUrl?: string;
}

/**
 * 画面で扱うチケット
 */
export interface Ticket {
  id: string;
  projectId: string;
  issueKey: string | null;
  title: string;
  description: string | null;
  status: TicketStatus;
  priority: TicketPriority;
  assignee: UserSummary | null;
  position: number;
  version: number;
  createdAt: string | null;
  updatedAt: string | null;
}

/**
 * Laravel の TicketResource が返すチケット（snake_case。担当者 ID だけ数値で届く）
 */
export interface TicketResponse {
  id: string;
  project_id: string;
  issue_key: string | null;
  title: string;
  description: string | null;
  status: TicketStatus;
  position: number;
  version: number;
  priority: TicketPriority;
  assignee: { id: number; name: string; avatar_url: string | null } | null;
  created_at: string | null;
  updated_at: string | null;
}

/**
 * チケット作成の入力（画面側の値。ID は文字列）
 */
export interface CreateTicketInput {
  projectId: string;
  title: string;
  description?: string | null;
  status?: TicketStatus;
  priority?: TicketPriority;
  assigneeId?: string | null;
}

/**
 * チケット更新の入力。未指定の項目は送らない。
 * expectedVersion を渡すと、別の人が先に更新していた場合に 409 で止まる。
 */
export interface UpdateTicketInput {
  expectedVersion?: number;
  title?: string;
  description?: string | null;
  status?: TicketStatus;
  priority?: TicketPriority;
  assigneeId?: string | null;
}
