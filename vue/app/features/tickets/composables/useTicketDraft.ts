import { ref } from 'vue';

import type { Ticket, TicketPriority, TicketStatus } from '../types/ticket';

interface SavedValues {
  title: string;
  description: string;
  status: TicketStatus;
  priority: TicketPriority;
  assigneeId: string;
}

const snapshotOf = (ticket: Ticket | null): SavedValues => ({
  title: ticket?.title ?? '',
  description: ticket?.description ?? '',
  status: ticket?.status ?? 'TODO',
  priority: ticket?.priority ?? 'MEDIUM',
  assigneeId: ticket?.assignee?.id ?? '',
});

/**
 * モーダルの入力値（下書き）と、最後に保存できた内容・バージョン。
 * 保存できた内容は、応答の項目とバージョンを同じスナップショットとして採用する。
 */
export function useTicketDraft(initialTicket: Ticket | null) {
  const ticket = ref<Ticket | null>(initialTicket);
  const initial = snapshotOf(initialTicket);

  const title = ref(initial.title);
  const description = ref(initial.description);
  const status = ref<TicketStatus>(initial.status);
  const priority = ref<TicketPriority>(initial.priority);
  const assigneeId = ref(initial.assigneeId);

  let saved = initial;
  let version = initialTicket?.version;

  function restoreSavedValues(): void {
    title.value = saved.title;
    description.value = saved.description;
    status.value = saved.status;
    priority.value = saved.priority;
    assigneeId.value = saved.assigneeId;
  }

  /** サーバーの内容を保存済みの基準として採用し、入力もそれに合わせる */
  function adopt(next: Ticket): void {
    saved = snapshotOf(next);
    version = next.version;
    ticket.value = next;
    restoreSavedValues();
  }

  return {
    ticket,
    title,
    description,
    status,
    priority,
    assigneeId,
    restoreSavedValues,
    adopt,
    currentVersion: () => version,
    assigneeChanged: () => assigneeId.value !== saved.assigneeId,
  };
}
