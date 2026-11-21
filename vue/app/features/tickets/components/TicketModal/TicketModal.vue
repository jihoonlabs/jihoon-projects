<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';

import type { Ticket } from '../../types/ticket';
import { getProjectBorderColor } from '../../utils/projectColor';
import {
  PRIORITY_LABELS,
  STATUS_LABELS,
  assigneeLabel,
} from '../../utils/ticketLabels';

const props = defineProps<{
  ticket: Ticket;
  projectColor: string | null;
}>();

const emit = defineEmits<{ close: [] }>();

const heading = ref<HTMLHeadingElement | null>(null);
const borderColor = getProjectBorderColor(props.projectColor);

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') emit('close');
}

onMounted(() => {
  heading.value?.focus();
  document.addEventListener('keydown', onKeydown);
});
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown));
</script>

<template>
  <div
    :class="$style.backdrop"
    role="presentation"
    @mousedown.self="emit('close')"
  >
    <section
      :class="$style.modal"
      :style="borderColor ? { '--project-color': borderColor } : undefined"
      role="dialog"
      aria-modal="true"
      aria-labelledby="ticket-modal-title"
    >
      <header :class="$style.header">
        <span v-if="ticket.issueKey" :class="$style.key">{{
          ticket.issueKey
        }}</span>
        <h2
          id="ticket-modal-title"
          ref="heading"
          tabindex="-1"
          :class="$style.title"
        >
          チケット詳細
        </h2>
      </header>

      <dl :class="$style.details">
        <div>
          <dt>タイトル</dt>
          <dd>{{ ticket.title }}</dd>
        </div>
        <div>
          <dt>状態</dt>
          <dd>{{ STATUS_LABELS[ticket.status] }}</dd>
        </div>
        <div>
          <dt>優先度</dt>
          <dd>{{ PRIORITY_LABELS[ticket.priority] }}</dd>
        </div>
        <div>
          <dt>担当者</dt>
          <dd>{{ assigneeLabel(ticket) }}</dd>
        </div>
        <div>
          <dt>説明</dt>
          <dd :class="$style.description">{{ ticket.description || '—' }}</dd>
        </div>
      </dl>

      <div :class="$style.actions">
        <button type="button" @click="emit('close')">閉じる</button>
      </div>
    </section>
  </div>
</template>

<style module lang="scss">
.backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(17, 24, 39, 0.4);
}

.modal {
  width: min(36rem, 100%);
  max-height: 90vh;
  overflow-y: auto;
  padding: 1.25rem;
  border-top: 4px solid var(--project-color, #d1d5db);
  border-radius: 0.75rem;
  background: #fff;
  color: #111827;
}

.header {
  margin-bottom: 1rem;
}

.key {
  color: #6b7280;
  font-size: 0.75rem;
}

.title {
  margin: 0.25rem 0 0;
  font-size: 1.25rem;
  font-weight: 700;
  outline: none;
}

.details {
  display: grid;
  gap: 0.75rem;
  margin: 0;

  dt {
    color: #6b7280;
    font-size: 0.75rem;
  }

  dd {
    margin: 0.125rem 0 0;
    overflow-wrap: anywhere;
  }
}

.description {
  white-space: pre-wrap;
}

.actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 1.25rem;
}
</style>
