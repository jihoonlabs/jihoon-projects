'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

import { LoginForm } from '@/features/auth/components/LoginForm/LoginForm';

import { Header } from '@/shared/components/Header';

import { useAuthStore } from '@/features/auth/store/useAuthStore';

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const router = useRouter();

  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isInitialized = useAuthStore((state) => state.isInitialized);

  const sessionExpired = useAuthStore((state) => state.sessionExpired);
  const userId = useAuthStore((state) => state.user?.id);

  useEffect(() => {
    if (isInitialized && !isAuthenticated && !sessionExpired) {
      router.replace('/login');
    }
  }, [isInitialized, isAuthenticated, sessionExpired, router]);

  // Laravel のセッション確認が完了するまで画面を表示しない
  if (!isInitialized) {
    return null;
  }

  // 未認証の場合はログイン画面へ遷移する
  if (!isAuthenticated && !sessionExpired) {
    return null;
  }

  return (
    <>
      {sessionExpired && (
        <section aria-label="再ログイン">
          <p role="alert">
            セッションの有効期限が切れました。再ログインしてください。未保存の入力はこのタブ内で同じアカウントに再ログインした場合のみ保持されます。再読み込み・画面移動で失われます。
          </p>
          <LoginForm />
        </section>
      )}
      <div key={userId} hidden={sessionExpired} inert={sessionExpired}>
        {!sessionExpired && <Header />}
        {children}
      </div>
    </>
  );
}
