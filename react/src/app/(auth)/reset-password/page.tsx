'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { ResetPasswordForm } from '@/features/auth/components/ResetPasswordForm/ResetPasswordForm';

function ResetContent() {
  const params = useSearchParams();
  // 重複したパラメータは従来どおり不正なリンクとして扱う。
  const email = params.getAll('email').length === 1 ? params.get('email')! : '';
  const token = params.getAll('token').length === 1 ? params.get('token')! : '';
  return <ResetPasswordForm email={email} token={token} />;
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<p>読み込み中...</p>}>
      <ResetContent />
    </Suspense>
  );
}
