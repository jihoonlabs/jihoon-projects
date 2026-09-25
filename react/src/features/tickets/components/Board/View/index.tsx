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
import { Ticket, TicketStatus } from '@/features/tickets/types/ticket';
import { useTicketStore } from '@/features/tickets/store/useTicketStore';

// 모달 컴포넌트 불러오기
import { FormModal } from '@/features/tickets/components/Modal/FormModal';
import { DeleteModal } from '@/features/tickets/components/Modal/DeleteModal';

import Header from '../Header';
import Main from '../Main';
import Card from '../Card';
import styles from './index.module.css';

export function TicketBoardView() {
  const { tickets, fetchTickets, updateStatus } = useTicketStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [assigneeFilter, setAssigneeFilter] = useState('ALL');
  const [activeTicket, setActiveTicket] = useState<Ticket | null>(null);

  // 1. FormModal (생성/수정) 상태 관리
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingTicket, setEditingTicket] = useState<Ticket | null>(null);

  // 2. DeleteModal (삭제) 상태 관리
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [deletingTicket, setDeletingTicket] = useState<{ id: string; title: string } | null>(null);

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

  // --- [모달 핸들러 정의] ---
  // 티켓 작성(생성) 모달 열기
  const handleOpenCreate = () => {
    setEditingTicket(null);
    setIsFormOpen(true);
  };

  // 티켓 수정 모달 열기
  const handleOpenEdit = (ticket: Ticket) => {
    setEditingTicket(ticket);
    setIsFormOpen(true);
  };

  // 티켓 삭제 모달 열기
  const handleOpenDelete = (id: string, title: string) => {
    setDeletingTicket({ id, title });
    setIsDeleteOpen(true);
  };

  // --- [DnD 핸들러] ---
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
      }
    }

    if (draggedTicket.status !== newStatus) {
      updateStatus(activeId, newStatus);
    }
  };

  return (
    <div className={styles.container}>
      {/* Header에 이슈 작성(생성) 버튼 클릭 이벤트 전달 */}
      <Header
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        assigneeFilter={assigneeFilter}
        onAssigneeChange={setAssigneeFilter}
        onCreateClick={handleOpenCreate}
      />

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragCancel={handleDragCancel}
      >
        {/* Main/Column/Card 계층에 수정/삭제 핸들러 전달 */}
        <Main
          tickets={tickets}
          searchQuery={searchQuery}
          assigneeFilter={assigneeFilter}
          onEdit={handleOpenEdit}
          onDelete={handleOpenDelete}
        />

        <DragOverlay>
          {activeTicket ? <Card ticket={activeTicket} isOverlay /> : null}
        </DragOverlay>
      </DndContext>

      {/* --- [모달 컴포넌트 바인딩] --- */}
      {/* 생성/수정 모달 */}
      <FormModal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        initialData={editingTicket}
      />

      {/* 삭제 확인 모달 */}
      <DeleteModal
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        ticketId={deletingTicket?.id ?? null}
        ticketTitle={deletingTicket?.title}
      />
    </div>
  );
}