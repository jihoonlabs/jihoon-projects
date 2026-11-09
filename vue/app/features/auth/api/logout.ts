import type { ApiClient } from '~/shared/api/apiClient';

export async function logout(client: ApiClient): Promise<void> {
  try {
    await client.sendJson('POST', '/api/auth/logout');
  } catch {
    throw new Error('ログアウトに失敗しました。');
  }
}
