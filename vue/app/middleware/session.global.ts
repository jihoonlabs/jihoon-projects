import { fetchCurrentUser } from '~/features/auth/api/me';
import { useApiClient } from '~/shared/api/apiClient';
import { useAuthStore } from '~/features/auth/store/useAuthStore';

/**
 * 最初の画面遷移で Laravel のセッションから利用者を復元する。
 * 復元が終わるまで遷移を待たせるため、未確認のまま画面を出さない。
 */
export default defineNuxtRouteMiddleware(async () => {
  const auth = useAuthStore();

  if (auth.initialized) {
    return;
  }

  const client = useApiClient();

  await auth.restoreSession((signal) => fetchCurrentUser(client, signal));
});
