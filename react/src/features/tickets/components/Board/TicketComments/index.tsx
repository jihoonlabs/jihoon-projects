'use client';

import { FormEvent, useEffect, useRef, useState } from 'react';
import {
  createTicketComment,
  deleteTicketComment,
  fetchTicketComments,
  updateTicketComment,
} from '@/features/tickets/api/ticketCommentApi';
import type { TicketComment } from '@/features/tickets/types/ticket';
import styles from './index.module.css';

interface TicketCommentsProps {
  ticketId: string;
  currentUserId: number | null;
  currentUserRole?: 'user' | 'admin';
}

export default function TicketComments(props: TicketCommentsProps) {
  return <TicketCommentsContent key={props.ticketId} {...props} />;
}

function TicketCommentsContent({
  ticketId,
  currentUserId,
  currentUserRole,
}: TicketCommentsProps) {
  const [comments, setComments] = useState<TicketComment[]>([]);
  const [body, setBody] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingBody, setEditingBody] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pendingList = useRef(true);
  const changesDuringLoad = useRef(new Map<string, TicketComment | null>());
  const inputRevision = useRef(0);

  useEffect(() => {
    let active = true;
    fetchTicketComments(ticketId)
      .then((items) => {
        if (active) {
          // 初期GETより新しい成功済みの投稿・編集・削除を優先する。
          const merged = new Map(items.map((item) => [item.id, item]));
          for (const [id, comment] of changesDuringLoad.current) {
            if (comment) merged.set(id, comment);
            else merged.delete(id);
          }
          pendingList.current = false;
          changesDuringLoad.current.clear();
          setComments([...merged.values()]);
        }
      })
      .catch((reason) => {
        if (active)
          setError(
            reason instanceof Error
              ? reason.message
              : 'コメントの取得に失敗しました。',
          );
      });
    return () => {
      active = false;
    };
  }, [ticketId]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const value = body.trim();
    if (!value || busy) return;
    const submittedRevision = inputRevision.current;
    setBusy(true);
    setError(null);
    try {
      const comment = await createTicketComment(ticketId, value);
      if (pendingList.current)
        changesDuringLoad.current.set(comment.id, comment);
      setComments((items) => [...items, comment]);
      if (inputRevision.current === submittedRevision) setBody('');
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : 'コメントの投稿に失敗しました。',
      );
    } finally {
      setBusy(false);
    }
  };

  const saveEdit = async (commentId: string) => {
    const value = editingBody.trim();
    if (!value || busy) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await updateTicketComment(ticketId, commentId, value);
      if (pendingList.current)
        changesDuringLoad.current.set(commentId, updated);
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
      setBusy(false);
    }
  };

  const remove = async (commentId: string) => {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await deleteTicketComment(ticketId, commentId);
      if (pendingList.current) changesDuringLoad.current.set(commentId, null);
      setComments((items) => items.filter((item) => item.id !== commentId));
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : 'コメントの削除に失敗しました。',
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className={styles.section} aria-labelledby="ticket-comments-title">
      <h3 id="ticket-comments-title">コメント</h3>
      {comments.length === 0 ? (
        <p className={styles.empty}>コメントはまだありません。</p>
      ) : (
        <ul className={styles.list}>
          {comments.map((comment) => (
            <li className={styles.comment} key={comment.id}>
              <strong>{comment.author.name}</strong>
              {editingId === comment.id ? (
                <>
                  <label>
                    コメント編集
                    <textarea
                      aria-label="コメント編集"
                      value={editingBody}
                      onChange={(event) => setEditingBody(event.target.value)}
                      maxLength={5000}
                    />
                  </label>
                  <div className={styles.actions}>
                    <button
                      type="button"
                      disabled={busy || !editingBody.trim()}
                      onClick={() => saveEdit(comment.id)}
                    >
                      保存
                    </button>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => setEditingId(null)}
                    >
                      キャンセル
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <p className={styles.body}>{comment.body}</p>
                  {(String(currentUserId) === comment.author.id ||
                    currentUserRole === 'admin') && (
                    <div className={styles.actions}>
                      {String(currentUserId) === comment.author.id && (
                        <button
                          type="button"
                          disabled={busy}
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
                        disabled={busy}
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
      <form className={styles.form} onSubmit={submit}>
        <label>
          コメントを追加
          <textarea
            value={body}
            onChange={(event) => {
              inputRevision.current += 1;
              setBody(event.target.value);
            }}
            maxLength={5000}
          />
        </label>
        <div className={styles.actions}>
          <button
            className={styles.primary}
            type="submit"
            disabled={busy || !body.trim()}
          >
            {busy ? '送信中...' : '送信'}
          </button>
        </div>
      </form>
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
