'use client';

import { FormEvent, useEffect, useState } from 'react';
import type {
  CreateTicketInput,
  Ticket,
  TicketPriority,
  TicketStatus,
  UpdateTicketInput,
} from '@/features/tickets/types/ticket';
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
  currentUserName?: string | null;
  onClose: () => void;
  onCreate: (input: CreateTicketInput) => Promise<void>;
  onUpdate: (id: string, input: UpdateTicketInput) => Promise<void>;
}

export default function TicketModal({
  ticket,
  currentUserId,
  currentUserName,
  onClose,
  onCreate,
  onUpdate,
}: TicketModalProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState<TicketStatus>('TODO');
  const [priority, setPriority] = useState<TicketPriority>('MEDIUM');
  const [assigneeId, setAssigneeId] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    setTitle(ticket?.title ?? '');
    setDescription(ticket?.description ?? '');
    setStatus(ticket?.status ?? 'TODO');
    setPriority(ticket?.priority ?? 'MEDIUM');
    setAssigneeId(ticket?.assignee?.id ?? '');
    setSaveError(null);
  }, [ticket]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!title.trim() || submitting) return;
    setSubmitting(true);
    setSaveError(null);
    try {
      const input = {
        title: title.trim(),
        description: description.trim() || null,
        status,
        priority,
        assigneeId: assigneeId || null,
      };
      if (ticket) await onUpdate(ticket.id, input);
      else await onCreate(input);
      onClose();
    } catch (error) {
      setSaveError(
        error instanceof Error ? error.message : '保存に失敗しました。',
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={styles.backdrop} role="presentation" onMouseDown={onClose}>
      <section
        className={styles.modal}
        role="dialog"
        aria-modal="true"
        aria-labelledby="ticket-modal-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <h2 id="ticket-modal-title">{ticket ? 'チケット編集' : 'チケット作成'}</h2>
        <form onSubmit={submit} className={styles.form}>
          <label>
            タイトル
            <input value={title} onChange={(e) => setTitle(e.target.value)} required maxLength={255} autoFocus />
          </label>
          <label>
            説明
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={4} />
          </label>
          <label>
            ステータス
            <select value={status} onChange={(e) => setStatus(e.target.value as TicketStatus)}>
              {STATUSES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
            </select>
          </label>
          <label>
            優先度
            <select value={priority} onChange={(e) => setPriority(e.target.value as TicketPriority)}>
              {PRIORITIES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
            </select>
          </label>
          <label>
            担当者
            <select value={assigneeId} onChange={(e) => setAssigneeId(e.target.value)}>
              <option value="">未割り当て</option>
              {currentUserId !== null && (
                <option value={String(currentUserId)}>{currentUserName ?? '自分'}</option>
              )}
            </select>
          </label>
          {saveError && <p className={styles.error} role="alert">{saveError}</p>}
          <div className={styles.actions}>
            <button type="button" onClick={onClose} disabled={submitting}>キャンセル</button>
            <button type="submit" disabled={submitting || !title.trim()}>
              {submitting ? '保存中...' : '保存'}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
