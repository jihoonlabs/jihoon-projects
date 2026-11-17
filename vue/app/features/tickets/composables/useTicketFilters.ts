import { ref } from 'vue';

import type { AssigneeFilter } from '../utils/filterTickets';

/**
 * 検索語と担当者の絞り込み。プロジェクトを切り替えたら reset で戻す。
 */
export function useTicketFilters() {
  const searchQuery = ref('');
  const assigneeFilter = ref<AssigneeFilter>('ALL');

  function reset(): void {
    searchQuery.value = '';
    assigneeFilter.value = 'ALL';
  }

  return { searchQuery, assigneeFilter, reset };
}
