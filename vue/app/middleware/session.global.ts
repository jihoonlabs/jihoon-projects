import { useAuthApi } from '~/features/auth/api/authApi';
import { useAuthStore } from '~/features/auth/stores/authStore';

/**
 * 最初の画面遷移で Laravel のセッションから利用者を復元する。
 * 復元が終わるまで遷移を待たせるため、未確認のまま画面を出さない。
 */
export default defineNuxtRouteMiddleware(async () => {
  const auth = useAuthStore();

  if (auth.initialized) {
    return;
  }

  await auth.restoreSession(useAuthApi().fetchCurrentUser);
});
