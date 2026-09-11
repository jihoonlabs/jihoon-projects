'use client';

import { useRouter } from 'next/navigation';

import { logoutApi } from '@/features/auth/api/logout';
import { useAuthStore } from '@/features/auth/store/useAuthStore';

import styles from './Header.module.css';

export function Header() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = async () => {
    try {
      await logoutApi();

      logout();
      router.push('/login');
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <header className={styles.header}>
      <h1>タスク管理ボード (Task Board)</h1>

      <div className={styles.userInfo}>
        <span>
          ようこそ、<strong>{user?.name}</strong> さん
        </span>

        <button
          type="button"
          onClick={handleLogout}
          className={styles.logoutBtn}
        >
          ログアウト
        </button>
      </div>
    </header>
  );
}
