import type { User } from '@/features/auth/types/user';

const API_URL = 'http://localhost:8000';

export const fetchMe = async (): Promise<User> => {
  const response = await fetch(`${API_URL}/api/auth/me`, {
    method: 'GET',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('認証情報を取得できませんでした。');
  }

  return response.json();
};