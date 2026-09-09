'use client';

import { useEffect } from 'react';

import { fetchMe } from '@/features/auth/api/me';
import { useAuthStore } from '@/features/auth/store/useAuthStore';

export function AuthInitializer() {
  const login = useAuthStore((state) => state.login);
  const logout = useAuthStore((state) => state.logout);

  useEffect(() => {
    const restoreAuth = async () => {
      try {
        const user = await fetchMe();

        login(user);
      } catch {
        logout();
      }
    };

    restoreAuth();
  }, [login, logout]);

  return null;
}