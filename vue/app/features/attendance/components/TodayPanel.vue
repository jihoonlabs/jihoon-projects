<script setup lang="ts">
import { computed } from 'vue';

import { formatAttendanceTime, STATUS_LABELS } from '../format';
import type { AttendanceToday, ClockAction } from '../types';

const props = defineProps<{
  today: AttendanceToday | null;
  disabled: boolean;
}>();

const emit = defineEmits<{ clock: [action: ClockAction] }>();

const statusLabel = computed(() =>
  props.today ? STATUS_LABELS[props.today.status] : '読み込み中...',
);

// 前日に出勤して日付をまたいだまま勤務中の場合は、勤務日を明示する
const crossesMidnight = computed(() => {
  const record = props.today?.record;

  return Boolean(record && record.workDate !== props.today?.date);
});
</script>

<template>
  <section :class="$style.panel" aria-labelledby="today-heading">
    <h2 id="today-heading">今日の勤怠</h2>
    <p :class="$style.status" role="status">{{ statusLabel }}</p>
    <p v-if="crossesMidnight">
      勤務日: {{ today?.record?.workDate }}（日付をまたいで勤務中）
    </p>

    <dl :class="$style.times">
      <div>
        <dt>出勤時刻</dt>
        <dd>{{ formatAttendanceTime(today?.record?.clockInAt ?? null) }}</dd>
      </div>
      <div>
        <dt>退勤時刻</dt>
        <dd>{{ formatAttendanceTime(today?.record?.clockOutAt ?? null) }}</dd>
      </div>
    </dl>

    <div :class="$style.actions">
      <button
        type="button"
        :class="$style.clockIn"
        :disabled="disabled || today?.status !== 'not_started'"
        @click="emit('clock', 'clock-in')"
      >
        出勤
      </button>
      <button
        type="button"
        :class="$style.clockOut"
        :disabled="disabled || today?.status !== 'working'"
        @click="emit('clock', 'clock-out')"
      >
        退勤
      </button>
    </div>
  </section>
</template>

<style module lang="scss">
@use '~/assets/styles/panel';

.panel {
  @include panel.panel;
}

.status {
  display: inline-flex;
  padding: 0.3rem 0.65rem;
  border-radius: 999px;
  background: #eef4ff;
  color: #1d4ed8;
  font-size: 0.875rem;
  font-weight: 700;
}

.times {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 2.5rem;
  margin: 1rem 0 1.25rem;

  dt {
    color: #4b5563;
    font-size: 0.875rem;
  }

  dd {
    margin-top: 0.25rem;
    font-weight: 600;
  }
}

.actions {
  display: flex;
  gap: 0.65rem;

  button {
    flex: 1;
    min-height: 52px;
    padding: 0.7rem 1rem;
    border: 1px solid #295dcc;
    border-radius: 8px;
    font: inherit;
    font-weight: 700;
    cursor: pointer;

    &:disabled {
      opacity: 0.45;
      cursor: not-allowed;
    }
  }

  .clockIn {
    background: #295dcc;
    color: #fff;
  }

  .clockOut {
    background: #fff;
    color: #295dcc;
  }
}
</style>
