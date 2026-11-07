import { useRuntimeConfig } from '#imports';

/**
 * Laravel API の失敗応答。HTTP ステータスと、応答本文にあればエラーコードを保持する。
 */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export interface ApiRequestOptions {
  signal?: AbortSignal;
}

export interface ApiClient {
  readonly baseUrl: string;
  getJson<T>(path: string, options?: ApiRequestOptions): Promise<T>;
}

const readErrorCode = async (
  response: Response,
): Promise<string | undefined> => {
  const body: unknown = await response.json().catch(() => null);

  if (body && typeof body === 'object' && 'code' in body) {
    const { code } = body;
    return typeof code === 'string' ? code : undefined;
  }

  return undefined;
};

/**
 * 接続先 URL を固定した API クライアントを作る。
 * Sanctum のセッション Cookie を送るため、常に credentials: 'include' で要求する。
 */
export function createApiClient(baseUrl: string): ApiClient {
  const origin = baseUrl.replace(/\/+$/, '');

  return {
    baseUrl: origin,

    async getJson<T>(path: string, { signal }: ApiRequestOptions = {}) {
      // 相対パス以外を受け付けると、意図しない外部 URL へ Cookie を送るおそれがある
      if (!path.startsWith('/') || path.startsWith('//')) {
        throw new Error(`API のパスは "/" から始めてください: ${path}`);
      }

      const response = await fetch(`${origin}${path}`, {
        credentials: 'include',
        headers: { Accept: 'application/json' },
        signal,
      });

      if (!response.ok) {
        throw new ApiError(
          `API 要求に失敗しました (${response.status})`,
          response.status,
          await readErrorCode(response),
        );
      }

      return (await response.json()) as T;
    },
  };
}

/**
 * runtimeConfig の接続先を使う API クライアント。画面やストアはこれを経由する。
 */
export function useApiClient(): ApiClient {
  const config = useRuntimeConfig();

  return createApiClient(config.public.apiUrl);
}
