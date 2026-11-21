import { onBeforeUnmount, ref, watch, type Ref } from 'vue';

import { isAbortError } from '~/shared/api/isAbortError';

import { useTicketApi } from '../api/ticketApi';
import type { Ticket } from '../types/ticket';
import { detailError } from '../utils/detailError';

/**
 * 詳細モーダルを開くとき、カードの古い内容ではなく最新の 1 件を取得する。
 * 別のチケットに切り替えた・画面を閉じたあとに届いた応答は捨てる。
 */
export function useTicketDetail(ticketId: Ref<string>) {
  const api = useTicketApi();

  const ticket = ref<Ticket | null>(null);
  const error = ref<string | null>(null);

  let controller: AbortController | null = null;
  let sequence = 0;

  async function load(): Promise<void> {
    controller?.abort();
    const mine = ++sequence;
    const current = new AbortController();
    controller = current;
    ticket.value = null;
    error.value = null;

    try {
      const loaded = await api.fetchTicket(ticketId.value, current.signal);

      // 中断だけに頼らず、遅れて届いた応答もここで破棄する
      if (mine === sequence && loaded.id === ticketId.value) {
        ticket.value = loaded;
      }
    } catch (failure) {
      if (mine === sequence && !isAbortError(failure)) {
        error.value = detailError(failure);
      }
    }
  }

  watch(ticketId, () => void load(), { immediate: true });
  onBeforeUnmount(() => {
    controller?.abort();
    sequence += 1;
  });

  return { ticket, error, retry: load };
}
