<script setup lang="ts">
import { formatAttendanceTime, formatDuration } from '../../utils/format';
import type { AttendanceHistory } from '../../types/attendance';

defineProps<{
  history: AttendanceHistory | null;
  page: number;
  disabled: boolean;
}>();

const emit = defineEmits<{ 'change-page': [page: number] }>();
</script>

<template>
  <section :class="$style.panel" aria-labelledby="history-heading">
    <h2 id="history-heading">自分の勤怠記録</h2>

    <div :class="$style.scroll">
      <table :class="$style.table">
        <thead>
          <tr>
            <th scope="col">勤務日</th>
            <th scope="col">出勤時刻</th>
            <th scope="col">退勤時刻</th>
            <th scope="col">勤務時間</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="record in history?.records ?? []" :key="record.id">
            <td>{{ record.workDate }}</td>
            <td>{{ formatAttendanceTime(record.clockInAt) }}</td>
            <td>{{ formatAttendanceTime(record.clockOutAt) }}</td>
            <td>{{ formatDuration(record.durationMinutes) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-if="history?.records.length === 0">勤怠記録はまだありません。</p>

    <nav
      v-if="history && history.lastPage > 1"
      :class="$style.pagination"
      aria-label="勤怠記録のページ"
    >
      <button
        type="button"
        :disabled="disabled || page <= 1"
        @click="emit('change-page', page - 1)"
      >
        前へ
      </button>
      <span>{{ history.currentPage }} / {{ history.lastPage }}</span>
      <button
        type="button"
        :disabled="disabled || page >= history.lastPage"
        @click="emit('change-page', page + 1)"
      >
        次へ
      </button>
    </nav>
  </section>
</template>

<style module lang="scss">
@use '~/assets/styles/panel';

.panel {
  @include panel.panel;
}

.scroll {
  overflow-x: auto;
}

.table {
  width: 100%;
  min-width: 480px;
  border-collapse: collapse;
  font-size: 0.875rem;

  th,
  td {
    padding: 0.6rem 0.5rem;
    border-bottom: 1px solid #e5e7eb;
    text-align: left;
    white-space: nowrap;
  }

  th {
    color: #4b5563;
    font-weight: 600;
  }
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.65rem;
  margin-top: 0.75rem;

  button {
    padding: 0.4rem 0.8rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    background: #fff;
    font: inherit;
    cursor: pointer;

    &:disabled {
      opacity: 0.45;
      cursor: not-allowed;
    }
  }
}
</style>
