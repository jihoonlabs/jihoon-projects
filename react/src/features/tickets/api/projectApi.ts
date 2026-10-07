import { fetchWithCsrf } from '@/shared/api/fetchWithCsrf';
import type { Project, ProjectMember, ProjectPermission, ProjectRole } from '../types/project';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface ProjectResponse {
  id: string | number;
  name: string;
  project_key: string;
  board_version: number;
}

interface ProjectMemberResponse {
  id: string | number;
  name: string;
  email: string | null;
  role: ProjectRole;
  permission: ProjectPermission;
}

async function readData<T>(response: Response): Promise<T> {
  if (!response.ok) throw new Error(`プロジェクト操作に失敗しました (${response.status})`);
  if (response.status === 204) return undefined as T;
  const result = await response.json();
  if (!result || typeof result !== 'object' || !('data' in result)) {
    throw new Error('プロジェクトAPIの応答形式が不正です。');
  }
  return result.data as T;
}

export async function fetchProjects(): Promise<Project[]> {
  const data = await readData<ProjectResponse[]>(await fetch(`${API_URL}/api/projects`, {
    credentials: 'include',
    headers: { Accept: 'application/json' },
  }));
  if (!Array.isArray(data)) throw new Error('プロジェクト一覧の応答形式が不正です。');
  return data.map(({ id, name, project_key, board_version }) => ({
    id: String(id),
    name,
    projectKey: project_key,
    boardVersion: board_version,
  }));
}

export async function fetchProjectMembers(projectId: string): Promise<ProjectMember[]> {
  const data = await readData<ProjectMemberResponse[]>(await fetch(
    `${API_URL}/api/projects/${encodeURIComponent(projectId)}/members`,
    { credentials: 'include', headers: { Accept: 'application/json' } },
  ));
  if (!Array.isArray(data)) throw new Error('メンバー一覧の応答形式が不正です。');
  return data.map((member) => ({ ...member, id: String(member.id) }));
}

export async function addProjectMember(
  projectId: string,
  input: Pick<ProjectMember, 'email' | 'role' | 'permission'>,
): Promise<ProjectMember> {
  const data = await readData<ProjectMemberResponse>(await fetchWithCsrf(
    `/api/projects/${encodeURIComponent(projectId)}/members`,
    { method: 'POST', body: JSON.stringify(input) },
  ));
  return { ...data, id: String(data.id) };
}

export async function updateProjectMember(
  projectId: string,
  memberId: string,
  input: Pick<ProjectMember, 'role' | 'permission'>,
): Promise<ProjectMember> {
  const data = await readData<ProjectMemberResponse>(await fetchWithCsrf(
    `/api/projects/${encodeURIComponent(projectId)}/members/${encodeURIComponent(memberId)}`,
    { method: 'PATCH', body: JSON.stringify(input) },
  ));
  return { ...data, id: String(data.id) };
}

export async function removeProjectMember(projectId: string, memberId: string): Promise<void> {
  await readData(await fetchWithCsrf(
    `/api/projects/${encodeURIComponent(projectId)}/members/${encodeURIComponent(memberId)}`,
    { method: 'DELETE' },
  ));
}
