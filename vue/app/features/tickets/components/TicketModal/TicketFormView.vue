<script setup lang="ts">
import type { ProjectMember } from '../../types/project';
import type { Ticket, TicketPriority, TicketStatus } from '../../types/ticket';
import type { ProjectChoice } from '../../types/ticketModal';
import { PRIORITY_LABELS, STATUS_LABELS } from '../../utils/ticketLabels';

const props = defineProps<{
  /** 編集中のチケット（作成なら null） */
  ticket: Ticket | null;
  projectId: string;
  projectChoice: ProjectChoice | null;
  projectMembers: ProjectMember[];
  submitting: boolean;
  readOnly: boolean;
  unavailable: boolean;
  conflict: boolean;
  saveError: string | null;
}>();

const title = defineModel<string>('title', { required: true });
const description = defineModel<string>('description', { required: true });
const status = defineModel<TicketStatus>('status', { required: true });
const priority = defineModel<TicketPriority>('priority', { required: true });
const assigneeId = defineModel<string>('assigneeId', { required: true });

defineEmits<{
  submit: [event: Event];
  cancel: [];
  changeProject: [projectId: string];
  retryMembers: [];
}>();

const hasMissingAssignee = () =>
  Boolean(
    props.ticket?.assignee &&
    !props.projectMembers.some(
      (member) => member.id === props.ticket?.assignee?.id,
    ),
  );
</script>

<template>
  <form :class="$style.form" @submit="$emit('submit', $event)">
    <template v-if="!ticket && projectChoice">
      <label>
        作成先プロジェクト
        <select
          :value="projectId"
          :disabled="submitting"
          @change="
            $emit('changeProject', ($event.target as HTMLSelectElement).value)
          "
        >
          <option value="ALL">プロジェクトを選択してください</option>
          <option
            v-for="project in projectChoice.projects.filter(
              (item) => !item.archivedAt,
            )"
            :key="project.id"
            :value="project.id"
          >
            {{ project.name }}
          </option>
        </select>
      </label>
      <p v-if="projectChoice.message" role="status">
        {{ projectChoice.message }}
      </p>
      <button
        v-if="projectChoice.canRetry"
        type="button"
        @click="$emit('retryMembers')"
      >
        メンバーと権限を再取得
      </button>
    </template>

    <label>
      タイトル
      <input
        v-model="title"
        :disabled="submitting"
        required
        maxlength="255"
        autofocus
      />
    </label>
    <label>
      説明
      <textarea v-model="description" :disabled="submitting" rows="5" />
    </label>
    <label>
      ステータス
      <select v-model="status" :disabled="submitting">
        <option v-for="(label, value) in STATUS_LABELS" :key="value" :value>
          {{ label }}
        </option>
      </select>
    </label>
    <label>
      優先度
      <select v-model="priority" :disabled="submitting">
        <option v-for="(label, value) in PRIORITY_LABELS" :key="value" :value>
          {{ label }}
        </option>
      </select>
    </label>
    <label>
      担当者
      <select v-model="assigneeId" :disabled="submitting">
        <option value="">未割り当て</option>
        <!-- 既にメンバーでない担当者も、選択肢から消さない -->
        <option v-if="hasMissingAssignee()" :value="ticket?.assignee?.id">
          {{ ticket?.assignee?.name }}
        </option>
        <option
          v-for="member in projectMembers"
          :key="member.id"
          :value="member.id"
        >
          {{ member.name }}
        </option>
      </select>
    </label>

    <p v-if="saveError" :class="$style.error" role="alert">{{ saveError }}</p>
    <slot />

    <div :class="$style.actions">
      <button type="button" :disabled="submitting" @click="$emit('cancel')">
        {{ ticket ? 'キャンセル' : '閉じる' }}
      </button>
      <button
        type="submit"
        :disabled="
          readOnly || submitting || conflict || unavailable || !title.trim()
        "
      >
        {{ submitting ? '保存中...' : '保存' }}
      </button>
    </div>
  </form>
</template>

<style module lang="scss">
.form {
  display: grid;
  gap: 0.75rem;

  label {
    display: grid;
    gap: 0.25rem;
    font-size: 0.875rem;
  }
}

.error {
  margin: 0;
  color: #b91c1c;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}
</style>
