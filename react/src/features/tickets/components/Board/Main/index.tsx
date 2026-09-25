import { INITIAL_COLUMNS } from '../../../mocks/tickets';
import { Ticket } from '../../../types/ticket';
import Column from '../Column';
import styles from './index.module.css';

interface MainProps {
  tickets: Ticket[];
  searchQuery: string;
  assigneeFilter: string;
}

export default function Main({
  tickets,
  searchQuery,
  assigneeFilter,
}: MainProps) {
  const filteredTickets = tickets.filter((ticket) => {
    const matchesSearch =
      ticket.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ticket.issueKey.toLowerCase().includes(searchQuery.toLowerCase());

    let matchesAssignee = true;
    if (assigneeFilter === 'ME') {
      matchesAssignee = ticket.assignee?.id === '1';
    } else if (assigneeFilter === 'UNASSIGNED') {
      matchesAssignee = !ticket.assignee;
    }

    return matchesSearch && matchesAssignee;
  });

  return (
    <main className={styles.container}>
      {INITIAL_COLUMNS.map((column) => {
        const columnTickets = filteredTickets.filter(
          (ticket) => ticket.status === column.id,
        );

        return (
          <Column key={column.id} column={column} tickets={columnTickets} />
        );
      })}
    </main>
  );
}
