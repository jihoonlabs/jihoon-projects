import { ResetPasswordForm } from '@/features/auth/components/ResetPasswordForm/ResetPasswordForm';

interface ResetPasswordPageProps {
  searchParams: Promise<{
    email?: string | string[];
    token?: string | string[];
  }>;
}

export default async function ResetPasswordPage({
  searchParams,
}: ResetPasswordPageProps) {
  const params = await searchParams;

  const email = typeof params.email === 'string' ? params.email : '';
  const token = typeof params.token === 'string' ? params.token : '';

  return <ResetPasswordForm email={email} token={token} />;
}
