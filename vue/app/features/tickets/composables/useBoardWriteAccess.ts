import { computed, type ComputedRef, type Ref } from 'vue';

import { useAuthStore } from '~/features/auth/store/useAuthStore';

import type { Project, ProjectMember } from '../types/project';
import type { ProjectChoice } from '../types/ticketModal';
import { ALL_PROJECTS } from '../utils/filterTickets';
import { canWriteProject } from '../utils/projectPermissions';

interface Input {
  projects: Ref<Project[]>;
  projectsLoading: Ref<boolean>;
  selectedProject: ComputedRef<Project | null>;
  selectedProjectId: Ref<string>;
  members: Ref<ProjectMember[]>;
  membersProjectId: Ref<string>;
  membersError: Ref<string | null>;
  currentMembership: ComputedRef<ProjectMember | undefined>;
}

/**
 * ボードで書き込み（作成・編集・削除）できるかと、作成モーダルに渡す情報。
 * 権限は、現在のセッションで取得できたメンバー情報だけで判定する。
 */
export function useBoardWriteAccess(input: Input) {
  const auth = useAuthStore();

  const canWrite = computed(() =>
    canWriteProject({
      project: input.selectedProject.value,
      membership: input.currentMembership.value,
      isAdmin: auth.user?.role === 'admin',
      sessionActive: auth.isAuthenticated,
    }),
  );

  // 全体表示では作成先をモーダルで選ぶため、ボタンは出す
  const canCreateTicket = computed(
    () =>
      !input.projectsLoading.value &&
      input.projects.value.length > 0 &&
      (input.selectedProjectId.value === ALL_PROJECTS || canWrite.value),
  );

  const membersReady = computed(
    () => input.membersProjectId.value === input.selectedProjectId.value,
  );

  /** 別のプロジェクトのメンバーを、担当者の選択肢に出さない */
  const modalMembers = computed(() =>
    membersReady.value ? input.members.value : [],
  );

  const createReadOnly = computed(() => !canWrite.value || !membersReady.value);

  const projectChoice = computed<ProjectChoice>(() => ({
    projects: input.projects.value,
    message:
      input.selectedProjectId.value === ALL_PROJECTS
        ? '作成先のプロジェクトを選択してください。'
        : (input.membersError.value ??
          (!membersReady.value
            ? 'メンバーと権限を確認中...'
            : !canWrite.value
              ? 'このプロジェクトは閲覧のみです。作成できるプロジェクトを選択してください。'
              : null)),
    canRetry: input.membersError.value !== null,
  }));

  return {
    canWrite,
    canCreateTicket,
    modalMembers,
    createReadOnly,
    projectChoice,
  };
}
