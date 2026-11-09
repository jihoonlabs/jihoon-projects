import type { RequestHandler } from 'msw';

import { server } from './server';

/**
 * 現在のテストだけで有効な API 応答を追加・上書きする。
 * 次のテストの開始時には既定の応答に戻る。
 */
export function overrideApi(...handlers: RequestHandler[]): void {
  server.use(...handlers);
}
