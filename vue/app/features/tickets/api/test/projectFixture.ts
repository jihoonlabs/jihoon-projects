import type {
  ProjectMemberResponse,
  ProjectResponse,
} from '../../types/project';

/**
 * Laravel の ProjectResource と同じ形のプロジェクト
 */
export function projectFixture(
  overrides: Partial<ProjectResponse> = {},
): ProjectResponse {
  return {
    id: '1',
    name: 'Product',
    project_key: 'PRD',
    board_version: 1,
    color: '#e3f2fd',
    archived_at: null,
    ...overrides,
  };
}

/**
 * Laravel のメンバー応答
 */
export function projectMemberFixture(
  overrides: Partial<ProjectMemberResponse> = {},
): ProjectMemberResponse {
  return {
    id: '7',
    name: 'Aki',
    email: 'aki@example.com',
    role: 'member',
    permission: 'write',
    ...overrides,
  };
}
