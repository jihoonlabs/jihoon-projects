'use client';

import { useTicketStore } from '@/features/tickets/store/useTicketStore';
import TicketCard from '@/features/tickets/components/TicketCard';
import { Header } from '@/shared/components/Header';

import styles from './page.module.css';

export default function TicketsPage() {
  const tickets = useTicketStore((state) => state.tickets);

  const todoTickets = tickets.filter((ticket) => ticket.status === 'TODO');
  const inProgressTickets = tickets.filter(
    (ticket) => ticket.status === 'IN_PROGRESS',
  );
  const doneTickets = tickets.filter((ticket) => ticket.status === 'DONE');

  return (
    <div className={styles.container}>
      <Header />

      <main className={styles.board}>
        <section className={styles.column}>
          <div className={styles.columnTitle}>
            <span>未対応 (TODO)</span>
            <span className={styles.count}>{todoTickets.length}</span>
          </div>

          {todoTickets.map((ticket) => (
            <TicketCard key={ticket.id} ticket={ticket} />
          ))}
        </section>

        <section className={styles.column}>
          <div className={styles.columnTitle}>
            <span>進行中 (IN PROGRESS)</span>
            <span className={styles.count}>{inProgressTickets.length}</span>
          </div>

          {inProgressTickets.map((ticket) => (
            <TicketCard key={ticket.id} ticket={ticket} />
          ))}
        </section>

        <section className={styles.column}>
          <div className={styles.columnTitle}>
            <span>完了 (DONE)</span>
            <span className={styles.count}>{doneTickets.length}</span>
          </div>

          {doneTickets.map((ticket) => (
            <TicketCard key={ticket.id} ticket={ticket} />
          ))}
        </section>
      </main>
    </div>
  );
}