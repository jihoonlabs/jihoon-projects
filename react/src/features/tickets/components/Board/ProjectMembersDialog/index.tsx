'use client';

import { FormEvent, useEffect, useState } from 'react';
import {
  addProjectMember,
  fetchProjectMembers,
  removeProjectMember,
  updateProjectMember,
} from '@/features/tickets/api/projectApi';
import type { Project, ProjectMember, ProjectPermission, ProjectRole } from '@/features/tickets/types/project';
import styles from './index.module.css';

interface Props {
  project: Project;
  onClose: () => void;
}

export default function ProjectMembersDialog({ project, onClose }: Props) {
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<ProjectRole>('member');
  const [permission, setPermission] = useState<ProjectPermission>('write');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = async () => {
    setMembers(await fetchProjectMembers(project.id));
  };

  useEffect(() => {
    let active = true;
    fetchProjectMembers(project.id)
      .then((items) => { if (active) setMembers(items); })
      .catch((reason) => { if (active) setError(reason instanceof Error ? reason.message : 'メンバーの取得に失敗しました。'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [project.id]);

  const run = async (operation: () => Promise<unknown>) => {
    setBusy(true);
    setError(null);
    try { await operation(); await reload(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'メンバーを更新できませんでした。'); }
    finally { setBusy(false); }
  };

  const add = (event: FormEvent) => {
    event.preventDefault();
    if (!email.trim()) return;
    void run(async () => {
      await addProjectMember(project.id, { email: email.trim(), role, permission });
      setEmail('');
    });
  };

  return (
    <div className={styles.backdrop} role="presentation" onMouseDown={onClose}>
      <section className={styles.dialog} role="dialog" aria-modal="true" aria-labelledby="project-members-title" onMouseDown={(event) => event.stopPropagation()}>
        <h2 id="project-members-title">{project.name} のメンバー管理</h2>
        {loading ? <p>読み込み中...</p> : (
          <ul className={styles.memberList}>
            {members.map((member) => (
              <li key={member.id} className={styles.member}>
                <span className={styles.memberName}>{member.name} ({member.email ?? 'メールアドレスなし'})</span>
                <label className={styles.field}>役割
                  <select aria-label={`${member.name} の役割`} value={member.role} disabled={busy} onChange={(event) => void run(() => updateProjectMember(project.id, member.id, { role: event.target.value as ProjectRole, permission: member.permission }))}>
                    <option value="member">メンバー</option><option value="leader">リーダー</option>
                  </select>
                </label>
                <label className={styles.field}>権限
                  <select aria-label={`${member.name} の権限`} value={member.permission} disabled={busy} onChange={(event) => void run(() => updateProjectMember(project.id, member.id, { role: member.role, permission: event.target.value as ProjectPermission }))}>
                    <option value="read">閲覧</option><option value="write">編集</option>
                  </select>
                </label>
                <button type="button" disabled={busy} onClick={() => void run(() => removeProjectMember(project.id, member.id))}>削除</button>
              </li>
            ))}
          </ul>
        )}
        <form className={styles.addForm} onSubmit={add}>
          <label className={styles.field}>メールアドレス<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
          <label className={styles.field}>役割<select value={role} onChange={(event) => setRole(event.target.value as ProjectRole)}><option value="member">メンバー</option><option value="leader">リーダー</option></select></label>
          <label className={styles.field}>権限<select value={permission} onChange={(event) => setPermission(event.target.value as ProjectPermission)}><option value="read">閲覧</option><option value="write">編集</option></select></label>
          <button type="submit" disabled={busy || !email.trim()}>メンバーを追加</button>
        </form>
        {error && <p className={styles.error} role="alert">{error}</p>}
        <div className={styles.actions}><button type="button" onClick={onClose}>閉じる</button></div>
      </section>
    </div>
  );
}
