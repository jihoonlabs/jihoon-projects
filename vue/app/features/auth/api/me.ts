import type { ApiClient } from '~/shared/api/apiClient';
import type { User } from '~/features/users/types/user';

/**
 * Laravel のセッションに紐づく利用者を取得する
 */
export function fetchCurrentUser(
  client: ApiClient,
  signal?: AbortSignal,
): Promise<User> {
  return client.getJson<User>('/api/auth/me', { signal });
}
