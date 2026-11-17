<script setup lang="ts">
import type { Ticket } from '../../types/ticket';
import TicketCard from '../TicketCard/TicketCard.vue';

defineProps<{
  label: string;
  tickets: Ticket[];
  projectColors: Record<string, string | null>;
}>();
</script>

<template>
  <section :class="$style.column" :aria-label="label">
    <div :class="$style.header">
      <span>{{ label }}</span>
      <span :class="$style.count">{{ tickets.length }}</span>
    </div>
    <div :class="$style.list">
      <TicketCard
        v-for="ticket in tickets"
        :key="ticket.id"
        :ticket="ticket"
        :project-color="projectColors[ticket.projectId] ?? null"
      />
    </div>
  </section>
</template>

<style module lang="scss">
.column {
  flex: 1 1 0;
  min-width: 14rem;
  padding: 0.75rem;
  border-radius: 0.75rem;
  background: #f3f4f6;
}

.header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  color: #374151;
  font-weight: 700;
}

.count {
  color: #6b7280;
  font-weight: 500;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
</style>
