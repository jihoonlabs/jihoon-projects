import { cancelSessionRestore } from './me';
import { fetchWithCsrf } from '@/shared/api/fetchWithCsrf';

export const logoutApi = async (): Promise<void> => {
  cancelSessionRestore();
  const response = await fetchWithCsrf('/api/auth/logout', {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error('ログアウトに失敗しました。');
  }
};
