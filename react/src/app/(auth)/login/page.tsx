'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { LoginForm } from '@/features/auth/components/LoginForm/LoginForm';

function LoginContent() {
  const params = useSearchParams();
  return (
    <>
      {process.env.NEXT_PUBLIC_DEMO_MODE === 'true' && (
        <aside style={{ padding: '1rem', textAlign: 'center' }}>
          <strong>公開デモ</strong>
          <p>メール: demo@example.com ／ パスワード: TicketDemo2026!</p>
          <p>
            架空データを使用しています。入力内容は他の閲覧者と共有されます。個人情報は入力しないでください。
          </p>
          <p>新規登録・メール送信・Google/LINE認証はデモでは利用できません。</p>
        </aside>
      )}
      <LoginForm
        error={params.get('error') ?? undefined}
        provider={params.get('provider') ?? undefined}
        verified={params.get('verified') ?? undefined}
        registered={params.get('registered') ?? undefined}
      />
    </>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<p>読み込み中...</p>}>
      <LoginContent />
    </Suspense>
  );
}
