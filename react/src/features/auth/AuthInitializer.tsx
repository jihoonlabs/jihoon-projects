'use client';

import { useEffect } from 'react';

import { AuthApiError, fetchMe } from '@/features/auth/api/me';
import { useAuthStore } from '@/features/auth/store/useAuthStore';

export function AuthInitializer() {
  const login = useAuthStore((state) => state.login);
  const logout = useAuthStore((state) => state.logout);
  const initialize = useAuthStore((state) => state.initialize);

  useEffect(() => {
    const restoreAuth = async () => {
      try {
        const user = await fetchMe();
        login(user);
      } catch (error) {
        if (error instanceof AuthApiError && error.status === 401) {
          logout();
        } else {
          console.error('認証情報の取得に失敗しました。', error);
        }
      } finally {
        initialize();
      }
    };

    restoreAuth();
  }, [login, logout, initialize]);

  return null;
}