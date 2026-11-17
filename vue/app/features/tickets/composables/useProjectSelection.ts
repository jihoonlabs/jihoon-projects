import { onBeforeUnmount, onMounted, ref, watch } from 'vue';

import { useAuthStore } from '~/features/auth/store/useAuthStore';
import { isAbortError } from '~/shared/api/isAbortError';

import { useProjectApi } from '../api/projectApi';
import type { Project } from '../types/project';
import { ALL_PROJECTS } from '../utils/filterTickets';
import { resolveInitialProjectId } from '../utils/resolveProjectSelection';

const PROJECT_ERROR = 'プロジェクトを取得できませんでした。';

/**
 * プロジェクト一覧の取得と、選択中のプロジェクトを URL（?project=）と同期する。
 * - 最初の一覧が届いたときだけ、URL（またはデモモードの先頭）から選択を復元する。
 * - 選択中のプロジェクトが一覧から消えたら、全体表示へ戻す。
 * - 新しい取得を始めたら前の取得を中断し、遅れて届いた古い応答は使わない。
 */
export function useProjectSelection() {
  const api = useProjectApi();
  const auth = useAuthStore();
  const route = useRoute();
  const router = useRouter();
  const demoMode = useRuntimeConfig().public.demoMode === true;

  const projects = ref<Project[]>([]);
  const selectedProjectId = ref(ALL_PROJECTS);
  const loading = ref(true);
  const error = ref<string | null>(null);

  let restored = false;
  let controller: AbortController | null = null;
  let sequence = 0;

  const writeQuery = (projectId: string) => {
    const query = { ...route.query };

    if (projectId === ALL_PROJECTS) {
      delete query.project;
    } else {
      query.project = projectId;
    }

    return router.replace({ query });
  };

  async function select(projectId: string): Promise<void> {
    selectedProjectId.value = projectId;
    await writeQuery(projectId);
  }

  async function load(): Promise<void> {
    if (!auth.isAuthenticated) {
      return;
    }

    controller?.abort();
    const current = new AbortController();
    controller = current;
    const mine = ++sequence;
    loading.value = true;

    try {
      const items = await api.fetchProjects({}, current.signal);

      if (mine !== sequence) {
        return;
      }

      projects.value = items;
      error.value = null;

      if (!restored) {
        restored = true;
        const requested = route.query.project;
        await select(
          resolveInitialProjectId(
            items,
            typeof requested === 'string' ? requested : null,
            demoMode,
          ),
        );
      } else if (
        selectedProjectId.value !== ALL_PROJECTS &&
        !items.some((project) => project.id === selectedProjectId.value)
      ) {
        await select(ALL_PROJECTS);
      }
    } catch (failure) {
      if (mine === sequence && !isAbortError(failure)) {
        error.value =
          failure instanceof Error ? failure.message : PROJECT_ERROR;
      }
    } finally {
      if (mine === sequence) {
        loading.value = false;
      }
    }
  }

  onMounted(load);
  onBeforeUnmount(() => {
    controller?.abort();
    sequence += 1;
  });
  watch(
    () => auth.sessionRevision,
    () => {
      void load();
    },
  );

  return { projects, selectedProjectId, loading, error, select, retry: load };
}
