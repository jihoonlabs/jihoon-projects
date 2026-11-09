import { useAuthStore } from '~/features/auth/store/useAuthStore';
import { userFixture } from '~/features/users/test/userFixture';
import type { User } from '~/features/users/types/user';

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
