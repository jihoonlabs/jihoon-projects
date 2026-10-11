'use client';

import { useState, useEffect, useRef } from 'react';
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
import {
  fetchProjects,
  fetchProjectMembers,
} from '@/features/tickets/api/projectApi';
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
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const modalTrigger = useRef<HTMLButtonElement | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [projectMembers, setProjectMembers] = useState<ProjectMember[]>([]);
  const [membersProjectId, setMembersProjectId] = useState('');
  const [projectError, setProjectError] = useState<string | null>(null);
  const [managingMembers, setManagingMembers] = useState(false);

  useEffect(() => {
    if (isModalOpen || !modalTrigger.current) return;
    const trigger = modalTrigger.current;
    modalTrigger.current = null;
    if (trigger.isConnected) trigger.focus();
    else
      document
        .querySelector<HTMLSelectElement>('[aria-label="プロジェクト"]')
        ?.focus();
  }, [isModalOpen]);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  useEffect(() => {
    let active = true;
    fetchProjects()
      .then((items) => {
        if (!active) return;
        setProjects(items);
        setSelectedProjectId((current) =>
          current && items.some((item) => item.id === current)
            ? current
            : (items[0]?.id ?? ''),
        );
      })
      .catch((reason) => {
        if (active)
          setProjectError(
            reason instanceof Error
              ? reason.message
              : 'プロジェクトを取得できませんでした。',
          );
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedProjectId) return;
    let active = true;
    fetchProjectMembers(selectedProjectId)
      .then((items) => {
        if (active) {
          setProjectMembers(items);
          setMembersProjectId(selectedProjectId);
          setProjectError(null);
        }
      })
      .catch((reason) => {
        if (active)
          setProjectError(
            reason instanceof Error
              ? reason.message
              : 'メンバーを取得できませんでした。',
          );
      });
    return () => {
      active = false;
    };
  }, [selectedProjectId]);

  const selectedProject =
    projects.find((project) => project.id === selectedProjectId) ?? null;
  const currentMembership =
    membersProjectId === selectedProjectId
      ? projectMembers.find((member) => member.id === String(currentUserId))
      : undefined;
  const isAdmin = currentUser?.role === 'admin';
  const canWrite = isAdmin || currentMembership?.permission === 'write';
  const canManageMembers = isAdmin || currentMembership?.role === 'leader';
  const projectTickets = tickets.filter(
    (ticket) => ticket.projectId === selectedProjectId,
  );
  const canDrag =
    canWrite && searchQuery.trim() === '' && assigneeFilter === 'ALL';

  const refreshProjects = async () => {
    const items = await fetchProjects();
    setProjects(items);
    setSelectedProjectId((current) =>
      current && items.some((item) => item.id === current)
        ? current
        : (items[0]?.id ?? ''),
    );
  };

  const handleStatusChange = async (id: string, status: TicketStatus) => {
    try {
      await updateStatus(id, status);
      await refreshProjects();
      setProjectError(null);
    } catch (reason) {
      setProjectError(
        reason instanceof Error
          ? reason.message
          : 'ステータスを更新できませんでした。',
      );
    }
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
    const draggedTicket = projectTickets.find(
      (ticket) => ticket.id === activeId,
    );
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
    const targetPosition =
      overPosition >= 0
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
      setProjectError(null);
    } catch (reason) {
      await refreshProjects();
      // 並行書き込み後の再取得がstoreのエラーを消しても、移動失敗を表示する。
      setProjectError(
        reason instanceof Error
          ? reason.message
          : 'チケットを移動できませんでした。',
      );
    }
  };

  const openCreate = () => {
    modalTrigger.current = null;
    setSelectedTicket(null);
    setIsModalOpen(true);
  };

  const openDetails = (ticket: Ticket, trigger: HTMLButtonElement) => {
    modalTrigger.current = trigger;
    setSelectedTicket(ticket);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedTicket(null);
  };

  const handleDelete = async (ticket: Ticket) => {
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
        canManageMembers={canManageMembers}
        onManageMembers={() => setManagingMembers(true)}
      />

      {(error || projectError) && <p role="alert">{error || projectError}</p>}
      {projects.length === 0 && !projectError && (
        <p>利用可能なプロジェクトがありません。</p>
      )}

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
          searchQuery={searchQuery}
          assigneeFilter={assigneeFilter}
          currentUserId={currentUserId}
          onStatusChange={handleStatusChange}
          onOpenDetails={openDetails}
          canWrite={canWrite}
          canDrag={canDrag}
        />

        <DragOverlay>
          {activeTicket && canDrag ? (
            <Card
              ticket={activeTicket}
              projectKey={selectedProject?.projectKey}
              isOverlay
              canWrite
              canDrag
            />
          ) : null}
        </DragOverlay>
      </DndContext>

      {isModalOpen && (
        <TicketModal
          key={selectedTicket?.id ?? 'create'}
          ticket={selectedTicket}
          currentUserId={currentUserId}
          currentUserRole={currentUser?.role}
          projectId={selectedTicket?.projectId ?? selectedProjectId}
          projectKey={selectedProject?.projectKey}
          projectMembers={
            membersProjectId === selectedProjectId ? projectMembers : []
          }
          readOnly={!canWrite}
          onClose={closeModal}
          onCreate={handleCreate}
          onUpdate={handleUpdate}
          onDelete={handleDelete}
        />
      )}
      {managingMembers && selectedProject && (
        <ProjectMembersDialog
          project={selectedProject}
          onClose={() => {
            setManagingMembers(false);
            void fetchProjectMembers(selectedProject.id)
              .then(setProjectMembers)
              .catch((reason) =>
                setProjectError(
                  reason instanceof Error
                    ? reason.message
                    : 'メンバーを取得できませんでした。',
                ),
              );
          }}
        />
      )}
    </div>
  );
}
