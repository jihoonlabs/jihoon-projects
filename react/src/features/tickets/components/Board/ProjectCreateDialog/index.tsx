'use client';

import { FormEvent, useState } from 'react';
import { createProject } from '@/features/tickets/api/projectApi';
import type { Project } from '@/features/tickets/types/project';
import styles from './index.module.css';

interface Props {
  onClose: () => void;
  onCreated: (project: Project) => void;
}

export default function ProjectCreateDialog({ onClose, onCreated }: Props) {
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const value = name.trim();
    if (!value || busy) return;
    setBusy(true);
    setError(null);
    try {
      const project = await createProject(value);
      onCreated(project);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'プロジェクトを作成できませんでした。');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className={styles.backdrop}>
      <section className={styles.dialog} role="dialog" aria-modal="true" aria-labelledby="project-create-title">
        <h2 id="project-create-title">プロジェクト作成</h2>
        <p>作成すると3文字のプロジェクトキーが自動発行されます。</p>
        <form onSubmit={(event) => void submit(event)}>
          <label className={styles.field}>
            プロジェクト名
            <input autoFocus required maxLength={255} value={name} disabled={busy} onChange={(event) => setName(event.target.value)} />
          </label>
          {error && <p role="alert" className={styles.error}>{error}</p>}
          <div className={styles.actions}>
            <button type="button" disabled={busy} onClick={onClose}>キャンセル</button>
            <button type="submit" disabled={busy || !name.trim()}>{busy ? '作成中...' : '作成する'}</button>
          </div>
        </form>
      </section>
    </div>
  );
}
