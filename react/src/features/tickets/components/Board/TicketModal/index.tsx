'use client';

import { useEffect, useRef, useState } from 'react';
import type { CSSProperties } from 'react';
import type {
  CreateTicketInput,
  Ticket,
  TicketPriority,
  TicketStatus,
  UpdateTicketInput,
} from '@/features/tickets/types/ticket';
import TicketComments from '../TicketComments';
import TicketDetailLoader from './TicketDetailLoader';
import TicketDetailView from './TicketDetailView';
import TicketFormView from './TicketFormView';
import useTicketEditor from './useTicketEditor';
import type { Project, ProjectMember } from '@/features/tickets/types/project';
import { getProjectBorderColor } from '@/features/tickets/utils/projectColor';
import styles from './index.module.css';

const STATUSES: Array<{ value: TicketStatus; label: string }> = [
  { value: 'BACKLOG', label: 'バックログ' },
  { value: 'TODO', label: 'TODO' },
  { value: 'IN_PROGRESS', label: '進行中' },
  { value: 'IN_REVIEW', label: 'レビュー中' },
  { value: 'DONE', label: '完了' },
];

const PRIORITIES: Array<{ value: TicketPriority; label: string }> = [
  { value: 'HIGHEST', label: '最高' },
  { value: 'HIGH', label: '高' },
  { value: 'MEDIUM', label: '中' },
  { value: 'LOW', label: '低' },
  { value: 'LOWEST', label: '最低' },
];

interface TicketModalProps {
  ticket: Ticket | null;
  currentUserId: number | null;
  currentUserRole?: 'user' | 'admin';
  onClose: () => void;
  onCreate: (input: CreateTicketInput) => Promise<void>;
  onUpdate: (id: string, input: UpdateTicketInput) => Promise<Ticket>;
  onDelete: (ticket: Ticket) => Promise<void>;
  projectId: string;
  projectKey?: string | null;
  projectColor?: string | null;
  projectMembers: ProjectMember[];
  projectSelection?: {
    projects: Project[];
    onChange: (id: string) => void;
    message?: string;
    onRetry?: () => void;
  };
  readOnly?: boolean;
  commentsReadOnly?: boolean;
}

export default function TicketModal(props: TicketModalProps) {
  if (!props.ticket) return <TicketModalContent {...props} />;
  return (
    <TicketDetailLoader
      key={props.ticket.id}
      ticketId={props.ticket.id}
      onClose={props.onClose}
    >
      {(loaded) => (
        <TicketModalContent key={loaded.id} {...props} ticket={loaded} />
      )}
    </TicketDetailLoader>
  );
}

