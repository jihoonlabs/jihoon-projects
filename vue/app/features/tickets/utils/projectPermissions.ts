import type { Project, ProjectMember } from '../types/project';

interface PermissionContext {
  project: Project | null;
  membership: ProjectMember | undefined;
  isAdmin: boolean;
  sessionActive: boolean;
}

/**
 * 管理者、またはプロジェクトのリーダーだけが運用できる
 */
export function canManageProject(context: PermissionContext): boolean {
  return (
    context.sessionActive &&
    context.project !== null &&
    (context.isAdmin || context.membership?.role === 'leader')
  );
}

/**
 * アーカイブ済みでないプロジェクトで、管理者または書き込み権限のある人だけが編集できる
 */
export function canWriteProject(context: PermissionContext): boolean {
  return (
    context.sessionActive &&
    context.project !== null &&
    context.project.archivedAt === null &&
    (context.isAdmin || context.membership?.permission === 'write')
  );
}
