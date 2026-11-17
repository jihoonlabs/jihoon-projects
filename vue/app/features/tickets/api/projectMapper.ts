import type {
  Project,
  ProjectMember,
  ProjectMemberResponse,
  ProjectResponse,
} from '../types/project';

/**
 * Laravel のプロジェクト応答を画面用の形に変換する（ID は文字列にそろえる）
 */
export function toProject(data: ProjectResponse): Project {
  return {
    id: String(data.id),
    name: data.name,
    projectKey: data.project_key,
    color: data.color ?? null,
    boardVersion: data.board_version,
    archivedAt: data.archived_at ?? null,
  };
}

/**
 * Laravel のメンバー応答を画面用の形に変換する（ID は文字列にそろえる）
 */
export function toProjectMember(data: ProjectMemberResponse): ProjectMember {
  return {
    id: String(data.id),
    name: data.name,
    email: data.email,
    role: data.role,
    permission: data.permission,
  };
}
