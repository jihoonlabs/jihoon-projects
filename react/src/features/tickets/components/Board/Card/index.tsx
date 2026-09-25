'use client';

import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Ticket } from '@/features/tickets/types/ticket';
import styles from './index.module.css';

interface CardProps {
  ticket: Ticket;
  isOverlay?: boolean;
}

const PRIORITY_LABELS: Record<string, string> = {
  HIGHEST: '最高',
  HIGH: '高',
  MEDIUM: '中',
  LOW: '低',
  LOWEST: '最低',
};

export default function Card({ ticket, isOverlay }: CardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: ticket.id });

  const style = {
    transform: CSS.Translate.toString(transform),
    transition,
    opacity: isDragging ? 0.3 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`${styles.card} ${isOverlay ? styles.overlayCard : ''}`}
    >
      <p className={styles.title}>{ticket.title}</p>

      <div className={styles.footer}>
        <div className={styles.metaInfo}>
          <span className={styles.issueKey}>{ticket.issueKey}</span>
          <span
            className={`${styles.priorityBadge} ${styles[ticket.priority]}`}
          >
            {PRIORITY_LABELS[ticket.priority] || ticket.priority}
          </span>
        </div>

        {ticket.assignee ? (
          <div className={styles.avatar} title={ticket.assignee.name}>
            {ticket.assignee.name.charAt(0)}
          </div>
        ) : (
          <div
            className={`${styles.avatar} ${styles.unassigned}`}
            title="未割り当て"
          >
            ?
          </div>
        )}
      </div>
    </div>
  );
}
