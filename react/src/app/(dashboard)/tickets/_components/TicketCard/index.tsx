'use client';

import { Ticket, TicketStatus, useTicketStore } from '@/store/useTicketStore';
import styles from './index.module.scss';

interface TicketCardProps {
  ticket: Ticket;
}

export default function TicketCard({ ticket }: TicketCardProps) {
  const updateStatus = useTicketStore((state) => state.updateStatus);

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    updateStatus(ticket.id, e.target.value as TicketStatus);
  };

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <span className={styles.id}>{ticket.id}</span>
        <span className={`${styles.priority} ${styles[ticket.priority]}`}>
          {ticket.priority}
        </span>
      </div>

      <h3 className={styles.title}>{ticket.title}</h3>
      <p className={styles.description}>{ticket.description}</p>

      <div className={styles.footer}>
        <select
          value={ticket.status}
          onChange={handleStatusChange}
          className={styles.select}
        >
          <option value="TODO">未対応</option>
          <option value="IN_PROGRESS">進行中</option>
          <option value="DONE">完了</option>
        </select>
        <span className={styles.assignee}>担当: {ticket.assignee}</span>
      </div>
    </div>
  );
}