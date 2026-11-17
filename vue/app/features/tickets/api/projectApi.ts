import { useProtectedApi } from '~/features/auth/api/protectedRequest';
import { ApiError } from '~/shared/api/apiClient';

import type {
  Project,
  ProjectMember,
  ProjectMemberResponse,
  ProjectResponse,
} from '../types/project';
import {
  PROJECT_ERROR_MESSAGE,
  ProjectApiError,
  translateFailure,
} from './apiErrors';
import { toProject, toProjectMember } from './projectMapper';

const toProjectError = (error: unknown): Error => {
  if (error instanceof ApiError) {
    return new ProjectApiError(
      error.status === 403
        ? '操作権限がありません (403)。'
        : `${PROJECT_ERROR_MESSAGE} (${error.status})`,
      error.status,
    );
  }

  return new ProjectApiError(PROJECT_ERROR_MESSAGE);
};

export function useProjectApi() {
  const api = useProtectedApi();

  return {
    /**
     * アクセスできるプロジェクトを取得する（archived: true でアーカイブ済み）
     */
    async fetchProjects(
      options: { archived?: boolean } = {},
      signal?: AbortSignal,
    ): Promise<Project[]> {
      const body = await translateFailure(
        api.getJson<{ data?: ProjectResponse[] | null }>(
          `/api/projects${options.archived ? '?archived=1' : ''}`,
          { signal },
        ),
        toProjectError,
      );

      if (!body || !Array.isArray(body.data)) {
        throw new ProjectApiError('プロジェクト一覧の応答形式が不正です。');
      }

      return body.data.map(toProject);
    },

    async fetchProjectMembers(
      projectId: string,
      signal?: AbortSignal,
    ): Promise<ProjectMember[]> {
      const body = await translateFailure(
        api.getJson<{ data?: ProjectMemberResponse[] | null }>(
          `/api/projects/${encodeURIComponent(projectId)}/members`,
          { signal },
        ),
        toProjectError,
      );

      if (!body || !Array.isArray(body.data)) {
        throw new ProjectApiError('メンバー一覧の応答形式が不正です。');
      }

      return body.data.map(toProjectMember);
    },
  };
}
