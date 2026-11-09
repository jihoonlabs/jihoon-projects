import { LOGIN_PATH } from '~/features/auth/utils/navigation';
import { useAuthStore } from '~/features/auth/store/useAuthStore';

/**
 * ログインが必要な画面。未ログインならログイン画面へ移す。
 * セッション期限切れのときは画面に残し、レイアウトで同じタブのまま再ログインさせる。
 */
export default defineNuxtRouteMiddleware(() => {
  const auth = useAuthStore();

  if (!auth.isAuthenticated && !auth.sessionExpired) {
    return navigateTo(LOGIN_PATH, { replace: true });
  }
});
