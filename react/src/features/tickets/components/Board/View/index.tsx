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
import { fetchProjects, fetchProjectMembers, createProject } from '@/features/tickets/api/projectApi';
import type { Project, ProjectMember } from '@/features/tickets/types/project';
import styles from './index.module.css';

export function TicketBoardView() {
  const {
    tickets,
    error,
    fetchTickets,
    updateStatus,
    moveTicket,
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
        setSelectedProjectId((current) => current && items.some((item) => item.id === current) ? current : '');
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
  const canWrite = selectedProject !== null && (isAdmin || currentMembership?.permission === 'write');
  const canManageMembers = selectedProject !== null && (isAdmin || currentMembership?.role === 'leader');
  // The API scopes accessible tickets; only render tickets belonging to accessible projects.
  const accessibleProjectIds = new Set(projects.map((project) => project.id));
  const projectTickets = tickets.filter((ticket) =>
    accessibleProjectIds.has(ticket.projectId) && (!selectedProjectId || ticket.projectId === selectedProjectId),
  );
  const projectKeys = Object.fromEntries(projects.map((project) => [project.id, project.projectKey]));
  const canDrag = selectedProject !== null && canWrite && searchQuery.trim() === '' && assigneeFilter === 'ALL';

  const refreshProjects = async () => {
    const items = await fetchProjects();
    setProjects(items);
    setSelectedProjectId((current) =>
      current && items.some((item) => item.id === current)
        ? current
        : '',
    );
  };

  const handleCreateProject = async () => {
    const name = window.prompt('新しいプロジェクト名を入力してください');
    if (name === null) return;
    if (!name.trim()) {
      setProjectError('プロジェクト名を入力してください。');
      return;
    }
    try {
      const created = await createProject(name.trim());
      await refreshProjects();
      setSelectedProjectId(created.id);
      setProjectError(null);
    } catch (reason) {
      setProjectError(reason instanceof Error ? reason.message : 'プロジェクトを作成できませんでした。');
    }
  };

  const handleStatusChange = async (id: string, status: TicketStatus) => {
    await updateStatus(id, status);
    await refreshProjects();
  };

  const handleCreate = async (input: Parameters<typeof addTicket>[0]) => {
    await addTicket(input);
    await refreshProjects();
  };

  const handleUpdate = async (
    id: string,
    input: Parameters<typeof updateTicket>[1],
  ) => {
    await updateTicket(id, input);
    await refreshProjects();
  };

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

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveTicket(null);

    if (!canDrag || !over || !selectedProject) return;

    const activeId = String(active.id);
    const overId = String(over.id);
    const draggedTicket = projectTickets.find((ticket) => ticket.id === activeId);
    if (!draggedTicket) return;

    const overTicket = projectTickets.find((ticket) => ticket.id === overId);
    const isOverColumn = INITIAL_COLUMNS.some((column) => column.id === overId);
    const newStatus = isOverColumn
      ? (overId as TicketStatus)
      : overTicket?.status;
    if (!newStatus) return;

    const targetTickets = projectTickets
      .filter((ticket) => ticket.status === newStatus)
      .sort((a, b) => a.position - b.position);
    const overPosition = overTicket
      ? targetTickets.findIndex((ticket) => ticket.id === overTicket.id)
      : -1;
    const targetPosition = overPosition >= 0
      ? overPosition
      : targetTickets.filter((ticket) => ticket.id !== activeId).length;

    try {
      const boardVersion = await moveTicket(
        activeId,
        newStatus,
        targetPosition,
        selectedProject.boardVersion,
      );
      setProjects((items) =>
        items.map((project) =>
          project.id === selectedProject.id
            ? { ...project, boardVersion }
            : project,
        ),
      );
    } catch {
      await refreshProjects();
    }
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
    await refreshProjects();
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
        canCreateProject={Boolean(currentUser)}
        onCreateProject={() => void handleCreateProject()}
        showAllProjects
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
          projectKey={selectedProject?.projectKey}
          projectKeys={projectKeys}
          searchQuery={searchQuery}
          assigneeFilter={assigneeFilter}
          currentUserId={currentUserId}
          onStatusChange={handleStatusChange}
          onEdit={openEdit}
          onDelete={handleDelete}
          canWrite={canWrite}
          canDrag={canDrag}
        />

        <DragOverlay>
          {activeTicket && canDrag ? <Card ticket={activeTicket} projectKey={selectedProject?.projectKey} isOverlay canWrite canDrag /> : null}
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
          onCreate={handleCreate}
          onUpdate={handleUpdate}
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
