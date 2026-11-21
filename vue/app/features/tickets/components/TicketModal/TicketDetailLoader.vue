<script setup lang="ts">
import { toRef } from 'vue';

import { useTicketDetail } from '../../composables/useTicketDetail';
import type { Ticket } from '../../types/ticket';
import TicketModalShell from './TicketModalShell.vue';

const props = defineProps<{ ticketId: string }>();

defineEmits<{ close: [] }>();
defineSlots<{ default(props: { ticket: Ticket }): unknown }>();

const { ticket, error, retry } = useTicketDetail(toRef(props, 'ticketId'));
</script>

<template>
  <slot v-if="ticket" :ticket="ticket" />
  <!-- カードの古い内容は見せず、最新の取得が済むまで案内だけを出す -->
  <TicketModalShell
    v-else
    heading="チケット情報"
    focus-heading
    :project-color="null"
    :locked="false"
    @close="$emit('close')"
  >
    <p v-if="error" :class="$style.error" role="alert">{{ error }}</p>
    <p v-else role="status">最新情報を取得中...</p>
    <div :class="$style.actions">
      <button type="button" @click="$emit('close')">閉じる</button>
      <button v-if="error" type="button" @click="retry()">再試行</button>
    </div>
  </TicketModalShell>
</template>

<style module lang="scss">
.error {
  color: #b91c1c;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1.25rem;
}
</style>
