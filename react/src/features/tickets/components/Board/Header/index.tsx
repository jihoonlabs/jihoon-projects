'use client';

import styles from './index.module.css';
import type { Project } from '@/features/tickets/types/project';

interface HeaderProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  assigneeFilter: string;
  onAssigneeChange: (value: string) => void;
  onCreate: () => void;
  projects: Project[];
  selectedProjectId: string;
  onProjectChange: (projectId: string) => void;
  canWrite: boolean;
  canCreateProject: boolean;
  onCreateProject: () => void;
  showAllProjects: boolean;
  canManageMembers: boolean;
  onManageMembers: () => void;
}

export default function Header({
  searchQuery,
  onSearchChange,
  assigneeFilter,
  onAssigneeChange,
  onCreate,
  projects,
  selectedProjectId,
  onProjectChange,
  canWrite,
  canCreateProject,
  onCreateProject,
  showAllProjects,
  canManageMembers,
  onManageMembers,
}: HeaderProps) {
  return (
    <header className={styles.container}>
      <div className={styles.leftSection}>
        <h1 className={styles.title}>チケットボード</h1>

        <select aria-label="プロジェクト" className={styles.selectFilter} value={selectedProjectId} onChange={(event) => onProjectChange(event.target.value)} disabled={projects.length === 0 && !showAllProjects}>
          {showAllProjects && <option value="">すべてのプロジェクト</option>}
          {projects.length === 0 && !showAllProjects && <option value="">利用可能なプロジェクトがありません</option>}
          {projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}
        </select>

        <div className={styles.filterGroup}>
          <input
            type="text"
            aria-label="チケット検索"
            placeholder="チケットを検索..."
            className={styles.searchInput}
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
          />
          <select
            aria-label="担当者フィルター"
            className={styles.selectFilter}
            value={assigneeFilter}
            onChange={(e) => onAssigneeChange(e.target.value)}
          >
            <option value="ALL">すべての担当者</option>
            <option value="ME">自分に割り当て</option>
            <option value="UNASSIGNED">未割り当て</option>
          </select>
        </div>
      </div>

      <div className={styles.rightSection}>
        {canCreateProject && <button type="button" onClick={onCreateProject}>+ プロジェクト作成</button>}
        {canManageMembers && <button type="button" onClick={onManageMembers}>メンバー管理</button>}
        {canWrite && <button type="button" className={styles.createBtn} onClick={onCreate}>
          + チケット作成
        </button>}
      </div>
    </header>
  );
}
