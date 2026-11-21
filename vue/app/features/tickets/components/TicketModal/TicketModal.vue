<script setup lang="ts">
import type { ProjectMember } from '../../types/project';
import type { Ticket } from '../../types/ticket';
import type { ProjectChoice } from '../../types/ticketModal';
import TicketDetailLoader from './TicketDetailLoader.vue';
import TicketModalContent from './TicketModalContent.vue';

defineProps<{
  /** 開いたカードのチケット（作成なら null）。表示前に最新の内容を取得し直す */
  ticket: Ticket | null;
  projectId: string;
  projectColor: string | null;
  projectMembers: ProjectMember[];
  projectChoice: ProjectChoice | null;
  readOnly: boolean;
}>();

defineEmits<{
  close: [];
  changeProject: [projectId: string];
  retryMembers: [];
}>();
</script>

<template>
  <TicketModalContent
    v-if="!ticket"
    :ticket="null"
    :project-id="projectId"
    :project-color="projectColor"
    :project-members="projectMembers"
    :project-choice="projectChoice"
    :read-only="readOnly"
    @close="$emit('close')"
    @change-project="$emit('changeProject', $event)"
    @retry-members="$emit('retryMembers')"
  />
  <TicketDetailLoader
    v-else
    :key="ticket.id"
    :ticket-id="ticket.id"
    @close="$emit('close')"
  >
    <template #default="{ ticket: loaded }">
      <TicketModalContent
        :key="loaded.id"
        :ticket="loaded"
        :project-id="projectId"
        :project-color="projectColor"
        :project-members="projectMembers"
        :project-choice="null"
        :read-only="readOnly"
        @close="$emit('close')"
      />
    </template>
  </TicketDetailLoader>
</template>
