'use client';

import { FormEvent, useEffect, useState } from 'react';
import {
  createTicketComment,
  deleteTicketComment,
  fetchTicketComments,
  updateTicketComment,
} from '@/features/tickets/api/ticketCommentApi';
import type { TicketComment } from '@/features/tickets/types/ticket';

interface TicketCommentsProps {
  ticketId: string;
  currentUserId: number | null;
  currentUserRole?: 'user' | 'admin';
}

export default function TicketComments({
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

  useEffect(() => {
    let active = true;
    fetchTicketComments(ticketId)
      .then((items) => {
        if (active) {
          setComments(items);
          setError(null);
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
    setBusy(true);
    setError(null);
    try {
      const comment = await createTicketComment(ticketId, value);
      setComments((items) => [...items, comment]);
      setBody('');
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
    <section aria-labelledby="ticket-comments-title">
      <h3 id="ticket-comments-title">コメント</h3>
      {comments.length === 0 ? (
        <p>コメントはまだありません。</p>
      ) : (
        <ul>
          {comments.map((comment) => (
            <li key={comment.id}>
              <strong>{comment.author.name}</strong>
              {editingId === comment.id ? (
                <>
                  <textarea
                    aria-label="コメント編集"
                    value={editingBody}
                    onChange={(event) => setEditingBody(event.target.value)}
                    maxLength={5000}
                  />
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
                </>
              ) : (
                <>
                  <p>{comment.body}</p>
                  {(String(currentUserId) === comment.author.id || currentUserRole === 'admin') && (
                    <div>
                      {String(currentUserId) === comment.author.id && <button
                        type="button"
                        disabled={busy}
                        onClick={() => {
                          setEditingId(comment.id);
                          setEditingBody(comment.body);
                        }}
                      >
                        編集
                      </button>}
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
      <form onSubmit={submit}>
        <label>
          コメントを追加
          <textarea
            value={body}
            onChange={(event) => setBody(event.target.value)}
            maxLength={5000}
          />
        </label>
        <button type="submit" disabled={busy || !body.trim()}>
          {busy ? '送信中...' : '送信'}
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
