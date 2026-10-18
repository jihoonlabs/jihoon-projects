'use client';

import styles from './index.module.css';
import type { Project } from '@/features/tickets/types/project';

interface HeaderProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  assigneeFilter: string;
  onAssigneeChange: (value: string) => void;
  onCreate: () => void;
  onCreateProject: () => void;
  canCreateTicket: boolean;
  projects: Project[];
  selectedProjectId: string;
  onProjectChange: (projectId: string) => void;
  canWrite: boolean;
  canManageMembers: boolean;
  onManageMembers: () => void;
  canManageProject: boolean;
  operationsOpen: boolean;
  onToggleOperations: () => void;
  projectsOpen: boolean;
  projectsBusy: boolean;
  onToggleProjects: () => void;
}

export default function Header({
  searchQuery,
  onSearchChange,
  assigneeFilter,
  onAssigneeChange,
  onCreate,
  onCreateProject,
  canCreateTicket,
  projects,
  selectedProjectId,
  onProjectChange,
  canWrite,
  canManageMembers,
  onManageMembers,
  canManageProject,
  operationsOpen,
  onToggleOperations,
  projectsOpen,
  projectsBusy,
  onToggleProjects,
}: HeaderProps) {
  const selectedProject = projects.find(
    (project) => project.id === selectedProjectId,
  );
  return (
    <header className={styles.container}>
      <div className={styles.topRow}>
        <div className={styles.leftSection}>
          <h1 className={styles.title}>チケットボード</h1>

          <select
            aria-label="プロジェクト"
            className={styles.selectFilter}
            value={selectedProjectId}
            onChange={(event) => onProjectChange(event.target.value)}
            disabled={projects.length === 0 || projectsBusy}
          >
            {projects.length === 0 ? (
              <option value="ALL">利用可能なプロジェクトがありません</option>
            ) : (
              <>
                <option value="ALL">全プロジェクト</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </>
            )}
          </select>
        </div>

        <div className={styles.rightSection}>
          <button
            type="button"
            onClick={onCreateProject}
            disabled={projectsBusy}
          >
            + プロジェクト作成
          </button>
          <button
            type="button"
            disabled={projectsBusy}
            aria-label="プロジェクト一覧・作成"
            aria-expanded={projectsOpen}
            aria-controls="project-directory-dialog"
            aria-haspopup="dialog"
            onClick={onToggleProjects}
          >
            一覧・作成
          </button>
          {selectedProject && canManageProject && (
            <button
              type="button"
              disabled={projectsBusy}
              aria-label="プロジェクト設定"
              aria-expanded={operationsOpen}
              aria-controls="project-operations"
              onClick={onToggleOperations}
            >
              設定
            </button>
          )}
          {selectedProject && canManageMembers && (
            <button
              type="button"
              disabled={projectsBusy}
              aria-label="メンバー管理"
              onClick={onManageMembers}
            >
              メンバー
            </button>
          )}
          {canCreateTicket && (
            <button
              type="button"
              className={styles.createBtn}
              disabled={projectsBusy}
              aria-label="+ チケット作成"
              onClick={onCreate}
            >
              + チケット作成
            </button>
          )}
        </div>
      </div>
      <div className={styles.bottomRow}>
        {!selectedProject &&
          projects.length > 0 &&
          selectedProjectId === 'ALL' && (
            <p className={styles.projectContext}>
              <strong>全プロジェクト</strong>
              <span>{projects.length}件</span>
              <span>編集・移動はプロジェクトを選択</span>
            </p>
          )}
        {selectedProject && (
          <p className={styles.projectContext}>
            <strong>{selectedProject.name}</strong>
            {selectedProject.projectKey && (
              <span>{selectedProject.projectKey}</span>
            )}
            <span>
              {selectedProject.archivedAt ? '終了済み・閲覧のみ' : '稼働中'}
            </span>
            <span>
              {canManageMembers
                ? 'メンバー管理可'
                : canWrite
                  ? '編集可'
                  : '閲覧のみ'}
            </span>
          </p>
        )}

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
    </header>
  );
}
