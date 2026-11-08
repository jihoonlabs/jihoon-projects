<script setup lang="ts">
import { onMounted } from 'vue';

import HistoryTable from '~/features/attendance/components/HistoryTable.vue';
import TodayPanel from '~/features/attendance/components/TodayPanel.vue';
import { useAttendance } from '~/features/attendance/composables/useAttendance';

definePageMeta({ layout: 'dashboard', middleware: 'auth' });

const demoMode = useRuntimeConfig().public.demoMode === true;
const attendance = useAttendance();
const {
  today,
  history,
  page,
  loading,
  submitting,
  error,
  actionsDisabled,
  changePage,
  clock,
} = attendance;

onMounted(() => {
  void attendance.start();
});
</script>

<template>
  <div :class="$style.page">
    <h1>勤怠管理</h1>
    <p v-if="demoMode" :class="$style.demoNote">
      「出勤」を押してから「退勤」を押すだけで試せます。共通デモのため記録は他の閲覧者にも表示されます。
    </p>

    <TodayPanel :today="today" :disabled="actionsDisabled" @clock="clock" />

    <p v-if="error" :class="$style.error" role="alert">{{ error }}</p>

    <HistoryTable
      :history="history"
      :page="page"
      :disabled="loading || submitting"
      @change-page="changePage"
    />
  </div>
</template>

<style module lang="scss">
.page {
  max-width: 960px;
  margin: 0 auto;
  padding-bottom: 3rem;
  color: #111827;

  h1 {
    margin-bottom: 1rem;
    font-size: 1.5rem;
  }
}

.demoNote {
  margin-bottom: 1rem;
  padding: 0.85rem 1rem;
  border: 1px solid #bfdbfe;
  border-radius: 0.75rem;
  background: #eff6ff;
  color: #1e3a5f;
  line-height: 1.55;
}

.error {
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  background: #fef2f2;
  color: #b91c1c;
}
</style>
