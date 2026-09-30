export type TicketStatus =
  'BACKLOG' | 'TODO' | 'IN_PROGRESS' | 'IN_REVIEW' | 'DONE';

export type TicketPriority = 'HIGHEST' | 'HIGH' | 'MEDIUM' | 'LOW' | 'LOWEST';

export interface UserSummary {
  id: string;
  name: string;
  avatarUrl?: string;
}

export interface Ticket {
  id: string;
  issueKey: string | null;
  title: string;
  description: string | null;
  status: TicketStatus;
  priority: TicketPriority;
  assignee: UserSummary | null;
  position: number;
  createdAt: string | null;
  updatedAt: string | null;
}

export interface CreateTicketInput {
  title: string;
  description?: string | null;
  status?: TicketStatus;
  priority?: TicketPriority;
  assigneeId?: string | null;
}

export interface UpdateTicketInput {
  title?: string;
  description?: string | null;
  status?: TicketStatus;
  priority?: TicketPriority;
  assigneeId?: string | null;
}


export interface TicketComment {
  id: string;
  body: string;
  author: UserSummary;
  createdAt: string | null;
  updatedAt: string | null;
}
