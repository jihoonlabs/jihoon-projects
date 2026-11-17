export type ProjectRole = 'leader' | 'member';
export type ProjectPermission = 'read' | 'write';

/**
 * 画面で扱うプロジェクト
 */
export interface Project {
  id: string;
  name: string;
  projectKey: string | null;
  color: string | null;
  boardVersion: number;
  archivedAt: string | null;
}

export interface ProjectMember {
  id: string;
  name: string;
  email: string | null;
  role: ProjectRole;
  permission: ProjectPermission;
}

/**
 * Laravel の ProjectResource が返すプロジェクト（snake_case）。
 * 古い応答では color と archived_at がないことがあるため省略可能にする。
 */
export interface ProjectResponse {
  id: string | number;
  name: string;
  project_key: string | null;
  board_version: number;
  color?: string | null;
  archived_at?: string | null;
}

/**
 * Laravel の ProjectMemberResource が返すメンバー
 */
export interface ProjectMemberResponse {
  id: string | number;
  name: string;
  email: string | null;
  role: ProjectRole;
  permission: ProjectPermission;
}
