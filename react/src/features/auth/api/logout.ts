import { fetchWithCsrf } from '@/shared/api/fetchWithCsrf';

export const logoutApi = async (): Promise<void> => {
  const response = await fetchWithCsrf('/api/auth/logout', {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error('ログアウトに失敗しました。');
  }
};
