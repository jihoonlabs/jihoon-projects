import { create } from 'zustand';

import type { AuthState } from '@/features/auth/types/auth';

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,

  // 認証情報は Laravel のセッション Cookie で管理する
  login: (user) => {
    set({
      user,
      isAuthenticated: true,
    });
  },

  // フロントエンドの認証状態を初期化する
  logout: () => {
    set({
      user: null,
      isAuthenticated: false,
    });
  },
}));