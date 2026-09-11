import { create } from 'zustand';

import type { AuthState } from '@/features/auth/types/auth';

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isInitialized: false,

  // ログイン成功後、ユーザー情報を認証状態として保持する
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

  // Laravel のセッション確認が完了したことを記録する
  initialize: () => {
    set({
      isInitialized: true,
    });
  },
}));
