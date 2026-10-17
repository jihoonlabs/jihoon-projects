import { useAuthStore } from '../store/useAuthStore';
import { fetchWithCsrf } from '@/shared/api/fetchWithCsrf';

const staleSession = () =>
  new DOMException('認証状態が変更されました。', 'AbortError');

async function protectedRequest(
  execute: (signal: AbortSignal) => Promise<Response>,
  signal?: AbortSignal | null,
): Promise<Response> {
  const started = useAuthStore.getState();
  if (started.sessionExpired) throw staleSession();
  const controller = new AbortController();
  const abort = () => controller.abort();
  if (signal?.aborted) abort();
  signal?.addEventListener('abort', abort, { once: true });
  // 古いセッションの応答で再ログインを取り消さず、継続中の要求も中断する。
  const unsubscribe = useAuthStore.subscribe((state) => {
    if (state.sessionRevision !== started.sessionRevision) abort();
  });
  try {
    const response = await execute(controller.signal);
    const current = useAuthStore.getState();
    if (
      controller.signal.aborted ||
      current.sessionRevision !== started.sessionRevision
    ) {
      throw staleSession();
    }
    if (response.status === 401 && current.isAuthenticated)
      current.expireSession();
    return response;
  } finally {
    unsubscribe();
    signal?.removeEventListener('abort', abort);
  }
}

export function protectedFetch(input: string, init: RequestInit = {}) {
  return protectedRequest(
    (signal) => fetch(input, { ...init, signal }),
    init.signal,
  );
}

export function protectedMutation(input: string, init: RequestInit = {}) {
  return protectedRequest(
    (signal) => fetchWithCsrf(input, { ...init, signal }),
    init.signal,
  );
}
