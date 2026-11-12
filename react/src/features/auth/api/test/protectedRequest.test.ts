import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';
import { protectedFetch, protectedMutation } from '../protectedRequest';
import { useAuthStore } from '../../store/useAuthStore';
import type { User } from '@/features/users/types/user';

const user: User = {
  id: 1,
  name: 'User',
  email: 'user@example.com',
  role: 'user',
  status: 'active',
  createdAt: '',
};
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}
beforeEach(() => {
  useAuthStore.getState().login(user);
  useAuthStore.getState().initialize();
});
afterEach(() => vi.unstubAllGlobals());

describe('認証が必要なリクエスト', () => {
  it('401を受け取ると、下書きの所有者情報を保持したままセッションを失効させること', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(null, { status: 401 })),
    );
    const response = await protectedFetch('/api/projects');
    expect(response.status).toBe(401);
    expect(useAuthStore.getState()).toMatchObject({
      isAuthenticated: false,
      sessionExpired: true,
      user,
    });
  });
  it('権限不足で403を受け取ってもログイン状態を維持すること', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(null, { status: 403 })),
    );
    await protectedFetch('/api/tickets');
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });
  it.each([200, 401])(
    '再ログイン後に届いた以前のリクエストの%s応答を破棄すること',
    async (status) => {
      const pending = deferred<Response>();
      const fetchMock = vi.fn().mockReturnValue(pending.promise);
      vi.stubGlobal('fetch', fetchMock);
      const request = protectedFetch('/api/projects');
      const rejected = expect(request).rejects.toMatchObject({
        name: 'AbortError',
      });
      useAuthStore.getState().login({ ...user, id: 2 });
      expect(fetchMock.mock.calls[0][1].signal.aborted).toBe(true);
      pending.resolve(new Response(null, { status }));
      await rejected;
      expect(useAuthStore.getState()).toMatchObject({
        isAuthenticated: true,
        sessionExpired: false,
        user: { id: 2 },
      });
    },
  );
  it('セッションが失効している間は読み取りと更新のリクエストを送信しないこと', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    useAuthStore.getState().expireSession();
    await expect(protectedFetch('/api/tickets')).rejects.toMatchObject({
      name: 'AbortError',
    });
    await expect(
      protectedMutation('/api/tickets', { method: 'POST' }),
    ).rejects.toMatchObject({ name: 'AbortError' });
    expect(fetchMock).not.toHaveBeenCalled();
  });
  it('CSRFの準備後に更新リクエストが401を受け取るとセッションを失効させること', async () => {
    document.cookie = 'XSRF-TOKEN=fixture; path=/';
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(new Response(null, { status: 401 }));
    vi.stubGlobal('fetch', fetchMock);
    await protectedMutation('/api/tickets/1', { method: 'PATCH' });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(useAuthStore.getState().sessionExpired).toBe(true);
  });
});
