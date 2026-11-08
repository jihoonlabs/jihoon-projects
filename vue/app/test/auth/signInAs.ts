import { useAuthStore } from '~/features/auth/stores/authStore';
import { userFixture } from '~/features/auth/test/userFixture';
import type { User } from '~/features/auth/types';

/**
 * セッション復元が済んだログイン状態から始める。
 * 復元要求は送らないため、/api/auth/me の応答を用意する必要はない。
 */
export function signInAs(user: User = userFixture()): User {
  useAuthStore().signIn(user);

  return user;
}

/**
 * セッション復元が済んだ未ログイン状態から始める
 */
export function signedOut(): void {
  useAuthStore().signOut();
}
