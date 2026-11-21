<script setup lang="ts">
import { computed, ref } from 'vue';

import { WRITE_MESSAGE } from '../../constants/ticketMessages';
import { useTicketEditor } from '../../composables/useTicketEditor';
import { useTicketStore } from '../../store/useTicketStore';
import type { ProjectMember } from '../../types/project';
import type { Ticket } from '../../types/ticket';
import type { ProjectChoice } from '../../types/ticketModal';
import TicketConflictPanel from './TicketConflictPanel.vue';
import TicketDetailView from './TicketDetailView.vue';
import TicketFormView from './TicketFormView.vue';
import TicketModalShell from './TicketModalShell.vue';

const props = defineProps<{
  ticket: Ticket | null;
  projectId: string;
  projectColor: string | null;
  projectMembers: ProjectMember[];
  projectChoice: ProjectChoice | null;
  readOnly: boolean;
}>();

const emit = defineEmits<{
  close: [];
  changeProject: [projectId: string];
  retryMembers: [];
}>();

const store = useTicketStore();
const mode = ref<'detail' | 'edit'>(props.ticket ? 'detail' : 'edit');
const deleting = ref(false);
const deleteError = ref<string | null>(null);

const editor = useTicketEditor({
  initialTicket: props.ticket,
  projectId: () => props.projectId,
  readOnly: () => props.readOnly,
  create: store.createTicket,
  update: store.updateTicket,
  onSaveStart: () => {
    deleteError.value = null;
  },
  onCreated: () => emit('close'),
  onUpdated: () => {
    mode.value = 'detail';
  },
});
const {
  ticket: current,
  title,
  description,
  status,
  priority,
  assigneeId,
  conflict,
  latest,
  reloading,
  reloadError,
  unavailable,
} = editor;

const submitting = computed(() => editor.submitting.value || deleting.value);
const saveError = computed(() => deleteError.value ?? editor.saveError.value);
const canEdit = computed(
  () => !!current.value && !props.readOnly && !unavailable.value,
);
const isDetail = computed(() => !!current.value && mode.value === 'detail');
const heading = computed(() =>
  isDetail.value
    ? 'チケット詳細'
    : current.value
      ? 'チケット編集'
      : 'チケット作成',
);
const assigneeName = computed(() => {
  if (!assigneeId.value) return '未割り当て';

  return (
    props.projectMembers.find((member) => member.id === assigneeId.value)
      ?.name ??
    current.value?.assignee?.name ??
    '—'
  );
});

function startEdit() {
  editor.clearSaveError();
  deleteError.value = null;
  mode.value = 'edit';
}

function cancelEdit() {
  if (!current.value) {
    emit('close');
    return;
  }

  editor.restoreSavedValues();
  editor.clearSaveError();
  deleteError.value = null;
  // 競合したまま取り消したときは、古い内容に戻さず閉じる
  if (conflict.value) {
    emit('close');
    return;
  }
  mode.value = 'detail';
}

async function remove() {
  const target = current.value;
  if (!target || !canEdit.value || submitting.value) return;
  if (!window.confirm(`${target.issueKey ?? target.title} を削除しますか？`)) {
    return;
  }

  deleting.value = true;
  editor.clearSaveError();
  deleteError.value = null;

  try {
    await store.deleteTicket(target.id);
    emit('close');
  } catch (error) {
    deleteError.value =
      error instanceof Error ? error.message : WRITE_MESSAGE.deleteFailed;
  } finally {
    deleting.value = false;
  }
}

function submit(event: Event) {
  // 削除の最中は保存しない
  if (deleting.value) event.preventDefault();
  else void editor.submit(event);
}

function changeProject(projectId: string) {
  // 別のプロジェクトの担当者を送らないよう、担当者だけ選び直す。他の入力は残す
  editor.resetAssigneeForProjectChange();
  deleteError.value = null;
  emit('changeProject', projectId);
}
</script>

<template>
  <TicketModalShell
    :heading="heading"
    :issue-key="isDetail ? current?.issueKey : null"
    :focus-heading="isDetail"
    :project-color="projectColor"
    :locked="submitting"
    @close="$emit('close')"
  >
    <TicketDetailView
      v-if="isDetail && current"
      :ticket="current"
      :assignee-name="assigneeName"
      :can-edit="canEdit"
      :submitting="submitting"
      :save-error="saveError"
      @close="$emit('close')"
      @edit="startEdit"
      @remove="remove"
    />
    <TicketFormView
      v-else
      v-model:title="title"
      v-model:description="description"
      v-model:status="status"
      v-model:priority="priority"
      v-model:assignee-id="assigneeId"
      :ticket="current"
      :project-id="projectId"
      :project-choice="projectChoice"
      :project-members="projectMembers"
      :submitting="submitting"
      :read-only="readOnly"
      :unavailable="unavailable"
      :conflict="conflict"
      :save-error="saveError"
      @submit="submit"
      @cancel="cancelEdit"
      @change-project="changeProject"
      @retry-members="$emit('retryMembers')"
    >
      <TicketConflictPanel
        v-if="conflict"
        :latest="latest"
        :reloading="reloading"
        :reload-error="reloadError"
        :unavailable="unavailable"
        @reload="editor.loadLatest()"
        @adopt="editor.adoptLatest()"
      />
    </TicketFormView>
  </TicketModalShell>
</template>
