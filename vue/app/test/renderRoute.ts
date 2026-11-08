import { useRouter } from '#imports';
import { waitFor } from '@testing-library/vue';
import { expect } from 'vitest';

import App from '~/app.vue';

import { renderScreen } from './renderScreen';

/**
 * アプリ全体（レイアウト・ルートミドルウェアを含む）を指定した URL で描画する。
 * ルーターはテストファイル内で共有されるため、前のテストと同じ URL でも遷移とミドルウェアを必ず実行する。
 */
export async function renderRoute(path: string) {
  const router = useRouter();
  const target = router.resolve(path);
  const view = await renderScreen(App, {
    route: {
      path: target.path,
      query: target.query,
      hash: target.hash,
      force: true,
    },
  });

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
