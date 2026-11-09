import { useRuntimeConfig } from '#imports';
import { onTestFinished } from 'vitest';

/**
 * 現在のテストだけ公開デモとして動かす。テスト終了時に元の設定へ戻す。
 */
export function enableDemoMode(): void {
  const config = useRuntimeConfig().public;
  const original = config.demoMode;

  config.demoMode = true;
  onTestFinished(() => {
    config.demoMode = original;
  });
}
