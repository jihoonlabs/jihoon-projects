'use client';

import { useState, useRef, type FormEvent } from 'react';
import { createProject } from '@/features/tickets/api/projectApi';
import type { Project } from '@/features/tickets/types/project';
import styles from './index.module.css';

interface Props {
  projects: Project[];
  loading: boolean;
  selectedProjectId: string;
  onSelect: (id: string) => void;
  onCreated: (project: Project) => void;
  onPendingChange?: (pending: boolean) => void;
}

export default function ProjectDirectory({
  projects,
  loading,
  selectedProjectId,
  onSelect,
  onCreated,
  onPendingChange,
}: Props) {
  const [search, setSearch] = useState('');
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const submitting = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const query = search.trim().toLocaleLowerCase('ja-JP');
  const visible = projects.filter((project) =>
    `${project.name} ${project.projectKey ?? ''}`
      .toLocaleLowerCase('ja-JP')
      .includes(query),
  );

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim() || loading || submitting.current) return;
    submitting.current = true;
    setBusy(true);
    onPendingChange?.(true);
    setError(null);
    try {
      const project = await createProject(name);
      onCreated(project);
      setName('');
      setSearch('');
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : 'プロジェクトを作成できませんでした。',
      );
    } finally {
      submitting.current = false;
      setBusy(false);
      onPendingChange?.(false);
    }
  };

  return (
    <section
      id="project-directory"
      aria-labelledby="project-directory-title"
      className={styles.container}
    >
      <div className={styles.heading}>
        <h2 id="project-directory-title">プロジェクト一覧</h2>
        <label className={styles.field}>
          プロジェクトを検索
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="名前・キーで検索"
            type="search"
          />
        </label>
      </div>
      {loading ? (
        <p role="status">プロジェクトを読み込み中...</p>
      ) : visible.length === 0 ? (
        <p>
          {projects.length === 0
            ? 'プロジェクトを作成すると、ここに表示されます。'
            : '一致するプロジェクトがありません。'}
        </p>
      ) : (
        <ul className={styles.list}>
          {visible.map((project) => (
            <li key={project.id}>
              <button
                type="button"
                onClick={() => onSelect(project.id)}
                aria-pressed={project.id === selectedProjectId}
                aria-label={`${project.name} ${project.projectKey ?? ''} ${project.id === selectedProjectId ? '表示中' : 'ボードを開く'}`}
                className={styles.project}
              >
                <strong>{project.name}</strong>
                <span>{project.projectKey ?? 'キー未設定'}</span>
                <span>
                  {project.id === selectedProjectId ? '表示中' : 'ボードを開く'}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={submit} className={styles.form}>
        <h3>プロジェクトを作成</h3>
        <p>作成者がリーダーになります。メンバーは作成後に追加できます。</p>
        <div className={styles.createRow}>
          <label className={styles.field}>
            プロジェクト名
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              required
              maxLength={255}
              disabled={busy}
            />
          </label>
          <button type="submit" disabled={busy || loading || !name.trim()}>
            {busy ? '作成中...' : 'プロジェクトを作成'}
          </button>
        </div>
        {error && (
          <p role="alert" className={styles.error}>
            {error}
          </p>
        )}
      </form>
    </section>
  );
}
