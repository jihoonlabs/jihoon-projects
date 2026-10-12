'use client';

import { useRef, useState } from 'react';
import { useRouter } from 'next/navigation';

import { logoutApi } from '@/features/auth/api/logout';
import { useAuthStore } from '@/features/auth/store/useAuthStore';

import styles from './Header.module.css';

export function Header({ compact = false }: { compact?: boolean }) {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inFlight = useRef(false);

  const handleLogout = async () => {
    if (inFlight.current) return;
    inFlight.current = true;
    setPending(true);
    setError(null);
    try {
      await logoutApi();
      logout();
      router.push('/login');
    } catch (reason) {
      // サーバーのセッションが残る失敗を、ログアウト成功として扱わない。
      setError(
        reason instanceof Error ? reason.message : 'ログアウトに失敗しました。',
      );
    } finally {
      inFlight.current = false;
      setPending(false);
    }
  };

  return (
    <div className={compact ? styles.compact : styles.header}>
      {!compact && <h1>タスク管理ボード (Task Board)</h1>}

      <div className={styles.userInfo}>
        <span>
          ようこそ、<strong>{user?.name}</strong> さん
        </span>

        <button
          type="button"
          onClick={handleLogout}
          className={styles.logoutBtn}
          disabled={pending}
        >
          {pending ? 'ログアウト中...' : 'ログアウト'}
        </button>
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
      </div>
    </div>
  );
}
