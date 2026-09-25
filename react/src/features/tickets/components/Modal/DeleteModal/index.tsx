'use client';

import { useState } from 'react';
import { BaseModal } from '@/shared/components/BaseModal';
import { useTicketStore } from '@/features/tickets/store/useTicketStore';
import styles from './index.module.css';

interface DeleteModalProps {
  isOpen: boolean;
  onClose: () => void;
  ticketId: string | null;
  ticketTitle?: string;
}

export function DeleteModal({
  isOpen,
  onClose,
  ticketId,
  ticketTitle,
}: DeleteModalProps) {
  const { deleteTicket } = useTicketStore();
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (!ticketId || isDeleting) return;

    try {
      setIsDeleting(true);
      await deleteTicket(ticketId);
      onClose();
    } catch (error) {
      console.error('Failed to delete ticket:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={onClose}
      title="課題の削除"
      maxWidth="400px"
    >
      <div className={styles.container}>
        <div className={styles.warningBox}>
          <span className={styles.icon}>⚠️</span>
          <p className={styles.message}>
            この操作は取り消せません。本当に削除しますか？
          </p>
        </div>

        {ticketTitle && (
          <div className={styles.targetTitle}>
            対象: <strong>{ticketTitle}</strong>
          </div>
        )}

        <div className={styles.actions}>
          <button
            type="button"
            className={styles.cancelButton}
            onClick={onClose}
            disabled={isDeleting}
          >
            キャンセル
          </button>
          <button
            type="button"
            className={styles.deleteButton}
            onClick={handleDelete}
            disabled={isDeleting}
          >
            {isDeleting ? '削除中...' : '削除する'}
          </button>
        </div>
      </div>
    </BaseModal>
  );
}