import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { fetchTicket } from '@/features/tickets/api/ticketApi';
import type { Ticket } from '@/features/tickets/types/ticket';
import { detailError } from '../detailError';
import styles from '../index.module.css';

interface TicketDetailLoaderProps {
  ticketId: string;
  onClose: () => void;
  children: (ticket: Ticket) => ReactNode;
}

export default function TicketDetailLoader({
  ticketId,
  onClose,
  children,
}: TicketDetailLoaderProps) {
  const [result, setResult] = useState<{
    attempt: number;
    ticket?: Ticket;
    error?: string;
  } | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    // 中断だけに依存せず、閉じた画面・別Ticketへの遅延応答も破棄する。
    void fetchTicket(ticketId, controller.signal)
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
  }, [ticketId, attempt]);

  const loaded = result?.attempt === attempt ? result.ticket : null;
  const error = result?.attempt === attempt ? result.error : null;
  if (loaded && loaded.id === ticketId) return children(loaded);

  return (
    <div className={styles.backdrop} role="presentation" onMouseDown={onClose}>
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
          <button type="button" onClick={onClose}>
            閉じる
          </button>
          {error && (
            <button type="button" onClick={() => setAttempt((value) => value + 1)}>
              再試行
            </button>
          )}
        </div>
      </section>
    </div>
  );
}
