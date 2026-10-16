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
import { fetchTicket, TicketApiError } from '@/features/tickets/api/ticketApi';
import TicketComments from '../TicketComments';
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

function detailError(error: unknown): string {
  if (error instanceof TicketApiError) {
    if (error.status === 404)
      return 'このチケットは削除されたか、存在しません。';
    if (error.status === 403 || error.status === 401)
      return 'このチケットへのアクセス権限がありません。';
  }
  return '最新のチケット情報を取得できませんでした。再試行してください。';
}

export default function TicketModal(props: TicketModalProps) {
  if (!props.ticket) return <TicketModalContent {...props} />;
  return <TicketDetailLoader key={props.ticket.id} {...props} />;
}

function TicketDetailLoader(props: TicketModalProps) {
  const id = props.ticket?.id;
  const [result, setResult] = useState<{
    attempt: number;
    ticket?: Ticket;
    error?: string;
  } | null>(null);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    if (!id) return;
    const controller = new AbortController();
    let active = true;
    // 中断だけに依存せず、閉じた画面・別Ticketへの遅延応答も破棄する。
    void fetchTicket(id, controller.signal)
      .then((ticket) => {
        if (active) setResult({ attempt, ticket });
      })
      .catch((reason) => {
        if (active) setResult({ attempt, error: detailError(reason) });
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [id, attempt]);

  const loaded = result?.attempt === attempt ? result.ticket : null;
  const error = result?.attempt === attempt ? result.error : null;
  if (loaded && loaded.id === id)
    return <TicketModalContent key={id} {...props} ticket={loaded} />;
  return (
    <div
      className={styles.backdrop}
      role="presentation"
      onMouseDown={props.onClose}
    >
      <section
        className={styles.modal}
        role="dialog"
        aria-modal="true"
        aria-labelledby="ticket-modal-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <h2 id="ticket-modal-title" tabIndex={-1}>
          チケット情報
        </h2>
        {error ? (
          <p className={styles.error} role="alert">
            {error}
          </p>
        ) : (
          <p role="status">最新情報を取得中...</p>
        )}
        <div className={styles.actions}>
          <button type="button" onClick={props.onClose}>
            閉じる
          </button>
          {error && (
            <button
              type="button"
              onClick={() => setAttempt((value) => value + 1)}
            >
              再試行
            </button>
          )}
        </div>
      </section>
    </div>
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
  const [ticket, setTicket] = useState(initialTicket);
  const initialValues = {
    title: ticket?.title ?? '',
    description: ticket?.description ?? '',
    status: ticket?.status ?? ('TODO' as TicketStatus),
    priority: ticket?.priority ?? ('MEDIUM' as TicketPriority),
    assigneeId: ticket?.assignee?.id ?? '',
  };
  const savedValues = useRef(initialValues);
  const version = useRef(ticket?.version);
  const [conflict, setConflict] = useState(false);
  const [latest, setLatest] = useState<Ticket | null>(null);
  const [reloadError, setReloadError] = useState<string | null>(null);
  const [reloading, setReloading] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);
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
  const canEdit = !!ticket && !readOnly && !unavailable;
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

  const loadLatest = async () => {
    if (!ticket || reloading) return;
    setReloading(true);
    setReloadError(null);
    try {
      const incoming = await fetchTicket(ticket.id);
      if (alive.current) setLatest(incoming);
    } catch (reason) {
      if (alive.current) {
        setReloadError(detailError(reason));
        if (
          reason instanceof TicketApiError &&
          [401, 403, 404].includes(reason.status)
        )
          setUnavailable(true);
      }
    } finally {
      if (alive.current) setReloading(false);
    }
  };

  const useLatest = () => {
    if (!latest) return;
    // 再取得だけでは入力・保存基準を変更しない。明示操作で編集をやり直す。
    savedValues.current = {
      title: latest.title,
      description: latest.description ?? '',
      status: latest.status,
      priority: latest.priority,
      assigneeId: latest.assignee?.id ?? '',
    };
    version.current = latest.version;
    setTicket(latest);
    restoreSavedValues();
    setLatest(null);
    setConflict(false);
    setSaveError(null);
  };

  const cancelEdit = () => {
    if (ticket) {
      restoreSavedValues();
      setSaveError(null);
      if (conflict) {
        onClose();
        return;
      }
      setMode('detail');
      return;
    }
    onClose();
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (readOnly || unavailable || conflict || !title.trim() || submitting)
      return;
    setSubmitting(true);
    setSaveError(null);
    const fields: UpdateTicketInput = {
      ...(ticket ? { expectedVersion: version.current } : {}),
      title: title.trim(),
      description: description.trim() || null,
      status,
      priority,
      // 同じ詳細画面で再編集する場合も、直前の成功した保存値と比較する。
      ...(ticket && assigneeId === savedValues.current.assigneeId
        ? {}
        : { assigneeId: assigneeId || null }),
    };
    try {
      if (ticket) {
        const updated = await onUpdate(ticket.id, fields);
        if (!alive.current) return;
        version.current = updated.version;
        // 応答のフィールドとバージョンを同じスナップショットとして採用する。
        savedValues.current = {
          title: updated.title,
          description: updated.description ?? '',
          status: updated.status,
          priority: updated.priority,
          assigneeId: updated.assignee?.id ?? '',
        };
        setTicket(updated);
        restoreSavedValues();
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
      if (!alive.current) return;
      if (error instanceof TicketApiError && error.code === 'ticket_conflict') {
        setConflict(true);
        setSaveError(
          '他のユーザーが変更したため保存できませんでした。入力内容は保持されています。',
        );
      } else {
        if (
          error instanceof TicketApiError &&
          [401, 403, 404].includes(error.status)
        )
          setUnavailable(true);
        setSaveError(
          error instanceof TicketApiError &&
            [401, 403, 404].includes(error.status)
            ? detailError(error)
            : error instanceof Error
              ? error.message
              : '保存に失敗しました。',
        );
      }
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
            {!ticket && projectSelection && (
              <>
                <label>
                  作成先プロジェクト
                  <select
                    value={projectId}
                    disabled={submitting}
                    onChange={(event) => {
                      // Project変更で別Projectの担当者を送信しない。その他の下書きは保全する。
                      setAssigneeId('');
                      setSaveError(null);
                      projectSelection.onChange(event.target.value);
                    }}
                  >
                    <option value="ALL">プロジェクトを選択してください</option>
                    {projectSelection.projects
                      .filter((project) => !project.archivedAt)
                      .map((project) => (
                        <option key={project.id} value={project.id}>
                          {project.name}
                        </option>
                      ))}
                  </select>
                </label>
                {projectSelection.message && (
                  <p role="status">{projectSelection.message}</p>
                )}
                {projectSelection.onRetry && (
                  <button type="button" onClick={projectSelection.onRetry}>
                    メンバーと権限を再取得
                  </button>
                )}
              </>
            )}
            <label>
              タイトル
              <input
                value={title}
                disabled={submitting}
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
                disabled={submitting}
                onChange={(event) => setDescription(event.target.value)}
                rows={5}
              />
            </label>
            <label>
              ステータス
              <select
                value={status}
                disabled={submitting}
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
                disabled={submitting}
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
                disabled={submitting}
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
            {conflict && (
              <section aria-label="競合の解決">
                <button
                  type="button"
                  onClick={() => void loadLatest()}
                  disabled={reloading}
                >
                  {reloading ? '取得中...' : '最新情報を再取得'}
                </button>
                {reloadError && <p role="alert">{reloadError}</p>}
                {latest && (
                  <div>
                    <h3>最新情報</h3>
                    <p>タイトル: {latest.title}</p>
                    <p>説明: {latest.description || '説明はありません。'}</p>
                    <p>
                      ステータス: {latest.status} / 優先度: {latest.priority}
                    </p>
                    <p>担当者: {latest.assignee?.name ?? '未割り当て'}</p>
                    <button
                      type="button"
                      onClick={useLatest}
                      disabled={unavailable}
                    >
                      最新情報で編集し直す（入力を置き換える）
                    </button>
                  </div>
                )}
              </section>
            )}
            <div className={styles.actions}>
              <button type="button" onClick={cancelEdit} disabled={submitting}>
                {ticket ? 'キャンセル' : '閉じる'}
              </button>
              <button
                type="submit"
                disabled={
                  readOnly ||
                  submitting ||
                  conflict ||
                  unavailable ||
                  !title.trim()
                }
              >
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
            readOnly={commentsReadOnly}
          />
        )}
      </section>
    </div>
  );
}
