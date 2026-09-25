'use client';

import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Ticket } from '@/features/tickets/types/ticket';
import styles from './index.module.css';

interface CardProps {
  ticket: Ticket;
  isOverlay?: boolean;
  onEdit?: (ticket: Ticket) => void;
  onDelete?: (id: string, title: string) => void;
}

const PRIORITY_LABELS: Record<string, string> = {
  HIGHEST: '最高',
  HIGH: '高',
  MEDIUM: '中',
  LOW: '低',
  LOWEST: '最低',
};

export default function Card({ ticket, isOverlay, onEdit, onDelete }: CardProps) {
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

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation(); // DnD 드래그 이벤트 전파 방지
    onEdit?.(ticket);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation(); // DnD 드래그 이벤트 전파 방지
    onDelete?.(ticket.id, ticket.title);
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`${styles.card} ${isOverlay ? styles.overlayCard : ''}`}
    >
      <div className={styles.cardHeader}>
        <p className={styles.title}>{ticket.title}</p>
        <div className={styles.actionButtons}>
          {onEdit && (
            <button
              type="button"
              className={styles.iconButton}
              onClick={handleEdit}
              title="編集"
              aria-label="編集"
            >
              ✏️
            </button>
          )}
          {onDelete && (
            <button
              type="button"
              className={`${styles.iconButton} ${styles.deleteBtn}`}
              onClick={handleDelete}
              title="削除"
              aria-label="削除"
            >
              🗑️
            </button>
          )}
        </div>
      </div>

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