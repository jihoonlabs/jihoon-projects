import { fetchWithCsrf } from '@/shared/api/fetchWithCsrf';
import type {
  Project,
  ProjectMember,
  ProjectPermission,
  ProjectRole,
} from '../types/project';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface ProjectResponse {
  id: string | number;
  name: string;
  project_key: string | null;
  board_version: number;
  color?: string;
  archived_at?: string | null;
}

interface ProjectMemberResponse {
  id: string | number;
  name: string;
  email: string | null;
  role: ProjectRole;
  permission: ProjectPermission;
}

export class ProjectApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

async function readData<T>(response: Response): Promise<T> {
  if (!response.ok)
    throw new ProjectApiError(
      response.status === 403
        ? '操作権限がありません (403)。'
        : response.status === 422
          ? '入力内容を確認してください (422)。'
          : `プロジェクト操作に失敗しました (${response.status})`,
      response.status,
    );
  if (response.status === 204) return undefined as T;
  const result = await response.json();
  if (!result || typeof result !== 'object' || !('data' in result)) {
    throw new Error('プロジェクトAPIの応答形式が不正です。');
  }
  return result.data as T;
}

function toProject({
  id,
  name,
  project_key,
  color,
  board_version,
  archived_at,
}: ProjectResponse): Project {
  return {
    id: String(id),
    name,
    projectKey: project_key,
    ...(color !== undefined ? { color } : {}),
    boardVersion: board_version,
    ...(archived_at !== undefined ? { archivedAt: archived_at } : {}),
  };
}

export async function createProject(name: string): Promise<Project> {
  const data = await readData<ProjectResponse>(
    await fetchWithCsrf('/api/projects', {
      method: 'POST',
      body: JSON.stringify({ name: name.trim() }),
    }),
  );
  if (
    !data ||
    typeof data !== 'object' ||
    !('id' in data) ||
    typeof data.name !== 'string'
  ) {
    throw new Error('プロジェクト作成の応答形式が不正です。');
  }
  return toProject(data);
}

export async function fetchProjects(options?: {
  archived?: boolean;
}): Promise<Project[]> {
  const data = await readData<ProjectResponse[]>(
    await fetch(
      `${API_URL}/api/projects${options?.archived ? '?archived=1' : ''}`,
      {
        credentials: 'include',
        headers: { Accept: 'application/json' },
      },
    ),
  );
  if (!Array.isArray(data))
    throw new Error('プロジェクト一覧の応答形式が不正です。');
  return data.map(toProject);
}

export async function fetchProjectMembers(
  projectId: string,
): Promise<ProjectMember[]> {
  const data = await readData<ProjectMemberResponse[]>(
    await fetch(
      `${API_URL}/api/projects/${encodeURIComponent(projectId)}/members`,
      { credentials: 'include', headers: { Accept: 'application/json' } },
    ),
  );
  if (!Array.isArray(data))
    throw new Error('メンバー一覧の応答形式が不正です。');
  return data.map((member) => ({ ...member, id: String(member.id) }));
}

export async function addProjectMember(
  projectId: string,
  input: Pick<ProjectMember, 'email' | 'role' | 'permission'>,
): Promise<ProjectMember> {
  const data = await readData<ProjectMemberResponse>(
    await fetchWithCsrf(
      `/api/projects/${encodeURIComponent(projectId)}/members`,
      { method: 'POST', body: JSON.stringify(input) },
    ),
  );
  return { ...data, id: String(data.id) };
}

export async function updateProjectMember(
  projectId: string,
  memberId: string,
  input: Pick<ProjectMember, 'role' | 'permission'>,
): Promise<ProjectMember> {
  const data = await readData<ProjectMemberResponse>(
    await fetchWithCsrf(
      `/api/projects/${encodeURIComponent(projectId)}/members/${encodeURIComponent(memberId)}`,
      { method: 'PATCH', body: JSON.stringify(input) },
    ),
  );
  return { ...data, id: String(data.id) };
}

export async function removeProjectMember(
  projectId: string,
  memberId: string,
): Promise<void> {
  await readData(
    await fetchWithCsrf(
      `/api/projects/${encodeURIComponent(projectId)}/members/${encodeURIComponent(memberId)}`,
      { method: 'DELETE' },
    ),
  );
}

export async function renameProject(
  projectId: string,
  name: string,
): Promise<Project> {
  return toProject(
    await readData<ProjectResponse>(
      await fetchWithCsrf(`/api/projects/${encodeURIComponent(projectId)}`, {
        method: 'PATCH',
        body: JSON.stringify({ name: name.trim() }),
      }),
    ),
  );
}

export async function archiveProject(projectId: string): Promise<Project> {
  try {
    return toProject(
      await readData<ProjectResponse>(
        await fetchWithCsrf(
          `/api/projects/${encodeURIComponent(projectId)}/archive`,
          { method: 'POST' },
        ),
      ),
    );
  } catch (reason) {
    if (reason instanceof ProjectApiError && reason.status === 409) {
      throw new ProjectApiError(
        '未完了のチケットがあります。すべて完了してからプロジェクトを終了してください (409)。',
        409,
      );
    }
    throw reason;
  }
}

export async function restoreProject(projectId: string): Promise<Project> {
  return toProject(
    await readData<ProjectResponse>(
      await fetchWithCsrf(
        `/api/projects/${encodeURIComponent(projectId)}/restore`,
        { method: 'POST' },
      ),
    ),
  );
}

export async function transferProjectLeader(
  projectId: string,
  memberId: string,
): Promise<ProjectMember> {
  const data = await readData<ProjectMemberResponse>(
    await fetchWithCsrf(
      `/api/projects/${encodeURIComponent(projectId)}/members/${encodeURIComponent(memberId)}/transfer-leader`,
      { method: 'POST' },
    ),
  );
  return { ...data, id: String(data.id) };
}
