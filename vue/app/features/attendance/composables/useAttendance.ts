import { computed, onBeforeUnmount, ref, watch } from 'vue';

import { useAuthStore } from '~/features/auth/stores/authStore';
import { isAbortError } from '~/shared/api/isAbortError';

import {
  ATTENDANCE_ERROR_MESSAGE,
  AttendanceError,
  useAttendanceApi,
} from '../api/attendanceApi';
import type { AttendanceHistory, AttendanceToday, ClockAction } from '../types';

/**
 * 今日の勤怠と自分の勤怠記録を読み込み、出勤・退勤を記録する。
 * - 新しい読み込みを始めたら前の読み込みを中断し、遅れて届いた古い応答で表示を上書きしない。
 * - セッション期限切れの間は勤怠のエラーを出さず、レイアウトの再ログインに任せる。
 */
export function useAttendance() {
  const api = useAttendanceApi();
  const auth = useAuthStore();

  const today = ref<AttendanceToday | null>(null);
  const history = ref<AttendanceHistory | null>(null);
  const page = ref(1);
  const loading = ref(true);
  const submitting = ref(false);
  const error = ref<string | null>(null);

  let loadController: AbortController | null = null;

  const showError = (cause: unknown) => {
    if (isAbortError(cause) || auth.sessionExpired) {
      return;
    }

    error.value =
      cause instanceof AttendanceError
        ? cause.message
        : ATTENDANCE_ERROR_MESSAGE;
  };

  /**
   * 今日の勤怠と指定ページの記録をまとめて読み込む。最後に始めた読み込みの結果だけを反映する。
   */
  const load = async (requestedPage: number): Promise<void> => {
    loadController?.abort();
    const controller = new AbortController();
    loadController = controller;
    loading.value = true;

    try {
      const [latestToday, latestHistory] = await Promise.all([
        api.fetchToday(controller.signal),
        api.fetchHistory(requestedPage, controller.signal),
      ]);

      if (controller.signal.aborted) return;
      today.value = latestToday;
      history.value = latestHistory;
    } finally {
      if (loadController === controller) {
        loadController = null;
        loading.value = false;
      }
    }
  };

  const loadAndShowErrors = async (requestedPage: number) => {
    try {
      await load(requestedPage);
    } catch (cause) {
      showError(cause);
    }
  };

  const changePage = (nextPage: number) => {
    error.value = null;
    page.value = nextPage;
    void loadAndShowErrors(nextPage);
  };

  const clock = async (action: ClockAction) => {
    if (submitting.value || loading.value) return;

    submitting.value = true;
    error.value = null;

    try {
      await api.clock(action);
      await load(page.value);
    } catch (cause) {
      showError(cause);

      // 失敗しても最新の状態に合わせる。再読み込みの失敗では、操作の失敗表示を残す
      try {
        await load(page.value);
      } catch {
        // 操作のエラーを表示したままにする
      }
    } finally {
      submitting.value = false;
    }
  };

  // 期限切れの後に再ログインしたら、その間に変わったかもしれない勤怠を読み直す
  watch(
    () => auth.isAuthenticated,
    (authenticated, wasAuthenticated) => {
      if (authenticated && !wasAuthenticated) {
        error.value = null;
        void loadAndShowErrors(page.value);
      }
    },
  );

  onBeforeUnmount(() => loadController?.abort());

  const actionsDisabled = computed(
    () => loading.value || submitting.value || today.value === null,
  );

  return {
    today,
    history,
    page,
    loading,
    submitting,
    error,
    actionsDisabled,
    start: () => loadAndShowErrors(page.value),
    changePage,
    clock,
  };
}
