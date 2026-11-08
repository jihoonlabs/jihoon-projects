import { useAuthStore } from '~/features/auth/stores/authStore';

/**
 * テストごとにアプリの状態（Pinia ストア）を初期状態へ戻す。
 * ストアを追加したら、ここで一緒に初期化する。
 */
export function resetAppState(): void {
  useAuthStore().reset();
}
