'use client';

import { FormEvent, useEffect, useRef, useState } from 'react';
import type { CSSProperties } from 'react';
import type {
  CreateTicketInput,
  Ticket,
  TicketPriority,
  TicketStatus,
  UpdateTicketInput,
} from '@/features/tickets/types/ticket';
import TicketComments from '../TicketComments';
import type { ProjectMember } from '@/features/tickets/types/project';
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
  onUpdate: (id: string, input: UpdateTicketInput) => Promise<void>;
  onDelete: (ticket: Ticket) => Promise<void>;
  projectId: string;
  projectKey?: string | null;
  projectMembers: ProjectMember[];
  readOnly?: boolean;
}

export default function TicketModal({
  ticket,
  currentUserId,
  currentUserRole,
  onClose,
  onCreate,
  onUpdate,
  onDelete,
  projectId,
  projectKey,
  projectMembers,
  readOnly = false,
}: TicketModalProps) {
  const initialValues = {
    title: ticket?.title ?? '',
    description: ticket?.description ?? '',
    status: ticket?.status ?? ('TODO' as TicketStatus),
    priority: ticket?.priority ?? ('MEDIUM' as TicketPriority),
    assigneeId: ticket?.assignee?.id ?? '',
  };
  const savedValues = useRef(initialValues);
  const [title, setTitle] = useState(initialValues.title);
  const [description, setDescription] = useState(initialValues.description);
  const [status, setStatus] = useState<TicketStatus>(initialValues.status);
  const [priority, setPriority] = useState<TicketPriority>(
    initialValues.priority,
  );
  const [assigneeId, setAssigneeId] = useState(initialValues.assigneeId);
  const [mode, setMode] = useState<'detail' | 'edit' | 'create'>(
    ticket ? 'detail' : 'create',
  );
  const [submitting, setSubmitting] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const canEdit = !!ticket && !readOnly;
  const isDetail = !!ticket && mode === 'detail';

  useEffect(() => {
    if (isDetail) headingRef.current?.focus();
  }, [isDetail]);

  const restoreSavedValues = () => {
    setTitle(savedValues.current.title);
    setDescription(savedValues.current.description);
    setStatus(savedValues.current.status);
    setPriority(savedValues.current.priority);
    setAssigneeId(savedValues.current.assigneeId);
  };

  const cancelEdit = () => {
    if (ticket) {
      restoreSavedValues();
      setSaveError(null);
      setMode('detail');
      return;
    }
    onClose();
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (readOnly || !title.trim() || submitting) return;
    setSubmitting(true);
    setSaveError(null);
    const fields: UpdateTicketInput = {
      title: title.trim(),
      description: description.trim() || null,
      status,
      priority,
      ...(ticket && assigneeId === (ticket.assignee?.id ?? '')
        ? {}
        : { assigneeId: assigneeId || null }),
    };
    try {
      if (ticket) {
        await onUpdate(ticket.id, fields);
        savedValues.current = {
          title: fields.title ?? '',
          description: fields.description ?? '',
          status: fields.status ?? 'TODO',
          priority: fields.priority ?? 'MEDIUM',
          assigneeId: fields.assigneeId ?? assigneeId,
        };
        setMode('detail');
      } else {
        await onCreate({
          projectId,
          title: title.trim(),
          description: description.trim() || null,
          status,
          priority,
          assigneeId: assigneeId || null,
        });
        onClose();
      }
    } catch (error) {
      setSaveError(
        error instanceof Error ? error.message : '保存に失敗しました。',
      );
    } finally {
      setSubmitting(false);
    }
  };

  const remove = async () => {
    if (!ticket || !canEdit || submitting) return;
    if (!window.confirm(`${ticket.issueKey ?? ticket.title} を削除しますか？`))
      return;
    setSubmitting(true);
    setSaveError(null);
    try {
      await onDelete(ticket);
      onClose();
    } catch (error) {
      setSaveError(
        error instanceof Error ? error.message : '削除に失敗しました。',
      );
    } finally {
      setSubmitting(false);
    }
  };

  const assigneeName = assigneeId
    ? (projectMembers.find((member) => member.id === assigneeId)?.name ??
      ticket?.assignee?.name ??
      '—')
    : '未割り当て';
  const projectColorStyle: CSSProperties & {
    '--project-border-color'?: string;
  } = {
    '--project-border-color':
      getProjectBorderColor(projectKey ?? null) ?? undefined,
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
          <div className={styles.detailContent}>
            <h3 className={styles.detailTitle}>{title}</h3>
            <dl className={styles.detailGrid}>
              <div className={styles.detailItem}>
                <dt>ステータス</dt>
                <dd>
                  {STATUSES.find((item) => item.value === status)?.label ??
                    status}
                </dd>
              </div>
              <div className={styles.detailItem}>
                <dt>優先度</dt>
                <dd>
                  {PRIORITIES.find((item) => item.value === priority)?.label ??
                    priority}
                </dd>
              </div>
              <div className={styles.detailItem}>
                <dt>担当者</dt>
                <dd>{assigneeName}</dd>
              </div>
            </dl>
            <section
              className={styles.descriptionSection}
              aria-labelledby="ticket-description-title"
            >
              <h3 id="ticket-description-title">説明</h3>
              <p>{description.trim() || '説明はありません。'}</p>
            </section>
            <div className={styles.actions}>
              <button type="button" onClick={onClose} disabled={submitting}>
                閉じる
              </button>
              {canEdit && (
                <button
                  type="button"
                  className={styles.primaryButton}
                  onClick={() => {
                    setSaveError(null);
                    setMode('edit');
                  }}
                >
                  編集
                </button>
              )}
              {canEdit && (
                <button
                  type="button"
                  className={styles.dangerButton}
                  onClick={() => void remove()}
                  disabled={submitting}
                >
                  削除
                </button>
              )}
            </div>
            {saveError && (
              <p className={styles.error} role="alert">
                {saveError}
              </p>
            )}
          </div>
        ) : (
          <form onSubmit={submit} className={styles.form}>
            <label>
              タイトル
              <input
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                required
                maxLength={255}
                autoFocus
              />
            </label>
            <label>
              説明
              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                rows={5}
              />
            </label>
            <label>
              ステータス
              <select
                value={status}
                onChange={(event) =>
                  setStatus(event.target.value as TicketStatus)
                }
              >
                {STATUSES.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              優先度
              <select
                value={priority}
                onChange={(event) =>
                  setPriority(event.target.value as TicketPriority)
                }
              >
                {PRIORITIES.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              担当者
              <select
                value={assigneeId}
                onChange={(event) => setAssigneeId(event.target.value)}
              >
                <option value="">未割り当て</option>
                {ticket?.assignee &&
                  !projectMembers.some(
                    (member) => member.id === ticket.assignee?.id,
                  ) && (
                    <option value={ticket.assignee.id}>
                      {ticket.assignee.name}
                    </option>
                  )}
                {projectMembers.map((member) => (
                  <option key={member.id} value={member.id}>
                    {member.name}
                  </option>
                ))}
              </select>
            </label>
            {saveError && (
              <p className={styles.error} role="alert">
                {saveError}
              </p>
            )}
            <div className={styles.actions}>
              <button type="button" onClick={cancelEdit} disabled={submitting}>
                {ticket ? 'キャンセル' : '閉じる'}
              </button>
              <button type="submit" disabled={submitting || !title.trim()}>
                {submitting ? '保存中...' : '保存'}
              </button>
            </div>
          </form>
        )}
        {ticket && (
          <TicketComments
            ticketId={ticket.id}
            currentUserId={currentUserId}
            currentUserRole={currentUserRole}
          />
        )}
      </section>
    </div>
  );
}
