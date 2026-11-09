import { renderSuspended } from '@nuxt/test-utils/runtime';
import { userEvent } from '@testing-library/user-event';

type RenderArgs = Parameters<typeof renderSuspended>;

/**
 * Nuxt の実行環境で画面を描画し、利用者操作用の user を一緒に返す。
 * 画面ごとの準備（ログイン状態・初期データ）は各機能の render 関数でこれを包む。
 */
export async function renderScreen(
  component: RenderArgs[0],
  options?: RenderArgs[1],
) {
  const user = userEvent.setup();
  const view = await renderSuspended(component, options);

  return { user, ...view };
}
