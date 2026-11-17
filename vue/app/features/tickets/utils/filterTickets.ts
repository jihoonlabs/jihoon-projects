import type { Ticket } from '../types/ticket';

export type AssigneeFilter = 'ALL' | 'ME' | 'UNASSIGNED';

export const ALL_PROJECTS = 'ALL';

interface TicketFilter {
  searchQuery: string;
  assigneeFilter: AssigneeFilter;
  currentUserId: number | null;
}

/**
 * タイトル・課題キーの検索と担当者の絞り込みを適用する
 */
export function filterTickets(
  tickets: readonly Ticket[],
  { searchQuery, assigneeFilter, currentUserId }: TicketFilter,
): Ticket[] {
  const query = searchQuery.toLowerCase();

  return tickets.filter((ticket) => {
    const matchesSearch =
      ticket.title.toLowerCase().includes(query) ||
      (ticket.issueKey ?? '').toLowerCase().includes(query);

    if (assigneeFilter === 'ME') {
      return (
        matchesSearch &&
        currentUserId !== null &&
        ticket.assignee?.id === String(currentUserId)
      );
    }

    if (assigneeFilter === 'UNASSIGNED') {
      return matchesSearch && !ticket.assignee;
    }

    return matchesSearch;
  });
}

/**
 * 選択中のプロジェクトのチケットだけを返す。
 * 全体表示でも、プロジェクト一覧にないプロジェクトのチケットは表示しない。
 */
export function ticketsInScope(
  tickets: readonly Ticket[],
  selectedProjectId: string,
  availableProjectIds: ReadonlySet<string>,
): Ticket[] {
  return tickets.filter((ticket) =>
    selectedProjectId === ALL_PROJECTS
      ? availableProjectIds.has(ticket.projectId)
      : ticket.projectId === selectedProjectId,
  );
}
