<script setup lang="ts">
import { useAuthStore } from '~/features/auth/store/useAuthStore';
import type { Ticket } from '../../types/ticket';

import { useProjectMembers } from '../../composables/useProjectMembers';
import { useProjectSelection } from '../../composables/useProjectSelection';
import { useTicketFilters } from '../../composables/useTicketFilters';
import { useTicketStore } from '../../store/useTicketStore';
import { groupByColumn } from '../../utils/boardColumns';
import { filterTickets, ticketsInScope } from '../../utils/filterTickets';
import BoardColumn from '../BoardColumn/BoardColumn.vue';
import BoardHeader from '../BoardHeader/BoardHeader.vue';
import BoardNotices from '../BoardNotices/BoardNotices.vue';
import TicketModal from '../TicketModal/TicketModal.vue';

const auth = useAuthStore();
const store = useTicketStore();
const { projects, selectedProjectId, loading, error, select, retry } =
  useProjectSelection();
const members = useProjectMembers(selectedProjectId);
const { searchQuery, assigneeFilter, reset } = useTicketFilters();
const openedTicket = ref<Ticket | null>(null);

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

const openedProjectColor = computed(() =>
  openedTicket.value
    ? (projectColors.value[openedTicket.value.projectId] ?? null)
    : null,
);

async function selectProject(projectId: string) {
  reset();
  await select(projectId);
}
</script>

<template>
  <section :class="$style.page" aria-label="チケットボード">
    <BoardHeader
      v-model:search-query="searchQuery"
      v-model:assignee-filter="assigneeFilter"
      :projects="projects"
      :selected-project-id="selectedProjectId"
      @select="selectProject"
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
      v-if="openedTicket"
      :ticket="openedTicket"
      :project-color="openedProjectColor"
      @close="openedTicket = null"
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
