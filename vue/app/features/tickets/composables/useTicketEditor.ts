import { ref } from 'vue';

import { useTicketApi } from '../api/ticketApi';
import { TicketConflictError } from '../api/apiErrors';
import { useTicketWriteApi } from '../api/ticketWriteApi';
import type { Ticket, TicketPriority, TicketStatus } from '../types/ticket';

interface EditorValues {
  title: string;
  description: string;
  status: TicketStatus;
  priority: TicketPriority;
  assigneeId: string;
}

const valuesOf = (ticket: Ticket): EditorValues => ({
  title: ticket.title,
  description: ticket.description ?? '',
  status: ticket.status,
  priority: ticket.priority,
  assigneeId: ticket.assignee ? String(ticket.assignee.id) : '',
});

/**
 * 既存チケットの編集状態。保存は expectedVersion 付きで送り、競合時は入力を保持して最新を取り直せるようにする。
 */
export function useTicketEditor(initial: Ticket, onSaved: (ticket: Ticket) => void) {
  const writeApi = useTicketWriteApi();
  const readApi = useTicketApi();

  // 保存に成功した時点の値とバージョン。差分送信とバージョン判定の基準になる。
  let saved = valuesOf(initial);
  let version = initial.version;

  const title = ref(saved.title);
  const description = ref(saved.description);
  const status = ref<TicketStatus>(saved.status);
  const priority = ref<TicketPriority>(saved.priority);
  const assigneeId = ref(saved.assigneeId);
  const saving = ref(false);
  const saveError = ref<string | null>(null);
  const conflict = ref(false);
  const latest = ref<Ticket | null>(null);

  const restore = (values: EditorValues) => {
    title.value = values.title;
    description.value = values.description;
    status.value = values.status;
    priority.value = values.priority;
    assigneeId.value = values.assigneeId;
  };

  async function save(): Promise<void> {
    if (saving.value || !title.value.trim()) return;
    saving.value = true;
    saveError.value = null;

    const trimmedTitle = title.value.trim();
    const nextDescription = description.value.trim() || null;
    const changedAssignee = assigneeId.value !== saved.assigneeId;

    try {
      const updated = await writeApi.updateTicket(initial.id, {
        expectedVersion: version,
        title: trimmedTitle,
        description: nextDescription,
        status: status.value,
        priority: priority.value,
        // 担当者を変えていない場合は送らない（別の人が担当を変えていても上書きしない）
        ...(changedAssignee ? { assigneeId: assigneeId.value || null } : {}),
      });
      // 応答のフィールドとバージョンを同じスナップショットとして採用する
      saved = valuesOf(updated);
      version = updated.version;
      restore(saved);
      onSaved(updated);
    } catch (error) {
      if (error instanceof TicketConflictError) {
        conflict.value = true;
        saveError.value =
          '他のユーザーが変更したため保存できませんでした。入力内容は保持されています。';
      } else {
        saveError.value =
          error instanceof Error ? error.message : '保存に失敗しました。';
      }
    } finally {
      saving.value = false;
    }
  }

  async function loadLatest(): Promise<void> {
    try {
      latest.value = await readApi.fetchTicket(initial.id);
    } catch (error) {
      saveError.value =
        error instanceof Error ? error.message : '最新の情報を取得できませんでした。';
    }
  }

  /** 最新の内容で編集をやり直す。入力中の値は捨てる（明示操作のときだけ）。 */
  function useLatest(): void {
    if (!latest.value) return;
    saved = valuesOf(latest.value);
    version = latest.value.version;
    restore(saved);
    latest.value = null;
    conflict.value = false;
    saveError.value = null;
  }

  return {
    title,
    description,
    status,
    priority,
    assigneeId,
    saving,
    saveError,
    conflict,
    latest,
    save,
    loadLatest,
    useLatest,
  };
}
