import { ResetPasswordForm } from '@/features/auth/components/ResetPasswordForm/ResetPasswordForm';

interface ResetPasswordPageProps {
  searchParams: Promise<{
    email?: string;
    token?: string;
  }>;
}

export default async function ResetPasswordPage({
  searchParams,
}: ResetPasswordPageProps) {
  const { email = '', token = '' } = await searchParams;

  return <ResetPasswordForm email={email} token={token} />;
}