<script setup lang="ts">
import type { Ticket } from '../../types/ticket';
import { PRIORITY_LABELS, STATUS_LABELS } from '../../utils/ticketLabels';

defineProps<{
  ticket: Ticket;
  assigneeName: string;
  canEdit: boolean;
  submitting: boolean;
  saveError: string | null;
}>();

defineEmits<{ close: []; edit: []; remove: [] }>();
</script>

<template>
  <div>
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
        <dd>{{ assigneeName }}</dd>
      </div>
      <div>
        <dt>説明</dt>
        <dd :class="$style.description">{{ ticket.description || '—' }}</dd>
      </div>
    </dl>

    <div :class="$style.actions">
      <button type="button" :disabled="submitting" @click="$emit('close')">
        閉じる
      </button>
      <button v-if="canEdit" type="button" @click="$emit('edit')">編集</button>
      <button
        v-if="canEdit"
        type="button"
        :disabled="submitting"
        @click="$emit('remove')"
      >
        削除
      </button>
    </div>
    <p v-if="saveError" :class="$style.error" role="alert">{{ saveError }}</p>
  </div>
</template>

<style module lang="scss">
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
  gap: 0.5rem;
  margin-top: 1.25rem;
}

.error {
  margin: 0.75rem 0 0;
  color: #b91c1c;
}
</style>
