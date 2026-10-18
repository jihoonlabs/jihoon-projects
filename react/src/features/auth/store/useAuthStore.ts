import { create } from 'zustand';

import type { AuthState } from '@/features/auth/types/auth';

export const useAuthStore = create<AuthState>((set) => ({
  sessionRevision: 0,
  sessionExpired: false,
  expireSession: () =>
    set((state) => ({
      isAuthenticated: false,
      sessionExpired: true,
      sessionRevision: state.sessionRevision + 1,
    })),
  user: null,
  isAuthenticated: false,
  isInitialized: false,

  // ログイン成功後、ユーザー情報を認証状態として保持する
  login: (user) => {
    set((state) => ({
      user,
      isAuthenticated: true,
      sessionExpired: false,
      sessionRevision: state.sessionRevision + 1,
    }));
  },

  // フロントエンドの認証状態を初期化する
  logout: () => {
    set((state) => ({
      user: null,
      isAuthenticated: false,
      sessionExpired: false,
      sessionRevision: state.sessionRevision + 1,
    }));
  },

  // Laravel のセッション確認が完了したことを記録する
  initialize: () => {
    set({
      isInitialized: true,
    });
  },
}));
