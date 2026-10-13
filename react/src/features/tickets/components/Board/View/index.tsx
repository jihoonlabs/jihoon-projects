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
import ProjectOperations from '../ProjectOperations';
import ProjectDirectory from '../ProjectDirectory';
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
    isLoading,
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
  const projectRevision = useRef(0);
  const projectListSequence = useRef(0);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [projectMembers, setProjectMembers] = useState<ProjectMember[]>([]);
  const memberRevision = useRef(0);
  const [memberAttempt, setMemberAttempt] = useState(0);
  const [memberError, setMemberError] = useState<{
    projectId: string;
    message: string;
  } | null>(null);
  const [membersProjectId, setMembersProjectId] = useState('');
  const [projectError, setProjectError] = useState<string | null>(null);
  const [managingMembers, setManagingMembers] = useState(false);
  const [showArchived, setShowArchived] = useState(false);
  const [projectListAttempt, setProjectListAttempt] = useState(0);
  const [operationsOpen, setOperationsOpen] = useState(false);
  const [projectsOpen, setProjectsOpen] = useState(false);
  const [projectsBusy, setProjectsBusy] = useState(false);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [projectNotice, setProjectNotice] = useState<string | null>(null);

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
    const revision = projectRevision.current;
    const sequence = ++projectListSequence.current;
    fetchProjects(showArchived ? { archived: true } : undefined)
      .then((items) => {
        if (
          !active ||
          revision !== projectRevision.current ||
          sequence !== projectListSequence.current
        )
          return;
        setProjects(items);
        setProjectError(null);
        setSelectedProjectId((current) =>
          current && items.some((item) => item.id === current)
            ? current
            : (items[0]?.id ?? ''),
        );
      })
      .catch((reason) => {
        if (
          active &&
          revision === projectRevision.current &&
          sequence === projectListSequence.current
        )
          setProjectError(
            reason instanceof Error
              ? reason.message
              : 'プロジェクトを取得できませんでした。',
          );
      })
      .finally(() => {
        if (active) setProjectsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [showArchived, projectListAttempt]);

  useEffect(() => {
    if (!selectedProjectId) return;
    let active = true;
    const revision = memberRevision.current;
    fetchProjectMembers(selectedProjectId)
      .then((items) => {
        if (active && revision === memberRevision.current) {
          setProjectMembers(items);
          setMembersProjectId(selectedProjectId);
          setMemberError(null);
        }
      })
      .catch((reason) => {
        if (active && revision === memberRevision.current) {
          setMembersProjectId('');
          setMemberError({
            projectId: selectedProjectId,
            message:
              reason instanceof Error
                ? reason.message
                : 'メンバーを取得できませんでした。',
          });
        }
      });
    return () => {
      active = false;
    };
  }, [selectedProjectId, memberAttempt]);

  const retryMembers = () => {
    memberRevision.current += 1;
    setMembersProjectId('');
    setMemberError(null);
    setMemberAttempt((attempt) => attempt + 1);
  };

  const selectedProject =
    projects.find((project) => project.id === selectedProjectId) ?? null;
  const currentMembership =
    membersProjectId === selectedProjectId
      ? projectMembers.find((member) => member.id === String(currentUserId))
      : undefined;
  const isAdmin = currentUser?.role === 'admin';
  const isArchived = Boolean(selectedProject?.archivedAt);
  const canManageProject =
    Boolean(selectedProject) &&
    (isAdmin || currentMembership?.role === 'leader');
  const canWrite =
    Boolean(selectedProject) &&
    !isArchived &&
    (isAdmin || currentMembership?.permission === 'write');
  const canManageMembers = !isArchived && canManageProject;
  const projectTickets = tickets.filter(
    (ticket) => ticket.projectId === selectedProjectId,
  );
  const canDrag =
    canWrite && searchQuery.trim() === '' && assigneeFilter === 'ALL';

  const refreshProjects = async () => {
    const revision = projectRevision.current;
    const sequence = ++projectListSequence.current;
    const items = await fetchProjects(
      showArchived ? { archived: true } : undefined,
    );
    if (
      revision !== projectRevision.current ||
      sequence !== projectListSequence.current
    )
      return;
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
    // 保存済みTicketの再作成を誘発しないよう、一覧更新の失敗を分けて扱う。
    try {
      await refreshProjects();
    } catch (reason) {
      setProjectError(
        reason instanceof Error
          ? reason.message
          : 'プロジェクトを取得できませんでした。',
      );
    }
  };

  const selectProject = (projectId: string) => {
    if (projectsBusy) return;
    setSelectedProjectId(projectId);
    setOperationsOpen(false);
    setSearchQuery('');
    setAssigneeFilter('ALL');
    setProjectNotice(null);
  };

  const changeProjectScope = (archived: boolean) => {
    if (projectsBusy) return;
    projectRevision.current += 1;
    setShowArchived(archived);
    setProjects([]);
    setSelectedProjectId('');
    setOperationsOpen(false);
    setProjectNotice(null);
    setProjectError(null);
    setProjectsLoading(true);
  };

  const handleProjectChanged = (project: Project) => {
    projectRevision.current += 1;
    const sameScope = Boolean(project.archivedAt) === showArchived;
    const items = projects.filter((item) => item.id !== project.id);
    if (sameScope) items.push(project);
    items.sort((a, b) => a.name.localeCompare(b.name, 'ja'));
    setProjects(items);
    if (!sameScope) {
      setSelectedProjectId(items[0]?.id ?? '');
      setOperationsOpen(false);
      setSearchQuery('');
      setAssigneeFilter('ALL');
    }
    setProjectNotice(
      project.archivedAt
        ? `${project.name} を終了しました。終了したプロジェクトの一覧から確認・復元できます。`
        : showArchived
          ? `${project.name} を復元しました。稼働中の一覧から開けます。`
          : `${project.name} の変更を保存しました。`,
    );
  };

  const handleProjectCreated = (project: Project) => {
    projectRevision.current += 1;
    setProjects((items) =>
      [...items.filter((item) => item.id !== project.id), project].sort(
        (a, b) => a.name.localeCompare(b.name, 'ja'),
      ),
    );
    setSelectedProjectId(project.id);
    setSearchQuery('');
    setAssigneeFilter('ALL');
    setProjectNotice(
      `${project.name} を作成しました。メンバーを追加してチケット作成を開始できます。`,
    );
  };

  const handleUpdate = async (
    id: string,
    input: Parameters<typeof updateTicket>[1],
  ) => {
    const updated = await updateTicket(id, input);
    // 保存成功後のメタデータ取得失敗を、保存失敗として扱わない。
    try {
      await refreshProjects();
    } catch (reason) {
      setProjectError(
        reason instanceof Error
          ? reason.message
          : 'プロジェクトを取得できませんでした。',
      );
    }
    return updated;
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
      // 並行書き込み後の再取得がstoreのエラーを消しても、移動失敗を表示する。
      setProjectError(
        reason instanceof Error
          ? reason.message
          : 'チケットを移動できませんでした。',
      );
      try {
        await refreshProjects();
      } catch {
        // Project再取得も失敗した場合は、元の移動エラーを保持する。
      }
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
    // 削除済みTicketへの再操作を誘発しないよう、後続の取得失敗を分離する。
    try {
      await refreshProjects();
    } catch (reason) {
      setProjectError(
        reason instanceof Error
          ? reason.message
          : 'プロジェクトを取得できませんでした。',
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
        onCreate={openCreate}
        projects={projects}
        selectedProjectId={selectedProjectId}
        onProjectChange={selectProject}
        canWrite={canWrite}
        canManageMembers={canManageMembers}
        onManageMembers={() => setManagingMembers(true)}
        canManageProject={canManageProject}
        operationsOpen={operationsOpen}
        onToggleOperations={() => setOperationsOpen((open) => !open)}
        projectsBusy={projectsBusy}
        projectsOpen={projectsOpen}
        onToggleProjects={() => setProjectsOpen((open) => !open)}
      />

      {projectsOpen && (
        <ProjectDirectory
          showArchived={showArchived}
          externalBusy={projectsBusy}
          onArchivedChange={changeProjectScope}
          onRetry={() => {
            setProjectsLoading(true);
            setProjectListAttempt((attempt) => attempt + 1);
          }}
          loading={projectsLoading}
          projects={projects}
          selectedProjectId={selectedProjectId}
          onSelect={selectProject}
          onCreated={handleProjectCreated}
          onPendingChange={setProjectsBusy}
        />
      )}
      {operationsOpen && selectedProject && canManageProject && (
        <ProjectOperations
          key={selectedProject.id}
          project={selectedProject}
          canRename={isAdmin}
          onChanged={handleProjectChanged}
          onPendingChange={setProjectsBusy}
        />
      )}
      {isArchived && (
        <p>終了したプロジェクトです。チケットとコメントは閲覧のみです。</p>
      )}
      {projectNotice && <p role="status">{projectNotice}</p>}

      {isLoading && <p role="status">チケット一覧を更新中...</p>}

      {memberError?.projectId === selectedProjectId && (
        <div className={styles.memberRecovery}>
          <p role="alert">{memberError.message}</p>
          <button type="button" onClick={retryMembers}>
            メンバーと権限を再取得
          </button>
        </div>
      )}
      {error && (
        <div className={styles.memberRecovery}>
          <p role="alert">{error}</p>
          <button
            type="button"
            disabled={isLoading}
            onClick={() => void fetchTickets()}
          >
            チケット一覧を再取得
          </button>
        </div>
      )}
      {projectError && <p role="alert">{projectError}</p>}
      {projects.length === 0 && !projectsLoading && !projectError && (
        <p>
          利用可能なプロジェクトがありません。「プロジェクト一覧・作成」から作成するか、リーダーにメンバー追加を依頼してください。
        </p>
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
          projectColor={selectedProject?.color}
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
              projectColor={selectedProject?.color}
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
          projectColor={selectedProject?.color}
          projectMembers={
            membersProjectId === selectedProjectId ? projectMembers : []
          }
          commentsReadOnly={isArchived}
          readOnly={!canWrite}
          onClose={closeModal}
          onCreate={handleCreate}
          onUpdate={handleUpdate}
          onDelete={handleDelete}
        />
      )}
      {managingMembers && selectedProject && (
        <ProjectMembersDialog
          key={selectedProject.id}
          project={selectedProject}
          canManage={canManageMembers}
          onMembersChanged={(items) => {
            memberRevision.current += 1;
            setMemberError(null);
            setProjectMembers(items);
            setMembersProjectId(selectedProject.id);
          }}
          onClose={() => {
            setManagingMembers(false);
            retryMembers();
          }}
        />
      )}
    </div>
  );
}
