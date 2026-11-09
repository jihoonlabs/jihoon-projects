import { useRuntimeConfig } from '#imports';

export type FieldErrors = Record<string, string[]>;

/**
 * Laravel API の失敗応答。HTTP ステータスと、応答本文にあればエラーコード・メッセージ・入力エラーを保持する。
 */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
    readonly serverMessage?: string,
    readonly fieldErrors: FieldErrors = {},
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export interface ApiRequestOptions {
  signal?: AbortSignal;
}

export type MutationMethod = 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface ApiClient {
  readonly baseUrl: string;
  getJson<T>(path: string, options?: ApiRequestOptions): Promise<T>;
  sendJson<T>(
    method: MutationMethod,
    path: string,
    body?: unknown,
    options?: ApiRequestOptions,
  ): Promise<T>;
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const readFieldErrors = (value: unknown): FieldErrors => {
  if (!isRecord(value)) {
    return {};
  }

  return Object.fromEntries(
    Object.entries(value)
      .filter((entry): entry is [string, unknown[]] => Array.isArray(entry[1]))
      .map(([field, messages]) => [
        field,
        messages.filter(
          (message): message is string => typeof message === 'string',
        ),
      ]),
  );
};

const toApiError = async (response: Response): Promise<ApiError> => {
  const body: unknown = await response.json().catch(() => null);
  const details = isRecord(body) ? body : {};

  return new ApiError(
    `API 要求に失敗しました (${response.status})`,
    response.status,
    typeof details.code === 'string' ? details.code : undefined,
    typeof details.message === 'string' ? details.message : undefined,
    readFieldErrors(details.errors),
  );
};

const readCookie = (name: string): string | null => {
  const prefix = `${name}=`;
  const cookie = document.cookie
    .split('; ')
    .find((entry) => entry.startsWith(prefix));

  return cookie ? decodeURIComponent(cookie.slice(prefix.length)) : null;
};

/**
 * 接続先 URL を固定した API クライアントを作る。
 * Sanctum のセッション Cookie を送るため、常に credentials: 'include' で要求する。
 */
export function createApiClient(baseUrl: string): ApiClient {
  const origin = baseUrl.replace(/\/+$/, '');

  const toUrl = (path: string) => {
    // 相対パス以外を受け付けると、意図しない外部 URL へ Cookie を送るおそれがある
    if (!path.startsWith('/') || path.startsWith('//')) {
      throw new Error(`API のパスは "/" から始めてください: ${path}`);
    }

    return `${origin}${path}`;
  };

  const readJson = async <T>(response: Response): Promise<T> => {
    if (!response.ok) {
      throw await toApiError(response);
    }

    // 本文のない成功応答（204 など）は undefined として扱う
    if (response.status === 204) {
      return undefined as T;
    }

    return (await response.json()) as T;
  };

  // 変更要求の前に Sanctum の CSRF Cookie を受け取り、ヘッダーで送り返す
  const fetchCsrfToken = async (signal?: AbortSignal) => {
    const response = await fetch(toUrl('/sanctum/csrf-cookie'), {
      credentials: 'include',
      signal,
    });

    if (!response.ok) {
      throw new Error('CSRF Cookie の取得に失敗しました。');
    }

    const token = readCookie('XSRF-TOKEN');

    if (!token) {
      throw new Error('CSRF Token が見つかりません。');
    }

    return token;
  };

  return {
    baseUrl: origin,

    async getJson<T>(path: string, { signal }: ApiRequestOptions = {}) {
      const url = toUrl(path);
      const response = await fetch(url, {
        credentials: 'include',
        headers: { Accept: 'application/json' },
        signal,
      });

      return readJson<T>(response);
    },

    async sendJson<T>(
      method: MutationMethod,
      path: string,
      body?: unknown,
      { signal }: ApiRequestOptions = {},
    ) {
      const url = toUrl(path);
      const token = await fetchCsrfToken(signal);
      const response = await fetch(url, {
        method,
        credentials: 'include',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
          'X-XSRF-TOKEN': token,
        },
        body: body === undefined ? undefined : JSON.stringify(body),
        signal,
      });

      return readJson<T>(response);
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
