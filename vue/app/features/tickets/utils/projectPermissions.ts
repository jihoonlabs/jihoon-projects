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

/**
 * メンバーの管理（追加・権限変更・リーダー引き継ぎ）は、アーカイブ済みでない場合だけ行える
 */
export function canManageMembers(context: PermissionContext): boolean {
  return canManageProject(context) && context.project?.archivedAt === null;
}

/**
 * 応答が現在のセッションと選択中のプロジェクトのものである場合だけ、自分のメンバー情報を返す。
 * 古いセッションや別プロジェクトのメンバーで権限を判定しないための関門。
 */
export function resolveCurrentMembership(input: {
  members: ProjectMember[];
  membersProjectId: string;
  selectedProjectId: string;
  membersSession: number;
  sessionRevision: number;
  userId: number | null;
}): ProjectMember | undefined {
  if (
    input.userId === null ||
    input.membersSession !== input.sessionRevision ||
    input.membersProjectId !== input.selectedProjectId
  ) {
    return undefined;
  }

  return input.members.find((member) => member.id === String(input.userId));
}
