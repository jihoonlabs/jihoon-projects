import { useHomePath } from '~/features/auth/utils/navigation';
import { useAuthStore } from '~/features/auth/store/useAuthStore';

/**
 * ログイン済みの利用者にはログイン画面を見せず、最初の画面へ移す
 */
export default defineNuxtRouteMiddleware(() => {
  if (useAuthStore().isAuthenticated) {
    return navigateTo(useHomePath(), { replace: true });
  }
});
