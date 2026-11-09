import { describe, expect, it, vi } from 'vitest';

import { ApiError } from '~/shared/api/apiClient';

import { userFixture } from '../../../users/test/userFixture';
import type { User } from '~/features/users/types/user';
import { useAuthStore } from '../useAuthStore';

const deferred = <T>() => {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((onResolve, onReject) => {
    resolve = onResolve;
    reject = onReject;
  });

  return { promise, resolve, reject };
};

describe('認証ストア', () => {
  describe('初期状態', () => {
    it('未ログイン・未確認・期限切れなしで始まること', () => {
      const auth = useAuthStore();

      expect(auth.user).toBeNull();
      expect(auth.initialized).toBe(false);
      expect(auth.isAuthenticated).toBe(false);
      expect(auth.sessionExpired).toBe(false);
      expect(auth.sessionRevision).toBe(0);
    });
  });

  describe('ログイン・ログアウト・期限切れ', () => {
    it('ログインすると利用者を保持し、確認済みにしてリビジョンを進めること', () => {
      const auth = useAuthStore();
      const user = userFixture({ id: 5 });

      auth.signIn(user);

      expect(auth.user).toEqual(user);
      expect(auth.isAuthenticated).toBe(true);
      expect(auth.initialized).toBe(true);
      expect(auth.sessionRevision).toBe(1);
    });

    it('ログアウトすると利用者を消し、リビジョンを進めること', () => {
      const auth = useAuthStore();
      auth.signIn(userFixture());

      auth.signOut();

      expect(auth.user).toBeNull();
      expect(auth.isAuthenticated).toBe(false);
      expect(auth.sessionRevision).toBe(2);
    });

    it('期限切れでは利用者を残したまま未認証として扱い、リビジョンを進めること', () => {
      const auth = useAuthStore();
      const user = userFixture({ id: 8 });
      auth.signIn(user);

      auth.expireSession();

      expect(auth.user).toEqual(user);
      expect(auth.isAuthenticated).toBe(false);
      expect(auth.sessionExpired).toBe(true);
      expect(auth.sessionRevision).toBe(2);
    });

    it('期限切れの後に再ログインすると期限切れが解除されること', () => {
      const auth = useAuthStore();
      auth.signIn(userFixture());
      auth.expireSession();

      auth.signIn(userFixture());

      expect(auth.sessionExpired).toBe(false);
      expect(auth.isAuthenticated).toBe(true);
    });
  });

  describe('セッション復元', () => {
    it('セッションの利用者でログイン状態にし、確認済みにすること', async () => {
      const auth = useAuthStore();
      const user = userFixture({ id: 4 });

      await auth.restoreSession(async () => user);

      expect(auth.user).toEqual(user);
      expect(auth.isAuthenticated).toBe(true);
      expect(auth.initialized).toBe(true);
    });

    it('未ログイン（401）なら未ログインのまま確認済みにし、エラーを記録しないこと', async () => {
      const auth = useAuthStore();
      const consoleError = vi
        .spyOn(console, 'error')
        .mockImplementation(() => undefined);

      await auth.restoreSession(async () => {
        throw new ApiError('API 要求に失敗しました (401)', 401);
      });

      expect(auth.user).toBeNull();
      expect(auth.initialized).toBe(true);
      expect(consoleError).not.toHaveBeenCalled();
    });

    it('通信エラーなら未ログインのまま確認済みにし、エラーを記録すること', async () => {
      const auth = useAuthStore();
      const failure = new TypeError('Failed to fetch');
      const consoleError = vi
        .spyOn(console, 'error')
        .mockImplementation(() => undefined);

      await auth.restoreSession(async () => {
        throw failure;
      });

      expect(auth.user).toBeNull();
      expect(auth.initialized).toBe(true);
      expect(consoleError).toHaveBeenCalledWith(
        '認証情報の取得に失敗しました。',
        failure,
      );
    });

    it('同時に呼ばれても、利用者の取得は 1 回だけ行うこと', async () => {
      const auth = useAuthStore();
      const fetchCurrentUser = vi.fn(async () => userFixture());

      await Promise.all([
        auth.restoreSession(fetchCurrentUser),
        auth.restoreSession(fetchCurrentUser),
      ]);

      expect(fetchCurrentUser).toHaveBeenCalledTimes(1);
    });

    it('確認済みなら、再び利用者を取得しないこと', async () => {
      const auth = useAuthStore();
      const fetchCurrentUser = vi.fn(async () => userFixture());
      await auth.restoreSession(fetchCurrentUser);

      await auth.restoreSession(fetchCurrentUser);

      expect(fetchCurrentUser).toHaveBeenCalledTimes(1);
    });

    it('復元中にログインしたら、遅れて届いた復元結果でログインを上書きしないこと', async () => {
      const auth = useAuthStore();
      const pending = deferred<User>();
      let receivedSignal: AbortSignal | undefined;
      const restoring = auth.restoreSession((signal) => {
        receivedSignal = signal;
        return pending.promise;
      });
      const signedIn = userFixture({ id: 20, name: '新しいログイン' });

      auth.signIn(signedIn);
      pending.resolve(userFixture({ id: 10, name: '古いセッション' }));
      await restoring;

      expect(receivedSignal?.aborted).toBe(true);
      expect(auth.user).toEqual(signedIn);
    });

    it('復元中にログアウトしたら、遅れて届いた復元結果でログイン状態に戻さないこと', async () => {
      const auth = useAuthStore();
      const pending = deferred<User>();
      const restoring = auth.restoreSession(() => pending.promise);

      auth.signOut();
      pending.resolve(userFixture());
      await restoring;

      expect(auth.user).toBeNull();
      expect(auth.initialized).toBe(true);
    });
  });

  describe('初期化', () => {
    it('ログイン状態と確認済みの印を消し、初期状態へ戻すこと', () => {
      const auth = useAuthStore();
      auth.signIn(userFixture());
      auth.expireSession();

      auth.reset();

      expect(auth.user).toBeNull();
      expect(auth.initialized).toBe(false);
      expect(auth.sessionExpired).toBe(false);
      expect(auth.sessionRevision).toBe(0);
    });
  });
});
