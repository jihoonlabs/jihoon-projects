import type { Ticket, TicketPriority, TicketStatus } from '../types/ticket';

export const STATUS_LABELS: Record<TicketStatus, string> = {
  BACKLOG: 'バックログ',
  TODO: 'TODO',
  IN_PROGRESS: '進行中',
  IN_REVIEW: 'レビュー中',
  DONE: '完了',
};

export const PRIORITY_LABELS: Record<TicketPriority, string> = {
  HIGHEST: '最高',
  HIGH: '高',
  MEDIUM: '中',
  LOW: '低',
  LOWEST: '最低',
};

/**
 * 担当者の表示名。未割り当てなら「未割り当て」
 */
export function assigneeLabel(ticket: Ticket): string {
  return ticket.assignee?.name ?? '未割り当て';
}
