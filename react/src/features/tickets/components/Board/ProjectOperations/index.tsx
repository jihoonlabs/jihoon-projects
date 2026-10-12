'use client';

import { useRef, useState, type FormEvent } from 'react';
import {
  archiveProject,
  renameProject,
  restoreProject,
} from '@/features/tickets/api/projectApi';
import type { Project } from '@/features/tickets/types/project';
import styles from './index.module.css';

interface Props {
  project: Project;
  canRename: boolean;
  onChanged: (project: Project) => void;
  onPendingChange: (pending: boolean) => void;
}

export default function ProjectOperations({
  project,
  canRename,
  onChanged,
  onPendingChange,
}: Props) {
  const [name, setName] = useState(project.name);
  const [confirmArchive, setConfirmArchive] = useState(false);
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (operation: () => Promise<Project>) => {
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    onPendingChange(true);
    setError(null);
    try {
      const updated = await operation();
      setName(updated.name);
      setConfirmArchive(false);
      onChanged(updated);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : 'プロジェクトを更新できませんでした。',
      );
    } finally {
      pending.current = false;
      setBusy(false);
      onPendingChange(false);
    }
  };

  const rename = (event: FormEvent) => {
    event.preventDefault();
    if (canRename && name.trim() && name.trim() !== project.name)
      void run(() => renameProject(project.id, name));
  };

  return (
    <section
      id="project-operations"
      aria-labelledby="project-operations-title"
      className={styles.container}
    >
      <h2 id="project-operations-title">{project.name} の設定</h2>
      <p>
        {project.projectKey ?? '—'}・
        {project.archivedAt ? '終了済み' : '稼働中'}
      </p>
      {canRename && (
        <form onSubmit={rename} className={styles.row}>
          <label>
            プロジェクト名を変更
            <input
              required
              maxLength={255}
              value={name}
              onChange={(event) => setName(event.target.value)}
              disabled={busy}
            />
          </label>
          <button
            type="submit"
            disabled={busy || !name.trim() || name.trim() === project.name}
          >
            名前を保存
          </button>
        </form>
      )}
      {project.archivedAt ? (
        <div className={styles.row}>
          <p>復元すると、チケットやメンバーの変更を再開できます。</p>
          <button
            type="button"
            disabled={busy}
            onClick={() => void run(() => restoreProject(project.id))}
          >
            プロジェクトを復元
          </button>
        </div>
      ) : confirmArchive ? (
        <div className={styles.row}>
          <p>
            プロジェクトを終了しますか？チケットとコメントは保持され、終了後は閲覧のみになります。
          </p>
          <button
            type="button"
            disabled={busy}
            onClick={() => void run(() => archiveProject(project.id))}
          >
            終了を確定
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => setConfirmArchive(false)}
          >
            キャンセル
          </button>
        </div>
      ) : (
        <div className={styles.row}>
          <p>
            すべてのチケットが完了したら終了できます。データは削除されません。
          </p>
          <button
            type="button"
            disabled={busy}
            onClick={() => setConfirmArchive(true)}
          >
            プロジェクトを終了
          </button>
        </div>
      )}
      {busy && <p role="status">更新中...</p>}
      {error && (
        <p role="alert" className={styles.error}>
          {error}
        </p>
      )}
    </section>
  );
}
