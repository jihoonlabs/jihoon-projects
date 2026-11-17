<script setup lang="ts">
import type { Ticket } from '../../types/ticket';
import { getProjectBorderColor } from '../../utils/projectColor';

const props = defineProps<{
  ticket: Ticket;
  projectColor: string | null;
}>();

const PRIORITY_LABELS: Record<Ticket['priority'], string> = {
  HIGHEST: '最高',
  HIGH: '高',
  MEDIUM: '中',
  LOW: '低',
  LOWEST: '最低',
};

// 色は #RRGGBB だけを使い、それ以外は中立の見た目にする
const borderColor = computed(() => getProjectBorderColor(props.projectColor));
</script>

<template>
  <article
    :class="$style.card"
    :style="borderColor ? { '--project-color': borderColor } : undefined"
  >
    <p v-if="ticket.issueKey" :class="$style.key">{{ ticket.issueKey }}</p>
    <p :class="$style.title">{{ ticket.title }}</p>
    <div :class="$style.meta">
      <span :class="$style.priority">
        優先度: {{ PRIORITY_LABELS[ticket.priority] }}
      </span>
      <span v-if="ticket.assignee" :class="$style.assignee">
        {{ ticket.assignee.name }}
      </span>
      <span v-else :class="$style.assignee">未割り当て</span>
    </div>
  </article>
</template>

<style module lang="scss">
.card {
  padding: 0.75rem;
  border: 1px solid #e5e7eb;
  border-left: 4px solid var(--project-color, #d1d5db);
  border-radius: 0.5rem;
  background: #fff;
  color: #111827;
}

.key {
  margin-bottom: 0.25rem;
  color: #6b7280;
  font-size: 0.75rem;
}

.title {
  margin-bottom: 0.5rem;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.meta {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  color: #4b5563;
  font-size: 0.75rem;
}
</style>
