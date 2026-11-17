import type { Ticket, TicketStatus } from '../types/ticket';

export interface BoardColumn {
  id: TicketStatus;
  label: string;
}

export const BOARD_COLUMNS: readonly BoardColumn[] = [
  { id: 'BACKLOG', label: 'バックログ' },
  { id: 'TODO', label: '未対応' },
  { id: 'IN_PROGRESS', label: '進行中' },
  { id: 'IN_REVIEW', label: 'レビュー中' },
  { id: 'DONE', label: '完了' },
];

/**
 * チケットを状態ごとの列に分け、各列を position の昇順に並べる（元の配列は変更しない）
 */
export function groupByColumn(
  tickets: readonly Ticket[],
): Array<BoardColumn & { tickets: Ticket[] }> {
  return BOARD_COLUMNS.map((column) => ({
    ...column,
    tickets: tickets
      .filter((ticket) => ticket.status === column.id)
      .sort((a, b) => a.position - b.position),
  }));
}