function TicketModalContent({
  ticket: initialTicket,
  currentUserId,
  currentUserRole,
  onClose,
  onCreate,
  onUpdate,
  onDelete,
  projectId,
  projectColor,
  projectMembers,
  projectSelection,
  readOnly = false,
  commentsReadOnly = false,
}: TicketModalProps) {
  const [mode, setMode] = useState<'detail' | 'edit' | 'create'>(
    initialTicket ? 'detail' : 'create',
  );
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const editor = useTicketEditor({
    initialTicket,
    projectId,
    readOnly,
    onCreate,
    onUpdate,
    onSaveStart: () => setDeleteError(null),
    onCreated: onClose,
    onUpdated: () => setMode('detail'),
  });
  const submitting = editor.submitting || deleting;
  const saveError = deleteError ?? editor.saveError;
  const ticket = editor.ticket;
  const headingRef = useRef<HTMLHeadingElement>(null);
  const canEdit = !!ticket && !readOnly && !editor.unavailable;
  const isDetail = !!ticket && mode === 'detail';

  useEffect(() => {
    if (isDetail) headingRef.current?.focus();
  }, [isDetail]);

  const cancelEdit = () => {
    if (ticket) {
      editor.restoreSavedValues();
      editor.clearSaveError();
      setDeleteError(null);
      if (editor.conflict) {
        onClose();
        return;
      }
      setMode('detail');
      return;
    }
    onClose();
  };

  const remove = async () => {
    if (!ticket || !canEdit || submitting) return;
    if (!window.confirm(`${ticket.issueKey ?? ticket.title} を削除しますか？`))
      return;
    setDeleting(true);
    editor.clearSaveError();
    setDeleteError(null);
    try {
      await onDelete(ticket);
      onClose();
    } catch (error) {
      setDeleteError(
        error instanceof Error ? error.message : '削除に失敗しました。',
      );
    } finally {
      setDeleting(false);
    }
  };

  const assigneeName = editor.assigneeId
    ? (projectMembers.find((member) => member.id === editor.assigneeId)?.name ??
      ticket?.assignee?.name ??
      '—')
    : '未割り当て';
  const projectColorStyle: CSSProperties & {
    '--project-border-color'?: string;
  } = {
    '--project-border-color':
      getProjectBorderColor(projectColor ?? null) ?? undefined,
  };

  return (
    <div
      className={styles.backdrop}
      role="presentation"
      onMouseDown={() => {
        if (!submitting) onClose();
      }}
    >
      <section
        className={styles.modal}
        style={projectColorStyle}
        role="dialog"
        aria-modal="true"
        aria-labelledby="ticket-modal-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className={styles.modalHeader}>
          {isDetail && (
            <span className={styles.issueKey}>{ticket.issueKey ?? '—'}</span>
          )}
          <h2
            ref={headingRef}
            id="ticket-modal-title"
            tabIndex={isDetail ? -1 : undefined}
          >
            {isDetail
              ? 'チケット詳細'
              : ticket
                ? 'チケット編集'
                : 'チケット作成'}
          </h2>
        </header>

        {isDetail && ticket ? (
          <TicketDetailView
            title={editor.title}
            status={
              STATUSES.find((item) => item.value === editor.status)?.label ??
              editor.status
            }
            priority={
              PRIORITIES.find((item) => item.value === editor.priority)?.label ??
              editor.priority
            }
            assigneeName={assigneeName}
            description={editor.description}
            canEdit={canEdit}
            submitting={submitting}
            saveError={saveError}
            onClose={onClose}
            onEdit={() => {
              editor.clearSaveError();
              setDeleteError(null);
              setMode('edit');
            }}
            onDelete={() => void remove()}
          />
        ) : (
          <TicketFormView
            ticket={ticket}
            projectId={projectId}
            projectSelection={projectSelection}
            projectMembers={projectMembers}
            title={editor.title}
            description={editor.description}
            status={editor.status}
            priority={editor.priority}
            assigneeId={editor.assigneeId}
            statuses={STATUSES}
            priorities={PRIORITIES}
            submitting={submitting}
            readOnly={readOnly}
            unavailable={editor.unavailable}
            saveError={saveError}
            conflict={editor.conflict}
            reloading={editor.reloading}
            reloadError={editor.reloadError}
            latest={editor.latest}
            onSubmit={(event) => {
              if (!deleting) void editor.submit(event);
              else event.preventDefault();
            }}
            onProjectChange={(id) => {
              // Project変更で別Projectの担当者を送信しない。その他の下書きは保全する。
              editor.resetAssigneeForProjectChange();
              setDeleteError(null);
              projectSelection?.onChange(id);
            }}
            onTitleChange={editor.setTitle}
            onDescriptionChange={editor.setDescription}
            onStatusChange={editor.setStatus}
            onPriorityChange={editor.setPriority}
            onAssigneeChange={editor.setAssigneeId}
            onLoadLatest={() => void editor.loadLatest()}
            onUseLatest={editor.useLatest}
            onCancel={cancelEdit}
          />
        )}
        {ticket && (
          <TicketComments
            ticketId={ticket.id}
            currentUserId={currentUserId}
            currentUserRole={currentUserRole}
            readOnly={commentsReadOnly}
          />
        )}
      </section>
    </div>
  );
}
