import { useRuntimeConfig } from '#imports';

/**
 * テストでもアプリと同じ runtimeConfig の接続先から API の URL を組み立てる。
 */
export function apiUrl(path: string): string {
  const base = useRuntimeConfig().public.apiUrl.replace(/\/+$/, '');

  return `${base}${path}`;
}
