'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

import { logoutApi } from '@/features/auth/api/logout';
import { useAuthStore } from '@/features/auth/store/useAuthStore';

import styles from './Header.module.css';

export function Header() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogout = async () => {
    if (pending) return;
    setPending(true);
    setError(null);
    try {
      await logoutApi();
      logout();
      router.replace('/login');
    } catch {
      setError('ログアウトできませんでした。もう一度お試しください。');
    } finally {
      setPending(false);
    }
  };

  return (
    <header className={styles.header}>
      <span className={styles.brand}>タスク管理</span>

      <div className={styles.userInfo}>
        <span>
          ようこそ、<strong>{user?.name}</strong> さん（
          {user?.role === 'admin' ? '管理者' : '一般ユーザー'}）
        </span>

        <button
          type="button"
          onClick={handleLogout}
          disabled={pending}
          className={styles.logoutBtn}
        >
          {pending ? 'ログアウト中...' : 'ログアウト'}
        </button>
      </div>
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
    </header>
  );
}
