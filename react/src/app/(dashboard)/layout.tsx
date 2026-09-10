'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

import { useAuthStore } from '@/features/auth/store/useAuthStore';

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const router = useRouter();

  const isAuthenticated = useAuthStore(
    (state) => state.isAuthenticated,
  );
  const isInitialized = useAuthStore(
    (state) => state.isInitialized,
  );

  useEffect(() => {
    if (isInitialized && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isInitialized, isAuthenticated, router]);

  // Laravel のセッション確認が完了するまで画面を表示しない
  if (!isInitialized) {
    return null;
  }

  // 未認証の場合はログイン画面へ遷移する
  if (!isAuthenticated) {
    return null;
  }

  return children;
}