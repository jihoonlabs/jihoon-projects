'use client';

import { useState } from 'react';
import {
  DndContext,
  DragEndEvent,
  DragStartEvent,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
} from '@dnd-kit/core';
import { MOCK_TICKETS, INITIAL_COLUMNS } from '@/features/tickets/mocks/tickets';
import { Ticket, TicketStatus } from '@/features/tickets/types/ticket';
import Header from '../Header';
import Main from '../Main';
import Card from '../Card';
import styles from './index.module.css';

export function TicketBoardView() {
  const [tickets, setTickets] = useState<Ticket[]>(MOCK_TICKETS);
  const [searchQuery, setSearchQuery] = useState('');
  const [assigneeFilter, setAssigneeFilter] = useState('ALL');
  const [activeTicket, setActiveTicket] = useState<Ticket | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    })
  );

  const handleDragStart = (event: DragStartEvent) => {
    const activeId = String(event.active.id);
    const found = tickets.find((t) => t.id === activeId);
    if (found) setActiveTicket(found);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveTicket(null);

    if (!over) return;

    const activeId = String(active.id);
    const overId = String(over.id);

    const draggedTicket = tickets.find((t) => t.id === activeId);
    if (!draggedTicket) return;

    const isOverColumn = INITIAL_COLUMNS.some((col) => col.id === overId);
    let newStatus: TicketStatus = draggedTicket.status;

    if (isOverColumn) {
      newStatus = overId as TicketStatus;
    } else {
      const overTicket = tickets.find((t) => t.id === overId);
      if (overTicket) {
        newStatus = overTicket.status;
      }
    }

    if (draggedTicket.status !== newStatus) {
      setTickets((prev) =>
        prev.map((ticket) =>
          ticket.id === activeId ? { ...ticket, status: newStatus } : ticket
        )
      );
    }
  };

  return (
    <div className={styles.container}>
      <Header
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        assigneeFilter={assigneeFilter}
        onAssigneeChange={setAssigneeFilter}
      />

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <Main
          tickets={tickets}
          searchQuery={searchQuery}
          assigneeFilter={assigneeFilter}
        />

        <DragOverlay>
          {activeTicket ? <Card ticket={activeTicket} isOverlay /> : null}
        </DragOverlay>
      </DndContext>
    </div>
  );
}