import modalStyles from '../index.module.css';
import styles from './index.module.css';

interface TicketDetailViewProps {
  title: string;
  status: string;
  priority: string;
  assigneeName: string;
  description: string;
  canEdit: boolean;
  submitting: boolean;
  saveError: string | null;
  onClose: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

export default function TicketDetailView({
  title,
  status,
  priority,
  assigneeName,
  description,
  canEdit,
  submitting,
  saveError,
  onClose,
  onEdit,
  onDelete,
}: TicketDetailViewProps) {
  return (
    <div className={styles.detailContent}>
      <h3 className={styles.detailTitle}>{title}</h3>
      <dl className={styles.detailGrid}>
        <div className={styles.detailItem}>
          <dt>ステータス</dt>
          <dd>{status}</dd>
        </div>
        <div className={styles.detailItem}>
          <dt>優先度</dt>
          <dd>{priority}</dd>
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
      <div className={modalStyles.actions}>
        <button type="button" onClick={onClose} disabled={submitting}>
          閉じる
        </button>
        {canEdit && (
          <button
            type="button"
            className={modalStyles.primaryButton}
            onClick={onEdit}
          >
            編集
          </button>
        )}
        {canEdit && (
          <button
            type="button"
            className={modalStyles.dangerButton}
            onClick={onDelete}
            disabled={submitting}
          >
            削除
          </button>
        )}
      </div>
      {saveError && (
        <p className={modalStyles.error} role="alert">
          {saveError}
        </p>
      )}
    </div>
  );
}
