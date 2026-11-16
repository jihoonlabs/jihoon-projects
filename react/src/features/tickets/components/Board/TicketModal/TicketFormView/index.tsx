import type { FormEvent } from 'react';
import type {
  Ticket,
  TicketPriority,
  TicketStatus,
} from '@/features/tickets/types/ticket';
import type { Project, ProjectMember } from '@/features/tickets/types/project';
import modalStyles from '../index.module.css';
import styles from './index.module.css';

interface TicketFormViewProps {
  ticket: Ticket | null;
  projectId: string;
  projectSelection?: {
    projects: Project[];
    onChange: (id: string) => void;
    message?: string;
    onRetry?: () => void;
  };
  projectMembers: ProjectMember[];
  title: string;
  description: string;
  status: TicketStatus;
  priority: TicketPriority;
  assigneeId: string;
  statuses: Array<{ value: TicketStatus; label: string }>;
  priorities: Array<{ value: TicketPriority; label: string }>;
  submitting: boolean;
  readOnly: boolean;
  unavailable: boolean;
  saveError: string | null;
  conflict: boolean;
  reloading: boolean;
  reloadError: string | null;
  latest: Ticket | null;
  onSubmit: (event: FormEvent) => void;
  onProjectChange: (id: string) => void;
  onTitleChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  onStatusChange: (value: TicketStatus) => void;
  onPriorityChange: (value: TicketPriority) => void;
  onAssigneeChange: (value: string) => void;
  onLoadLatest: () => void;
  onUseLatest: () => void;
  onCancel: () => void;
}

export default function TicketFormView({
  ticket,
  projectId,
  projectSelection,
  projectMembers,
  title,
  description,
  status,
  priority,
  assigneeId,
  statuses,
  priorities,
  submitting,
  readOnly,
  unavailable,
  saveError,
  conflict,
  reloading,
  reloadError,
  latest,
  onSubmit,
  onProjectChange,
  onTitleChange,
  onDescriptionChange,
  onStatusChange,
  onPriorityChange,
  onAssigneeChange,
  onLoadLatest,
  onUseLatest,
  onCancel,
}: TicketFormViewProps) {
  return (
    <form onSubmit={onSubmit} className={styles.form}>
      {!ticket && projectSelection && (
        <>
          <label>
            作成先プロジェクト
            <select
              value={projectId}
              disabled={submitting}
              onChange={(event) => onProjectChange(event.target.value)}
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
          onChange={(event) => onTitleChange(event.target.value)}
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
          onChange={(event) => onDescriptionChange(event.target.value)}
          rows={5}
        />
      </label>
      <label>
        ステータス
        <select
          value={status}
          disabled={submitting}
          onChange={(event) =>
            onStatusChange(event.target.value as TicketStatus)
          }
        >
          {statuses.map((item) => (
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
            onPriorityChange(event.target.value as TicketPriority)
          }
        >
          {priorities.map((item) => (
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
          onChange={(event) => onAssigneeChange(event.target.value)}
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
        <p className={modalStyles.error} role="alert">
          {saveError}
        </p>
      )}
      {conflict && (
        <section aria-label="競合の解決">
          <button type="button" onClick={onLoadLatest} disabled={reloading}>
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
              <button type="button" onClick={onUseLatest} disabled={unavailable}>
                最新情報で編集し直す（入力を置き換える）
              </button>
            </div>
          )}
        </section>
      )}
      <div className={modalStyles.actions}>
        <button type="button" onClick={onCancel} disabled={submitting}>
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
  );
}
