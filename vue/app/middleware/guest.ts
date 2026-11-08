import { useHomePath } from '~/features/auth/navigation';
import { useAuthStore } from '~/features/auth/stores/authStore';

/**
 * ログイン済みの利用者にはログイン画面を見せず、最初の画面へ移す
 */
export default defineNuxtRouteMiddleware(() => {
  if (useAuthStore().isAuthenticated) {
    return navigateTo(useHomePath(), { replace: true });
  }
});
