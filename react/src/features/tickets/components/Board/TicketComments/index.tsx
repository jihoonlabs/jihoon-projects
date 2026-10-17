'use client';

import { FormEvent, useEffect, useState, useRef } from 'react';
import {
  createTicketComment,
  deleteTicketComment,
  fetchTicketComments,
  updateTicketComment,
} from '@/features/tickets/api/ticketCommentApi';
import styles from './index.module.css';
import type { TicketComment } from '@/features/tickets/types/ticket';

interface TicketCommentsProps {
  ticketId: string;
  currentUserId: number | null;
  currentUserRole?: 'user' | 'admin';
  readOnly?: boolean;
}

export default function TicketComments(props: TicketCommentsProps) {
  return <TicketCommentsContent key={props.ticketId} {...props} />;
}

function TicketCommentsContent({
  ticketId,
  currentUserId,
  currentUserRole,
  readOnly = false,
}: TicketCommentsProps) {
  const requestBusy = useRef(false);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [comments, setComments] = useState<TicketComment[]>([]);
  const [body, setBody] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingBody, setEditingBody] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchTicketComments(ticketId)
      .then((items) => {
        if (active) {
          setComments(items);
          setLoadError(null);
        }
      })
      .catch((reason) => {
        if (active)
          setLoadError(
            reason instanceof Error
              ? reason.message
              : 'コメントの取得に失敗しました。',
          );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [ticketId, loadAttempt]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const submittedBody = body;
    const value = submittedBody.trim();
    if (readOnly || !value || requestBusy.current || loading || loadError)
      return;
    requestBusy.current = true;
    setBusy(true);
    setError(null);
    try {
      const comment = await createTicketComment(ticketId, value);
      setComments((items) => [...items, comment]);
      // 応答待ちの間に書いた次の下書きは消さない。
      setBody((current) => (current === submittedBody ? '' : current));
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : 'コメントの投稿に失敗しました。',
      );
    } finally {
      requestBusy.current = false;
      setBusy(false);
    }
  };

  const saveEdit = async (commentId: string) => {
    const value = editingBody.trim();
    if (readOnly || !value || requestBusy.current || loading || loadError)
      return;
    requestBusy.current = true;
    setBusy(true);
    setError(null);
    try {
      const updated = await updateTicketComment(ticketId, commentId, value);
      setComments((items) =>
        items.map((item) => (item.id === commentId ? updated : item)),
      );
      setEditingId(null);
      setEditingBody('');
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : 'コメントの更新に失敗しました。',
      );
    } finally {
      requestBusy.current = false;
      setBusy(false);
    }
  };

  const remove = async (commentId: string) => {
    if (readOnly || requestBusy.current || loading || loadError) return;
    requestBusy.current = true;
    setBusy(true);
    setError(null);
    try {
      await deleteTicketComment(ticketId, commentId);
      setComments((items) => items.filter((item) => item.id !== commentId));
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : 'コメントの削除に失敗しました。',
      );
    } finally {
      requestBusy.current = false;
      setBusy(false);
    }
  };

  return (
    <section
      className={styles.container}
      aria-labelledby="ticket-comments-title"
    >
      <h3 id="ticket-comments-title">コメント</h3>
      {loading && <p role="status">コメントを取得中...</p>}
      {loadError && (
        <div>
          <p className={styles.error} role="alert">
            {loadError}
          </p>
          <button
            type="button"
            onClick={() => {
              setLoading(true);
              setLoadError(null);
              setLoadAttempt((value) => value + 1);
            }}
          >
            コメントを再取得
          </button>
        </div>
      )}
      {!loading && !loadError && comments.length === 0 ? (
        <p>コメントはまだありません。</p>
      ) : (
        <ul className={styles.list}>
          {comments.map((comment) => (
            <li key={comment.id} className={styles.comment}>
              <div className={styles.meta}>
                <strong>{comment.author.name}</strong>
                {comment.createdAt &&
                  !Number.isNaN(Date.parse(comment.createdAt)) && (
                    <time dateTime={comment.createdAt}>
                      {new Date(comment.createdAt).toLocaleString('ja-JP')}
                    </time>
                  )}
              </div>
              {!readOnly && editingId === comment.id ? (
                <>
                  <textarea
                    aria-label="コメント編集"
                    value={editingBody}
                    onChange={(event) => setEditingBody(event.target.value)}
                    disabled={busy || loading || Boolean(loadError)}
                    maxLength={5000}
                  />
                  <button
                    type="button"
                    disabled={
                      busy ||
                      loading ||
                      Boolean(loadError) ||
                      !editingBody.trim()
                    }
                    onClick={() => saveEdit(comment.id)}
                  >
                    保存
                  </button>
                  <button
                    type="button"
                    disabled={busy || loading || Boolean(loadError)}
                    onClick={() => setEditingId(null)}
                  >
                    キャンセル
                  </button>
                </>
              ) : (
                <>
                  <p className={styles.body}>{comment.body}</p>
                  {!readOnly &&
                    (String(currentUserId) === comment.author.id ||
                      currentUserRole === 'admin') && (
                      <div className={styles.actions}>
                        {String(currentUserId) === comment.author.id && (
                          <button
                            type="button"
                            disabled={busy || loading || Boolean(loadError)}
                            onClick={() => {
                              setEditingId(comment.id);
                              setEditingBody(comment.body);
                            }}
                          >
                            編集
                          </button>
                        )}
                        <button
                          type="button"
                          disabled={busy || loading || Boolean(loadError)}
                          onClick={() => remove(comment.id)}
                        >
                          削除
                        </button>
                      </div>
                    )}
                </>
              )}
            </li>
          ))}
        </ul>
      )}
      {!readOnly && (
        <form className={styles.form} onSubmit={submit}>
          <label>
            コメントを追加
            <textarea
              value={body}
              onChange={(event) => setBody(event.target.value)}
              maxLength={5000}
            />
          </label>
          <button
            type="submit"
            disabled={busy || loading || Boolean(loadError) || !body.trim()}
          >
            {busy ? '送信中...' : '送信'}
          </button>
        </form>
      )}
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
