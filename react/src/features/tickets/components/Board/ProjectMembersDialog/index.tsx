'use client';

import { type FormEvent, useEffect, useRef, useState } from 'react';
import {
  addProjectMember,
  fetchProjectMembers,
  removeProjectMember,
  transferProjectLeader,
  updateProjectMember,
} from '@/features/tickets/api/projectApi';
import type {
  Project,
  ProjectMember,
  ProjectPermission,
} from '@/features/tickets/types/project';
import styles from './index.module.css';

interface Props {
  project: Project;
  canManage?: boolean;
  onMembersChanged?: (members: ProjectMember[]) => void;
  onClose: () => void;
}

export default function ProjectMembersDialog({
  project,
  canManage = true,
  onMembersChanged,
  onClose,
}: Props) {
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [email, setEmail] = useState('');
  const [permission, setPermission] = useState<ProjectPermission>('write');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const [outOfDate, setOutOfDate] = useState(false);
  const [transferTo, setTransferTo] = useState<ProjectMember | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const dialog = useRef<HTMLElement>(null);
  const allowChanges =
    canManage && !project.archivedAt && !loading && !busy && !outOfDate;

  useEffect(() => {
    const trigger = document.activeElement as HTMLElement | null;
    heading.current?.focus();
    return () => {
      if (trigger?.isConnected) trigger.focus();
    };
  }, []);

  useEffect(() => {
    let active = true;
    fetchProjectMembers(project.id)
      .then((items) => {
        if (active) setMembers(items);
      })
      .catch((reason) => {
        if (active) {
          setOutOfDate(true);
          setError(
            reason instanceof Error
              ? reason.message
              : 'メンバーの取得に失敗しました。',
          );
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [project.id]);

  const reload = async () => {
    const items = await fetchProjectMembers(project.id);
    setMembers(items);
    onMembersChanged?.(items);
    setOutOfDate(false);
  };

  const retry = async () => {
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    setError(null);
    try {
      await reload();
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : 'メンバーの取得に失敗しました。',
      );
    } finally {
      pending.current = false;
      setBusy(false);
    }
  };

  const run = async (operation: () => Promise<unknown>) => {
    if (!allowChanges || pending.current) return;
    pending.current = true;
    setBusy(true);
    setError(null);
    setNotice(null);
    let saved = false;
    try {
      await operation();
      saved = true;
      setTransferTo(null);
      setNotice('メンバーの変更を保存しました。');
      await reload();
    } catch (reason) {
      if (saved) setOutOfDate(true);
      setError(
        saved
          ? '変更は保存されました。メンバー一覧を再取得してください。'
          : reason instanceof Error
            ? reason.message
            : 'メンバーを更新できませんでした。',
      );
    } finally {
      pending.current = false;
      setBusy(false);
    }
  };

  const add = (event: FormEvent) => {
    event.preventDefault();
    if (!email.trim()) return;
    void run(async () => {
      await addProjectMember(project.id, {
        email: email.trim(),
        role: 'member',
        permission,
      });
      setEmail('');
    });
  };

  const transfer = () => {
    if (!transferTo) return;
    const target = transferTo;
    void run(async () => {
      const updated = await transferProjectLeader(project.id, target.id);
      // 成功した譲渡を即座に反映し、再取得失敗時も旧leaderの操作権限を残さない。
      const items = members.map((member) =>
        member.id === updated.id
          ? updated
          : member.role === 'leader'
            ? { ...member, role: 'member' as const }
            : member,
      );
      setMembers(items);
      onMembersChanged?.(items);
    });
  };

  return (
    <div
      className={styles.backdrop}
      role="presentation"
      onMouseDown={() => {
        if (!busy) onClose();
      }}
    >
      <section
        ref={dialog}
        className={styles.dialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby="project-members-title"
        onMouseDown={(event) => event.stopPropagation()}
        onKeyDown={(event) => {
          if (event.key === 'Escape') {
            event.stopPropagation();
            if (!busy) onClose();
          }
          if (event.key === 'Tab') {
            const items = Array.from(
              dialog.current?.querySelectorAll<HTMLElement>(
                'button:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex="0"]',
              ) ?? [],
            );
            if (items.length === 0) {
              event.preventDefault();
              heading.current?.focus();
              return;
            }
            const first = items[0];
            const last = items[items.length - 1];
            if (
              event.shiftKey &&
              (document.activeElement === first ||
                document.activeElement === heading.current)
            ) {
              event.preventDefault();
              last?.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
              event.preventDefault();
              first?.focus();
            }
          }
        }}
      >
        <h2 ref={heading} tabIndex={-1} id="project-members-title">
          {project.name} のメンバー管理
        </h2>
        {!canManage && (
          <p>
            管理権限が変更されました。現在はメンバー一覧の閲覧のみ可能です。
          </p>
        )}
        {loading ? (
          <p>読み込み中...</p>
        ) : (
          <ul className={styles.memberList}>
            {members.map((member) => (
              <li key={member.id} className={styles.member}>
                <span className={styles.memberName}>
                  {member.name} ({member.email ?? 'メールアドレスなし'})・
                  {member.role === 'leader' ? 'リーダー' : 'メンバー'}
                </span>
                <label className={styles.field}>
                  権限
                  <select
                    aria-label={`${member.name} の権限`}
                    value={member.permission}
                    disabled={!allowChanges}
                    onChange={(event) =>
                      void run(() =>
                        updateProjectMember(project.id, member.id, {
                          role: member.role,
                          permission: event.target.value as ProjectPermission,
                        }),
                      )
                    }
                  >
                    <option value="read">閲覧</option>
                    <option value="write">編集</option>
                  </select>
                </label>
                {canManage && member.role !== 'leader' && (
                  <>
                    <button
                      type="button"
                      disabled={!allowChanges}
                      onClick={() => setTransferTo(member)}
                      aria-label={`${member.name} をリーダーにする`}
                    >
                      リーダーにする
                    </button>
                    <button
                      type="button"
                      disabled={!allowChanges}
                      onClick={() =>
                        void run(() =>
                          removeProjectMember(project.id, member.id),
                        )
                      }
                      aria-label={`${member.name} をメンバーから削除`}
                    >
                      削除
                    </button>
                  </>
                )}
              </li>
            ))}
          </ul>
        )}
        {canManage && transferTo && (
          <div className={styles.confirmation}>
            <p>
              {transferTo.name}{' '}
              にリーダーを引き継ぎますか？現在のリーダーはメンバーになります。編集・閲覧権限は変わりません。
            </p>
            <button type="button" disabled={!allowChanges} onClick={transfer}>
              リーダー引き継ぎを確定
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => setTransferTo(null)}
            >
              キャンセル
            </button>
          </div>
        )}
        {canManage && !project.archivedAt && (
          <form className={styles.addForm} onSubmit={add}>
            <label className={styles.field}>
              メールアドレス
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                disabled={!allowChanges}
              />
            </label>
            <label className={styles.field}>
              権限
              <select
                value={permission}
                onChange={(event) =>
                  setPermission(event.target.value as ProjectPermission)
                }
                disabled={!allowChanges}
              >
                <option value="read">閲覧</option>
                <option value="write">編集</option>
              </select>
            </label>
            <button type="submit" disabled={!allowChanges || !email.trim()}>
              メンバーを追加
            </button>
          </form>
        )}
        {notice && <p role="status">{notice}</p>}
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
        {outOfDate && (
          <button type="button" disabled={busy} onClick={() => void retry()}>
            メンバー一覧を再取得
          </button>
        )}
        <div className={styles.actions}>
          <button type="button" disabled={busy} onClick={onClose}>
            閉じる
          </button>
        </div>
      </section>
    </div>
  );
}
