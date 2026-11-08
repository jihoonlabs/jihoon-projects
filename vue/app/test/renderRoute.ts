import { useRouter } from '#imports';
import { waitFor } from '@testing-library/vue';
import { expect } from 'vitest';

import App from '~/app.vue';

import { renderScreen } from './renderScreen';

/**
 * アプリ全体（レイアウト・ルートミドルウェアを含む）を指定した URL で描画する
 */
export async function renderRoute(path: string) {
  const view = await renderScreen(App, { route: path });
  const router = useRouter();

  return {
    ...view,
    router,
    currentPath: () => router.currentRoute.value.fullPath,
  };
}

/**
 * 画面遷移（リダイレクトを含む）が指定した URL に落ち着くまで待つ
 */
export async function expectPath(path: string) {
  const router = useRouter();

  await waitFor(() => {
    expect(router.currentRoute.value.fullPath).toBe(path);
  });
}
