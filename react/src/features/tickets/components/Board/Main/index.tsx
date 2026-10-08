import { INITIAL_COLUMNS } from '../../../mocks/tickets';
import { Ticket, TicketStatus } from '../../../types/ticket';
import Column from '../Column';
import styles from './index.module.css';

interface MainProps {
  tickets: Ticket[];
  projectKey?: string | null;
  searchQuery: string;
  assigneeFilter: string;
  currentUserId: number | null;
  onStatusChange?: (id: string, status: TicketStatus) => void;
  onEdit?: (ticket: Ticket) => void;
  onDelete?: (ticket: Ticket) => void;
  canWrite?: boolean;
  canDrag?: boolean;
}

export default function Main({
  tickets,
  projectKey,
  searchQuery,
  assigneeFilter,
  currentUserId,
  onStatusChange,
  onEdit,
  onDelete,
  canWrite = true,
  canDrag = canWrite,
}: MainProps) {
  const filteredTickets = tickets.filter((ticket) => {
    const matchesSearch =
      ticket.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (ticket.issueKey ?? '').toLowerCase().includes(searchQuery.toLowerCase());

    let matchesAssignee = true;
    if (assigneeFilter === 'ME') {
      matchesAssignee =
        currentUserId !== null && ticket.assignee?.id === String(currentUserId);
    } else if (assigneeFilter === 'UNASSIGNED') {
      matchesAssignee = !ticket.assignee;
    }

    return matchesSearch && matchesAssignee;
  });

  return (
    <main className={styles.container}>
      {INITIAL_COLUMNS.map((column) => {
        const columnTickets = filteredTickets
          .filter((ticket) => ticket.status === column.id)
          .sort((a, b) => a.position - b.position);

        return (
          <Column
            key={column.id}
            column={column}
            tickets={columnTickets}
            projectKey={projectKey}
            onStatusChange={onStatusChange}
            onEdit={onEdit}
            onDelete={onDelete}
            canWrite={canWrite}
            canDrag={canDrag}
          />
        );
      })}
    </main>
  );
}
