import { defineStore } from 'pinia';
import { ref } from 'vue';

import { useAuthStore } from '~/features/auth/store/useAuthStore';
import { isAbortError } from '~/shared/api/isAbortError';

import { useTicketApi } from '../api/ticketApi';
import type { Ticket } from '../types/ticket';

const UNEXPECTED_ERROR_MESSAGE = '予期しないエラーが発生しました。';

/**
 * ボードに表示するチケット一覧（読み取り専用）。
 * 古い取得結果や、別のログインセッションの結果で表示を上書きしない。
 */
export const useTicketStore = defineStore('tickets', () => {
  const auth = useAuthStore();
  const api = useTicketApi();

  const tickets = ref<Ticket[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  let sequence = 0;
  let controller: AbortController | null = null;

  async function fetchTickets(): Promise<void> {
    if (!auth.isAuthenticated) {
      return;
    }

    // 取得中の古い要求は破棄し、最後に始めた取得だけを反映する
    controller?.abort();
    const current = new AbortController();
    controller = current;
    const mine = ++sequence;
    const revision = auth.sessionRevision;
    const isLatest = () =>
      mine === sequence && revision === auth.sessionRevision;

    isLoading.value = true;
    error.value = null;

    try {
      const incoming = await api.fetchTickets(current.signal);

      if (isLatest()) {
        tickets.value = incoming;
      }
    } catch (failure) {
      if (isLatest() && !isAbortError(failure)) {
        error.value =
          failure instanceof Error ? failure.message : UNEXPECTED_ERROR_MESSAGE;
      }
    } finally {
      // 後から始まった取得が続いている間は、読み込み中の表示を残す
      if (mine === sequence) {
        isLoading.value = false;
        controller = null;
      }
    }
  }

  /**
   * 画面を離れる・別のアカウントになるときに、取得中の要求ごと状態を初期化する
   */
  function reset(): void {
    controller?.abort();
    controller = null;
    sequence += 1;
    tickets.value = [];
    isLoading.value = false;
    error.value = null;
  }

  return { tickets, isLoading, error, fetchTickets, reset };
});
