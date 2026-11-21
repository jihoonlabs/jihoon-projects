<script setup lang="ts">
import { useAuthStore } from '~/features/auth/store/useAuthStore';
import type { Ticket } from '../../types/ticket';

import { useBoardWriteAccess } from '../../composables/useBoardWriteAccess';
import { useProjectMembers } from '../../composables/useProjectMembers';
import { useProjectSelection } from '../../composables/useProjectSelection';
import { useTicketFilters } from '../../composables/useTicketFilters';
import { useTicketStore } from '../../store/useTicketStore';
import { groupByColumn } from '../../utils/boardColumns';
import { filterTickets, ticketsInScope } from '../../utils/filterTickets';
import BoardColumn from '../BoardColumn/BoardColumn.vue';
import BoardHeader from '../BoardHeader/BoardHeader.vue';
import BoardNotices from '../BoardNotices/BoardNotices.vue';
import DemoGuide from '../DemoGuide/DemoGuide.vue';
import TicketModal from '../TicketModal/TicketModal.vue';

const auth = useAuthStore();
const demoMode = useRuntimeConfig().public.demoMode === true;
const store = useTicketStore();
const { projects, selectedProjectId, loading, error, select, retry } =
  useProjectSelection();
const members = useProjectMembers(selectedProjectId);
const { searchQuery, assigneeFilter, reset } = useTicketFilters();
const openedTicket = ref<Ticket | null>(null);
const creating = ref(false);

// ログイン直後・再ログイン後にチケットを取得し直す
watch(
  () => auth.sessionRevision,
  () => {
    if (auth.isAuthenticated) {
      void store.fetchTickets();
    }
  },
  { immediate: true },
);
onBeforeUnmount(() => store.reset());

const selectedProject = computed(
  () =>
    projects.value.find((project) => project.id === selectedProjectId.value) ??
    null,
);
const access = useBoardWriteAccess({
  projects,
  projectsLoading: loading,
  selectedProject,
  selectedProjectId,
  members: members.members,
  membersProjectId: members.membersProjectId,
  membersError: members.error,
  currentMembership: members.currentMembership,
});
const projectColors = computed(() =>
  Object.fromEntries(
    projects.value.map((project) => [project.id, project.color]),
  ),
);
const columns = computed(() => {
  const scoped = ticketsInScope(
    store.tickets,
    selectedProjectId.value,
    new Set(projects.value.map((project) => project.id)),
  );

  return groupByColumn(
    filterTickets(scoped, {
      searchQuery: searchQuery.value,
      assigneeFilter: assigneeFilter.value,
      currentUserId: auth.user?.id ?? null,
    }),
  );
});

// 詳細は開いたチケットのプロジェクト、作成は選択中のプロジェクトを基準にする
const modalProjectId = computed(
  () => openedTicket.value?.projectId ?? selectedProjectId.value,
);
const modalProjectColor = computed(
  () => projectColors.value[modalProjectId.value] ?? null,
);
// 全体表示で開いた詳細は、権限を判定できる個別プロジェクトがないため閲覧のみ
const modalReadOnly = computed(() =>
  openedTicket.value ? !access.canWrite.value : access.createReadOnly.value,
);

function closeModal() {
  openedTicket.value = null;
  creating.value = false;
}

async function selectProject(projectId: string) {
  reset();
  await select(projectId);
}
</script>

<template>
  <section :class="$style.page" aria-label="チケットボード">
    <DemoGuide v-if="demoMode" />

    <BoardHeader
      v-model:search-query="searchQuery"
      v-model:assignee-filter="assigneeFilter"
      :projects="projects"
      :selected-project-id="selectedProjectId"
      :can-create-ticket="access.canCreateTicket.value"
      @select="selectProject"
      @create="creating = true"
    />

    <BoardNotices
      :loading="store.isLoading"
      :ticket-error="store.error"
      :project-error="error"
      :member-error="members.error.value"
      :no-projects="projects.length === 0 && !loading && !error"
      :archived="Boolean(selectedProject?.archivedAt)"
      @retry-tickets="store.fetchTickets()"
      @retry-members="members.retry()"
      @retry-projects="retry()"
    />

    <div :class="$style.board">
      <BoardColumn
        v-for="column in columns"
        :key="column.id"
        :label="column.label"
        :tickets="column.tickets"
        :project-colors="projectColors"
        @open="openedTicket = $event"
      />
    </div>

    <TicketModal
      v-if="openedTicket || creating"
      :key="openedTicket?.id ?? 'create'"
      :ticket="openedTicket"
      :project-id="modalProjectId"
      :project-color="modalProjectColor"
      :project-members="access.modalMembers.value"
      :project-choice="openedTicket ? null : access.projectChoice.value"
      :read-only="modalReadOnly"
      @close="closeModal"
      @change-project="selectProject"
      @retry-members="members.retry()"
    />
  </section>
</template>

<style module lang="scss">
.page {
  color: #111827;
}

.board {
  display: flex;
  gap: 0.75rem;
  overflow-x: auto;
  padding-bottom: 1rem;
}
</style>
