'use client';

import { useEffect } from 'react';

import {
  AuthApiError,
  cancelSessionRestore,
  fetchMe,
} from '@/features/auth/api/me';
import { useAuthStore } from '@/features/auth/store/useAuthStore';

export function AuthInitializer() {
  const login = useAuthStore((state) => state.login);
  const logout = useAuthStore((state) => state.logout);
  const initialize = useAuthStore((state) => state.initialize);

  useEffect(() => {
    let active = true;
    const startedWith = useAuthStore.getState();
    const isCurrent = () => active && useAuthStore.getState() === startedWith;
    const restoreAuth = async () => {
      try {
        const user = await fetchMe();
        if (isCurrent()) login(user);
      } catch (error) {
        // 初期GETより後のログイン・ログアウトを遅延応答で取り消さない。
        if (
          !isCurrent() ||
          (error instanceof Error && error.name === 'AbortError')
        )
          return;
        if (
          error instanceof AuthApiError &&
          (error.status === 401 || error.status === 403)
        ) {
          logout();
        } else {
          console.error('認証情報の取得に失敗しました。', error);
        }
      } finally {
        if (active) initialize();
      }
    };

    void restoreAuth();
    return () => {
      active = false;
      cancelSessionRestore();
    };
  }, [login, logout, initialize]);

  return null;
}
