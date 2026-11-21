import { onBeforeUnmount, ref } from 'vue';

import { isAbortError } from '~/shared/api/isAbortError';

import { isTicketApiError } from '../api/apiErrors';
import { useTicketApi } from '../api/ticketApi';
import { WRITE_MESSAGE } from '../constants/ticketMessages';
import type {
  CreateTicketInput,
  Ticket,
  UpdateTicketInput,
} from '../types/ticket';
import { detailError } from '../utils/detailError';
import { useTicketDraft } from './useTicketDraft';

const LOST_ACCESS = [401, 403, 404];

interface Options {
  initialTicket: Ticket | null;
  projectId: () => string;
  readOnly: () => boolean;
  create: (input: CreateTicketInput) => Promise<unknown>;
  update: (id: string, input: UpdateTicketInput) => Promise<Ticket>;
  onSaveStart: () => void;
  onCreated: () => void;
  onUpdated: () => void;
}

/**
 * 作成・編集の保存と、他の人の更新（409）との競合の扱い。
 * 競合しても入力は消さず、自動で再送もしない。最新の内容は明示操作でだけ採用する。
 */
export function useTicketEditor(options: Options) {
  const api = useTicketApi();
  const draft = useTicketDraft(options.initialTicket);

  const submitting = ref(false);
  const saveError = ref<string | null>(null);
  const unavailable = ref(false);
  const conflict = ref(false);
  const latest = ref<Ticket | null>(null);
  const reloading = ref(false);
  const reloadError = ref<string | null>(null);

  // 閉じた・別のチケットに切り替えた画面へ、遅れて届いた結果を反映しない
  let alive = true;
  onBeforeUnmount(() => {
    alive = false;
  });

  function markLostAccess(error: unknown, statuses: number[]): void {
    if (isTicketApiError(error) && statuses.includes(error.status ?? 0)) {
      unavailable.value = true;
    }
  }

  async function loadLatest(): Promise<void> {
    const current = draft.ticket.value;
    if (!current || reloading.value) return;

    reloading.value = true;
    reloadError.value = null;

    try {
      const incoming = await api.fetchTicket(current.id);
      if (alive) latest.value = incoming;
    } catch (failure) {
      if (alive && !isAbortError(failure)) {
        reloadError.value = detailError(failure);
        markLostAccess(failure, LOST_ACCESS);
      }
    } finally {
      if (alive) reloading.value = false;
    }
  }

  /** 再取得だけでは入力を変えない。明示操作で、最新の内容から編集をやり直す */
  function adoptLatest(): void {
    if (!latest.value) return;

    draft.adopt(latest.value);
    latest.value = null;
    conflict.value = false;
    saveError.value = null;
  }

  function buildUpdate(): UpdateTicketInput {
    return {
      expectedVersion: draft.currentVersion(),
      title: draft.title.value.trim(),
      description: draft.description.value.trim() || null,
      status: draft.status.value,
      priority: draft.priority.value,
      // 担当者が変わっていなければ送らない（直前に保存できた値と比べる）
      ...(draft.assigneeChanged()
        ? { assigneeId: draft.assigneeId.value || null }
        : {}),
    };
  }

  function handleFailure(error: unknown): void {
    if (isTicketApiError(error) && error.code === 'ticket_conflict') {
      conflict.value = true;
      saveError.value = WRITE_MESSAGE.conflict;
      return;
    }

    markLostAccess(error, [403, 404]);
    saveError.value =
      isTicketApiError(error) && LOST_ACCESS.includes(error.status ?? 0)
        ? detailError(error)
        : error instanceof Error
          ? error.message
          : WRITE_MESSAGE.saveFailed;
  }

  async function submit(event: Event): Promise<void> {
    event.preventDefault();
    if (
      options.readOnly() ||
      unavailable.value ||
      conflict.value ||
      !draft.title.value.trim() ||
      submitting.value
    ) {
      return;
    }

    submitting.value = true;
    saveError.value = null;
    options.onSaveStart();

    try {
      const current = draft.ticket.value;

      if (current) {
        const updated = await options.update(current.id, buildUpdate());
        if (!alive) return;
        draft.adopt(updated);
        options.onUpdated();
      } else {
        await options.create({
          projectId: options.projectId(),
          title: draft.title.value.trim(),
          description: draft.description.value.trim() || null,
          status: draft.status.value,
          priority: draft.priority.value,
          assigneeId: draft.assigneeId.value || null,
        });
        if (!alive) return;
        options.onCreated();
      }
    } catch (error) {
      if (alive && !isAbortError(error)) handleFailure(error);
    } finally {
      if (alive) submitting.value = false;
    }
  }

  return {
    ...draft,
    submitting,
    saveError,
    unavailable,
    conflict,
    latest,
    reloading,
    reloadError,
    clearSaveError: () => {
      saveError.value = null;
    },
    resetAssigneeForProjectChange: () => {
      draft.assigneeId.value = '';
      saveError.value = null;
    },
    loadLatest,
    adoptLatest,
    submit,
  };
}
