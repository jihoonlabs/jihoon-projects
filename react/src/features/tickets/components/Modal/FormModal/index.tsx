'use client';

import { useState, useEffect, FormEvent } from 'react';
import { BaseModal } from '@/shared/components/BaseModal';
import { Ticket, TicketStatus, TicketPriority } from '@/features/tickets/types/ticket';
import { useTicketStore } from '@/features/tickets/store/useTicketStore';
import styles from './index.module.css';

const ASSIGNEE_OPTIONS = [
  { id: 'unassigned', name: '未割り当て', avatar: '👤' },
  { id: 'park.jihoon', name: 'パク・ジフン', avatar: '👨‍💻' },
  { id: 'kim.dev', name: 'キム・開発', avatar: '👩‍💻' },
  { id: 'lee.design', name: 'イ・デザイン', avatar: '🎨' },
];

interface TicketFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialData?: Ticket | null;
}

export function TicketFormModal({
  isOpen,
  onClose,
  initialData,
}: TicketFormModalProps) {
  const { addTicket, updateTicket } = useTicketStore();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [assignee, setAssignee] = useState('unassigned');
  const [status, setStatus] = useState<TicketStatus>('TODO');
  const [priority, setPriority] = useState<TicketPriority>('MEDIUM');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isEditMode = Boolean(initialData);

  useEffect(() => {
    if (initialData) {
      setTitle(initialData.title);
      setDescription(initialData.description || '');
      setAssignee(initialData.assignee || 'unassigned');
      setStatus(initialData.status);
      setPriority(initialData.priority);
    } else {
      setTitle('');
      setDescription('');
      setAssignee('unassigned');
      setStatus('TODO');
      setPriority('MEDIUM');
    }
  }, [initialData, isOpen]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!title.trim() || isSubmitting) return;

    try {
      setIsSubmitting(true);
      const payload = {
        title,
        description,
        assignee: assignee === 'unassigned' ? '' : assignee,
        status,
        priority,
      };

      if (isEditMode && initialData) {
        await updateTicket(initialData.id, payload);
      } else {
        await addTicket(payload);
      }
      onClose();
    } catch (error) {
      console.error('Failed to save ticket:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? '課題の編集' : '課題の作成'}
      maxWidth="640px"
    >
      <form onSubmit={handleSubmit} className={styles.form}>
        {/* 요약 */}
        <div className={styles.field}>
          <label htmlFor="ticket-title" className={styles.label}>
            概要 <span className={styles.required}>*</span>
          </label>
          <input
            id="ticket-title"
            type="text"
            className={styles.inputTitle}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="概要を入力してください"
            required
          />
        </div>

        {/* 상태 / 우선순위 / 담당자 */}
        <div className={styles.metaGrid}>
          <div className={styles.field}>
            <label htmlFor="ticket-status" className={styles.label}>
              ステータス
            </label>
            <select
              id="ticket-status"
              className={styles.select}
              value={status}
              onChange={(e) => setStatus(e.target.value as TicketStatus)}
            >
              <option value="TODO">📋 未着手 (TO DO)</option>
              <option value="IN_PROGRESS">⚡ 進行中 (IN PROGRESS)</option>
              <option value="DONE">✅ 完了 (DONE)</option>
            </select>
          </div>

          <div className={styles.field}>
            <label htmlFor="ticket-priority" className={styles.label}>
              優先度
            </label>
            <select
              id="ticket-priority"
              className={styles.select}
              value={priority}
              onChange={(e) => setPriority(e.target.value as TicketPriority)}
            >
              <option value="LOW">🟢 低 (Low)</option>
              <option value="MEDIUM">🟡 中 (Medium)</option>
              <option value="HIGH">🟠 高 (High)</option>
              <option value="URGENT">🔴 最高 (Urgent)</option>
            </select>
          </div>

          <div className={styles.field}>
            <label htmlFor="ticket-assignee" className={styles.label}>
              担当者
            </label>
            <select
              id="ticket-assignee"
              className={styles.select}
              value={assignee}
              onChange={(e) => setAssignee(e.target.value)}
            >
              {ASSIGNEE_OPTIONS.map((opt) => (
                <option key={opt.id} value={opt.id}>
                  {opt.avatar} {opt.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* 설명 */}
        <div className={styles.field}>
          <label htmlFor="ticket-description" className={styles.label}>
            説明
          </label>
          <textarea
            id="ticket-description"
            className={styles.textarea}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="説明を入力してください..."
            rows={5}
          />
        </div>

        {/* 하단 버튼 */}
        <div className={styles.actions}>
          <button
            type="button"
            className={styles.cancelButton}
            onClick={onClose}
            disabled={isSubmitting}
          >
            キャンセル
          </button>
          <button
            type="submit"
            className={styles.submitButton}
            disabled={isSubmitting}
          >
            {isSubmitting ? '保存中...' : isEditMode ? '保存' : '作成'}
          </button>
        </div>
      </form>
    </BaseModal>
  );
}