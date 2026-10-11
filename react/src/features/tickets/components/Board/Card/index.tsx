'use client';

import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { CSSProperties } from 'react';
import { Ticket, TicketStatus } from '@/features/tickets/types/ticket';
import { getProjectBorderColor } from '@/features/tickets/utils/projectColor';
import styles from './index.module.css';

interface CardProps {
  ticket: Ticket;
  projectKey?: string | null;
  isOverlay?: boolean;
  onStatusChange?: (id: string, status: TicketStatus) => void;
  onOpenDetails?: (ticket: Ticket, trigger: HTMLButtonElement) => void;
  canWrite?: boolean;
  canDrag?: boolean;
}

const PRIORITY_LABELS: Record<string, string> = {
  HIGHEST: '最高',
  HIGH: '高',
  MEDIUM: '中',
  LOW: '低',
  LOWEST: '最低',
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
  projectKey = null,
  isOverlay,
  onStatusChange,
  onOpenDetails,
  canWrite = true,
  canDrag = canWrite,
}: CardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: ticket.id, disabled: !canDrag });

  const style: CSSProperties & { '--project-border-color'?: string } = {
    transform: CSS.Translate.toString(transform),
    transition,
    opacity: isDragging ? 0.3 : 1,
    '--project-border-color': getProjectBorderColor(projectKey) ?? undefined,
  };

  return (
    <article
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      aria-disabled={undefined}
      role="group"
      aria-label={
        ticket.issueKey ? `${ticket.issueKey}: ${ticket.title}` : ticket.title
      }
      className={`${styles.card} ${!canDrag ? styles.staticCard : ''} ${isOverlay ? styles.overlayCard : ''}`}
    >
      <div className={styles.heading}>
        <button
          type="button"
          className={styles.title}
          aria-label={`${ticket.issueKey ?? ticket.title} の詳細を開く`}
          onPointerDown={(event) => event.stopPropagation()}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ')
              event.stopPropagation();
          }}
          onClick={(event) => onOpenDetails?.(ticket, event.currentTarget)}
        >
          {ticket.title}
        </button>
        {!isOverlay && (
          <button
            type="button"
            className={styles.detailsButton}
            onPointerDown={(event) => event.stopPropagation()}
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ')
                event.stopPropagation();
            }}
            onClick={(event) => onOpenDetails?.(ticket, event.currentTarget)}
          >
            詳細
          </button>
        )}
      </div>

      {!isOverlay && (
        <div
          className={styles.controls}
          onPointerDown={(event) => event.stopPropagation()}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ')
              event.stopPropagation();
          }}
        >
          {canWrite && (
            <select
              aria-label={`${ticket.title} のステータス`}
              value={ticket.status}
              onChange={(event) =>
                onStatusChange?.(ticket.id, event.target.value as TicketStatus)
              }
            >
              {Object.entries(STATUS_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          )}
        </div>
      )}

      <div className={styles.footer}>
        <div className={styles.metaInfo}>
          <span className={styles.issueKey}>{ticket.issueKey ?? '—'}</span>
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
    </article>
  );
}
