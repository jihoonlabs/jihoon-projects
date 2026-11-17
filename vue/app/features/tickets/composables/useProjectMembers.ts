import { onBeforeUnmount, ref, watch, type Ref } from 'vue';

import { useAuthStore } from '~/features/auth/store/useAuthStore';
import { isAbortError } from '~/shared/api/isAbortError';

import { useProjectApi } from '../api/projectApi';
import type { ProjectMember } from '../types/project';
import { ALL_PROJECTS } from '../utils/filterTickets';

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
  const error = ref<string | null>(null);

  let controller: AbortController | null = null;
  let sequence = 0;

  async function load(): Promise<void> {
    controller?.abort();
    const mine = ++sequence;
    members.value = [];
    membersProjectId.value = '';
    error.value = null;

    const projectId = selectedProjectId.value;

    if (auth.sessionExpired || projectId === ALL_PROJECTS) {
      return;
    }

    const current = new AbortController();
    controller = current;

    try {
      const items = await api.fetchProjectMembers(projectId, current.signal);

      if (mine === sequence) {
        members.value = items;
        membersProjectId.value = projectId;
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

  return { members, membersProjectId, error, retry: load };
}
