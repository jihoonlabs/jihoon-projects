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
import ProjectMembersDialog from '../ProjectMembersDialog';
import { fetchProjects, fetchProjectMembers } from '@/features/tickets/api/projectApi';
import type { Project, ProjectMember } from '@/features/tickets/types/project';
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
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [projectMembers, setProjectMembers] = useState<ProjectMember[]>([]);
  const [membersProjectId, setMembersProjectId] = useState('');
  const [projectError, setProjectError] = useState<string | null>(null);
  const [managingMembers, setManagingMembers] = useState(false);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  useEffect(() => {
    let active = true;
    fetchProjects()
      .then((items) => {
        if (!active) return;
        setProjects(items);
        setSelectedProjectId((current) => current && items.some((item) => item.id === current) ? current : items[0]?.id ?? '');
      })
      .catch((reason) => { if (active) setProjectError(reason instanceof Error ? reason.message : 'プロジェクトを取得できませんでした。'); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!selectedProjectId) return;
    let active = true;
    fetchProjectMembers(selectedProjectId)
      .then((items) => { if (active) { setProjectMembers(items); setMembersProjectId(selectedProjectId); setProjectError(null); } })
      .catch((reason) => { if (active) setProjectError(reason instanceof Error ? reason.message : 'メンバーを取得できませんでした。'); });
    return () => { active = false; };
  }, [selectedProjectId]);

  const selectedProject = projects.find((project) => project.id === selectedProjectId) ?? null;
  const currentMembership = membersProjectId === selectedProjectId
    ? projectMembers.find((member) => member.id === String(currentUserId))
    : undefined;
  const isAdmin = currentUser?.role === 'admin';
  const canWrite = isAdmin || currentMembership?.permission === 'write';
  const canManageMembers = isAdmin || currentMembership?.role === 'leader';
  const projectTickets = tickets.filter((ticket) => ticket.projectId === selectedProjectId);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    }),
  );

  const handleDragStart = (event: DragStartEvent) => {
    const activeId = String(event.active.id);
    const found = projectTickets.find((t) => t.id === activeId);
    if (found) setActiveTicket(found);
  };

  const handleDragCancel = () => {
    setActiveTicket(null);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveTicket(null);

    if (!canWrite || !over) return;

    const activeId = String(active.id);
    const overId = String(over.id);

    const draggedTicket = projectTickets.find((t) => String(t.id) === activeId);
    if (!draggedTicket) return;

    const isOverColumn = INITIAL_COLUMNS.some((col) => col.id === overId);
    let newStatus: TicketStatus = draggedTicket.status;

    if (isOverColumn) {
      newStatus = overId as TicketStatus;
    } else {
      const overTicket = projectTickets.find((t) => String(t.id) === overId);
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
        projects={projects}
        selectedProjectId={selectedProjectId}
        onProjectChange={setSelectedProjectId}
        canWrite={canWrite}
        canManageMembers={canManageMembers}
        onManageMembers={() => setManagingMembers(true)}
      />

      {(error || projectError) && <p role="alert">{error || projectError}</p>}
      {projects.length === 0 && !projectError && <p>利用可能なプロジェクトがありません。</p>}

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragCancel={handleDragCancel}
      >
        <Main
          tickets={projectTickets}
          searchQuery={searchQuery}
          assigneeFilter={assigneeFilter}
          currentUserId={currentUserId}
          onStatusChange={updateStatus}
          onEdit={openEdit}
          onDelete={handleDelete}
          canWrite={canWrite}
        />

        <DragOverlay>
          {activeTicket && canWrite ? <Card ticket={activeTicket} isOverlay canWrite /> : null}
        </DragOverlay>
      </DndContext>

      {isModalOpen && (
        <TicketModal
          key={editingTicket?.id ?? 'create'}
          ticket={editingTicket}
          currentUserId={currentUserId}
          currentUserRole={currentUser?.role}
          projectId={editingTicket?.projectId ?? selectedProjectId}
          projectMembers={membersProjectId === selectedProjectId ? projectMembers : []}
          readOnly={!canWrite}
          onClose={() => setIsModalOpen(false)}
          onCreate={addTicket}
          onUpdate={updateTicket}
        />
      )}
      {managingMembers && selectedProject && (
        <ProjectMembersDialog
          project={selectedProject}
          onClose={() => {
            setManagingMembers(false);
            void fetchProjectMembers(selectedProject.id)
              .then(setProjectMembers)
              .catch((reason) => setProjectError(reason instanceof Error ? reason.message : 'メンバーを取得できませんでした。'));
          }}
        />
      )}
    </div>
  );
}
