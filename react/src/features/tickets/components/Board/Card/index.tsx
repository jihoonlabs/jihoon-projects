'use client';

import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Ticket, TicketStatus } from '@/features/tickets/types/ticket';
import styles from './index.module.css';

interface CardProps {
  ticket: Ticket;
  isOverlay?: boolean;
  onStatusChange?: (id: string, status: TicketStatus) => void;
  onEdit?: (ticket: Ticket) => void;
  onDelete?: (ticket: Ticket) => void;
  canWrite?: boolean;
  canDrag?: boolean;
}

const PRIORITY_LABELS: Record<string, string> = {
  HIGHEST: '最高', HIGH: '高', MEDIUM: '中', LOW: '低', LOWEST: '最低',
};

const STATUS_LABELS: Record<TicketStatus, string> = {
  BACKLOG: 'バックログ',
  TODO: 'TODO',
  IN_PROGRESS: '進行中',
  IN_REVIEW: 'レビュー中',
  DONE: '完了',
};

export default function Card({
  ticket,
  isOverlay,
  onStatusChange,
  onEdit,
  onDelete,
  canWrite = true,
  canDrag = canWrite,
}: CardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: ticket.id, disabled: !canDrag });

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

      {!isOverlay && (
        <div
          className={styles.controls}
          onPointerDown={(event) => event.stopPropagation()}
        >
          {canWrite && <select
            aria-label={`${ticket.title} のステータス`}
            value={ticket.status}
            onChange={(event) =>
              onStatusChange?.(ticket.id, event.target.value as TicketStatus)
            }
          >
            {Object.entries(STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>}
          <button type="button" onClick={() => onEdit?.(ticket)}>{canWrite ? '編集' : '詳細'}</button>
          {canWrite && <button type="button" onClick={() => onDelete?.(ticket)}>削除</button>}
        </div>
      )}

      <div className={styles.footer}>
        <div className={styles.metaInfo}>
          <span className={styles.issueKey}>{ticket.issueKey ?? '—'}</span>
          <span className={`${styles.priorityBadge} ${styles[ticket.priority]}`}>
            {PRIORITY_LABELS[ticket.priority] || ticket.priority}
          </span>
        </div>

        {ticket.assignee ? (
          <div className={styles.avatar} title={ticket.assignee.name}>
            {ticket.assignee.name.charAt(0)}
          </div>
        ) : (
          <div className={`${styles.avatar} ${styles.unassigned}`} title="未割り当て">?</div>
        )}
      </div>
    </div>
  );
}
