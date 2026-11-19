import { computed, onBeforeUnmount, ref, watch, type Ref } from 'vue';

import { useAuthStore } from '~/features/auth/store/useAuthStore';
import { isAbortError } from '~/shared/api/isAbortError';

import { useProjectApi } from '../api/projectApi';
import type { ProjectMember } from '../types/project';
import { ALL_PROJECTS } from '../utils/filterTickets';
import { resolveCurrentMembership } from '../utils/projectPermissions';

const MEMBER_ERROR = 'メンバーを取得できませんでした。';

/**
 * 選択中のプロジェクトのメンバーを取得する（権限の判定に使う）。
 * 全体表示では取得しない。プロジェクトを切り替えたら、前のメンバーは捨てる。
 */
export function useProjectMembers(selectedProjectId: Ref<string>) {
  const api = useProjectApi();
  const auth = useAuthStore();

  const members = ref<ProjectMember[]>([]);
  const membersProjectId = ref('');
  const membersSession = ref(-1);
  const error = ref<string | null>(null);

  let controller: AbortController | null = null;
  let sequence = 0;

  async function load(): Promise<void> {
    controller?.abort();
    const mine = ++sequence;
    members.value = [];
    membersProjectId.value = '';
    membersSession.value = -1;
    error.value = null;

    const projectId = selectedProjectId.value;

    if (!auth.isAuthenticated || projectId === ALL_PROJECTS) {
      return;
    }

    const current = new AbortController();
    controller = current;

    try {
      const items = await api.fetchProjectMembers(projectId, current.signal);

      if (mine === sequence) {
        members.value = items;
        membersProjectId.value = projectId;
        membersSession.value = auth.sessionRevision;
      }
    } catch (failure) {
      if (mine === sequence && !isAbortError(failure)) {
        error.value = failure instanceof Error ? failure.message : MEMBER_ERROR;
      }
    }
  }

  watch([selectedProjectId, () => auth.sessionRevision], () => void load(), {
    immediate: true,
  });
  onBeforeUnmount(() => {
    controller?.abort();
    sequence += 1;
  });

  /** 選択中プロジェクトで、ログイン中の利用者自身のメンバー情報（取得できていなければ undefined） */
  const currentMembership = computed(() =>
    resolveCurrentMembership({
      members: members.value,
      membersProjectId: membersProjectId.value,
      selectedProjectId: selectedProjectId.value,
      membersSession: membersSession.value,
      sessionRevision: auth.sessionRevision,
      userId: auth.user?.id ?? null,
    }),
  );

  return {
    members,
    membersProjectId,
    currentMembership,
    error,
    retry: load,
  };
}
