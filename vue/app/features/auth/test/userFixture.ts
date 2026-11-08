import type { User } from '../types';

/**
 * Laravel の /api/auth/me と同じ形の利用者。テストで意味のある項目だけを上書きする。
 */
export function userFixture(overrides: Partial<User> = {}): User {
  return {
    id: 1,
    name: 'テストユーザー',
    email: 'user@example.com',
    role: 'user',
    status: 'active',
    createdAt: '2026-11-01T00:00:00.000000Z',
    ...overrides,
  };
}
