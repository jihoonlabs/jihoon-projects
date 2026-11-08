import { watch } from 'vue';

import {
  ApiError,
  useApiClient,
  type ApiClient,
  type ApiRequestOptions,
  type MutationMethod,
} from '~/shared/api/apiClient';

import { useAuthStore } from '../stores/authStore';

type AuthStore = ReturnType<typeof useAuthStore>;

const staleSession = () =>
  new DOMException('認証状態が変更されました。', 'AbortError');

/**
 * ログインが必要な API 要求を実行する。
 * - 要求中にログイン・ログアウト・期限切れが起きたら要求を中断し、古いセッションの応答を使わない。
 * - ログイン中に 401 が返ったらセッション期限切れとして扱う。
 */
export async function protectedRequest<T>(
  store: AuthStore,
  execute: (signal: AbortSignal) => Promise<T>,
  signal?: AbortSignal,
): Promise<T> {
  if (store.sessionExpired) {
    throw staleSession();
  }

  const startedRevision = store.sessionRevision;
  const controller = new AbortController();
  const abort = () => controller.abort();

  if (signal?.aborted) {
    abort();
  }

  signal?.addEventListener('abort', abort, { once: true });

  const stopWatching = watch(
    () => store.sessionRevision,
    (revision) => {
      if (revision !== startedRevision) {
        abort();
      }
    },
    { flush: 'sync' },
  );

  const isOutdated = () =>
    controller.signal.aborted || store.sessionRevision !== startedRevision;

  try {
    const result = await execute(controller.signal);

    if (isOutdated()) {
      throw staleSession();
    }

    return result;
  } catch (error) {
    if (isOutdated()) {
      throw staleSession();
    }

    if (
      error instanceof ApiError &&
      error.status === 401 &&
      store.isAuthenticated
    ) {
      store.expireSession();
    }

    throw error;
  } finally {
    stopWatching();
    signal?.removeEventListener('abort', abort);
  }
}

/**
 * ログインが必要な画面・ストアから使う API クライアント
 */
export function createProtectedApi(client: ApiClient, store: AuthStore) {
  return {
    getJson<T>(path: string, { signal }: ApiRequestOptions = {}) {
      return protectedRequest(
        store,
        (requestSignal) => client.getJson<T>(path, { signal: requestSignal }),
        signal,
      );
    },

    sendJson<T>(
      method: MutationMethod,
      path: string,
      body?: unknown,
      { signal }: ApiRequestOptions = {},
    ) {
      return protectedRequest(
        store,
        (requestSignal) =>
          client.sendJson<T>(method, path, body, { signal: requestSignal }),
        signal,
      );
    },
  };
}

export function useProtectedApi() {
  return createProtectedApi(useApiClient(), useAuthStore());
}
