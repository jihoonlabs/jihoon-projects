import type { User } from '@/features/users/types/user';

const API_URL = 'http://localhost:8000';

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

  // セッションが存在しない場合
  if (response.status === 401) {
    throw new Error('UNAUTHENTICATED');
  }

  // 認証以外の通信・サーバーエラー
  if (!response.ok) {
    throw new Error('認証情報を取得できませんでした。');
  }

  return response.json();
};