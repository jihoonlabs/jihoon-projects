import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

import { ApiError } from '~/shared/api/apiClient';

import type { User } from '../types';

export type FetchCurrentUser = (signal: AbortSignal) => Promise<User>;

/**
 * Laravel のセッションに対応するフロントエンドの認証状態。
 * sessionRevision はログイン・ログアウト・期限切れのたびに進み、古いセッションの応答を見分けるために使う。
 */
export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const initialized = ref(false);
  const sessionRevision = ref(0);
  const sessionExpired = ref(false);

  const isAuthenticated = computed(
    () => user.value !== null && !sessionExpired.value,
  );

  let restoreController: AbortController | null = null;
  let pendingRestore: Promise<void> | null = null;

  const cancelRestore = () => {
    restoreController?.abort();
    restoreController = null;
    pendingRestore = null;
  };

  function signIn(signedInUser: User) {
    // 復元中の古い応答で、新しいログインを上書きしない
    cancelRestore();
    user.value = signedInUser;
    initialized.value = true;
    sessionExpired.value = false;
    sessionRevision.value += 1;
  }

  function signOut() {
    cancelRestore();
    user.value = null;
    initialized.value = true;
    sessionExpired.value = false;
    sessionRevision.value += 1;
  }

  function expireSession() {
    // 同じアカウントでの再ログインかを判定するため、利用者情報は残す
    sessionExpired.value = true;
    sessionRevision.value += 1;
  }

  function markInitialized() {
    initialized.value = true;
  }

  /**
   * Laravel のセッションから利用者を一度だけ復元する。同時に呼ばれても要求は 1 回にまとめる。
   */
  function restoreSession(fetchCurrentUser: FetchCurrentUser): Promise<void> {
    if (initialized.value) {
      return Promise.resolve();
    }

    if (pendingRestore) {
      return pendingRestore;
    }

    const controller = new AbortController();
    const startedRevision = sessionRevision.value;
    restoreController = controller;

    const restoring = (async () => {
      try {
        const restoredUser = await fetchCurrentUser(controller.signal);

        if (
          !controller.signal.aborted &&
          sessionRevision.value === startedRevision
        ) {
          user.value = restoredUser;
          sessionRevision.value += 1;
        }
      } catch (error) {
        const outdated =
          controller.signal.aborted ||
          sessionRevision.value !== startedRevision;
        const signedOut =
          error instanceof ApiError &&
          (error.status === 401 || error.status === 403);

        // 未ログイン（401・403）は正常な結果。それ以外の失敗だけを記録する
        if (!outdated && !signedOut) {
          console.error('認証情報の取得に失敗しました。', error);
        }
      } finally {
        if (restoreController === controller) {
          restoreController = null;
          pendingRestore = null;
        }

        if (!controller.signal.aborted) {
          initialized.value = true;
        }
      }
    })();

    pendingRestore = restoring;

    return restoring;
  }

  /**
   * 初期状態に戻す（テストや、アプリ全体の状態を捨てるとき用）
   */
  function reset() {
    cancelRestore();
    user.value = null;
    initialized.value = false;
    sessionRevision.value = 0;
    sessionExpired.value = false;
  }

  return {
    user,
    initialized,
    sessionRevision,
    sessionExpired,
    isAuthenticated,
    signIn,
    signOut,
    expireSession,
    markInitialized,
    restoreSession,
    reset,
  };
});
