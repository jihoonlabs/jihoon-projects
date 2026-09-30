'use client';

import { useDroppable } from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { Ticket, TicketStatus } from '@/features/tickets/types/ticket';
import { ColumnConfig } from '@/features/tickets/mocks/tickets';
import Card from '../Card';
import styles from './index.module.css';

interface ColumnProps {
  column: ColumnConfig;
  tickets: Ticket[];
  onStatusChange?: (id: string, status: TicketStatus) => void;
  onEdit?: (ticket: Ticket) => void;
  onDelete?: (ticket: Ticket) => void;
}

export default function Column({
  column,
  tickets,
  onStatusChange,
  onEdit,
  onDelete,
}: ColumnProps) {
  const { setNodeRef } = useDroppable({
    id: column.id,
  });

  const ticketIds = tickets.map((t) => t.id);

  return (
    <div ref={setNodeRef} className={styles.container}>
      <div className={styles.header}>
        <span>{column.label}</span>
        <span className={styles.count}>{tickets.length}</span>
      </div>

      <SortableContext items={ticketIds} strategy={verticalListSortingStrategy}>
        <div className={styles.cardList}>
          {tickets.map((ticket) => (
            <Card
              key={ticket.id}
              ticket={ticket}
              onStatusChange={onStatusChange}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
        </div>
      </SortableContext>
    </div>
  );
}
