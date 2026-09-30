'use client';

import { useState, useEffect } from 'react';
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
import { INITIAL_COLUMNS } from '@/features/tickets/mocks/tickets';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { Ticket, TicketStatus } from '@/features/tickets/types/ticket';
import { useTicketStore } from '@/features/tickets/store/useTicketStore';
import Header from '../Header';
import Main from '../Main';
import Card from '../Card';
import TicketModal from '../TicketModal';
import styles from './index.module.css';

export function TicketBoardView() {
  const {
    tickets,
    error,
    fetchTickets,
    updateStatus,
    addTicket,
    updateTicket,
    deleteTicket,
  } = useTicketStore();
  const currentUser = useAuthStore((state) => state.user);
  const currentUserId = currentUser?.id ?? null;

  const [searchQuery, setSearchQuery] = useState('');
  const [assigneeFilter, setAssigneeFilter] = useState('ALL');
  const [activeTicket, setActiveTicket] = useState<Ticket | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTicket, setEditingTicket] = useState<Ticket | null>(null);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    }),
  );

  const handleDragStart = (event: DragStartEvent) => {
    const activeId = String(event.active.id);
    const found = tickets.find((t) => t.id === activeId);
    if (found) setActiveTicket(found);
  };

  const handleDragCancel = () => {
    setActiveTicket(null);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveTicket(null);

    if (!over) return;

    const activeId = String(active.id);
    const overId = String(over.id);

    const draggedTicket = tickets.find((t) => String(t.id) === activeId);
    if (!draggedTicket) return;

    const isOverColumn = INITIAL_COLUMNS.some((col) => col.id === overId);
    let newStatus: TicketStatus = draggedTicket.status;

    if (isOverColumn) {
      newStatus = overId as TicketStatus;
    } else {
      const overTicket = tickets.find((t) => String(t.id) === overId);
      if (overTicket) {
        newStatus = overTicket.status;
      } else return;
    }

    // The displayed status can lag queued writes. Let the store compare the
    // requested status when its turn executes, so the final drop is not lost.
    updateStatus(activeId, newStatus);
  };

  const openCreate = () => {
    setEditingTicket(null);
    setIsModalOpen(true);
  };

  const openEdit = (ticket: Ticket) => {
    setEditingTicket(ticket);
    setIsModalOpen(true);
  };

  const handleDelete = async (ticket: Ticket) => {
    if (!window.confirm(`${ticket.issueKey ?? ticket.title} を削除しますか？`)) return;
    await deleteTicket(ticket.id);
  };

  return (
    <div className={styles.container}>
      <Header
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        assigneeFilter={assigneeFilter}
        onAssigneeChange={setAssigneeFilter}
        onCreate={openCreate}
      />

      {error && <p role="alert">{error}</p>}

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragCancel={handleDragCancel}
      >
        <Main
          tickets={tickets}
          searchQuery={searchQuery}
          assigneeFilter={assigneeFilter}
          currentUserId={currentUserId}
          onStatusChange={updateStatus}
          onEdit={openEdit}
          onDelete={handleDelete}
        />

        <DragOverlay>
          {activeTicket ? <Card ticket={activeTicket} isOverlay /> : null}
        </DragOverlay>
      </DndContext>

      {isModalOpen && (
        <TicketModal
          key={editingTicket?.id ?? 'create'}
          ticket={editingTicket}
          currentUserId={currentUserId}
          currentUserName={currentUser?.name}
          onClose={() => setIsModalOpen(false)}
          onCreate={addTicket}
          onUpdate={updateTicket}
        />
      )}
    </div>
  );
}
