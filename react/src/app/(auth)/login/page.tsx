import { LoginForm } from '@/features/auth/components/LoginForm/LoginForm';
import type { LoginRedirectParams } from '@/features/auth/types/auth';

interface LoginPageProps {
  searchParams: Promise<LoginRedirectParams>;
}

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const redirectParams = await searchParams;

  return <LoginForm {...redirectParams} />;
}
