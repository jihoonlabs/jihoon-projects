import type { User } from '@/features/users/types/user';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export class AuthApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = 'AuthApiError';
  }
}

export const fetchMe = async (): Promise<User> => {
  const response = await fetch(`${API_URL}/api/auth/me`, {
    method: 'GET',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new AuthApiError('認証情報を取得できませんでした。', response.status);
  }

  return response.json();
};
