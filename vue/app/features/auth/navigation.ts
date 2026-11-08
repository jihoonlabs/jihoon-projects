import { useRuntimeConfig } from '#imports';

import type { SocialProvider } from './types';

export const LOGIN_PATH = '/login';

/**
 * ログイン後に開く画面。公開デモでは勤怠機能を使わないためチケット画面にする。
 */
export function homePathFor(demoMode: boolean): string {
  return demoMode ? '/tickets' : '/attendance';
}

export function useHomePath(): string {
  return homePathFor(useRuntimeConfig().public.demoMode === true);
}

/**
 * Laravel のソーシャルログイン開始 URL。完了後に Vue 版へ戻るよう client=vue を付ける。
 */
export function socialLoginUrl(apiUrl: string, provider: SocialProvider) {
  const origin = apiUrl.replace(/\/+$/, '');

  return `${origin}/api/auth/${provider}/redirect?client=vue`;
}
