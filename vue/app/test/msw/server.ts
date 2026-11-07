import { setupServer } from 'msw/node';

// 既定の応答はテストごとに setup.ts で入れ直すため、ここでは空で作る
export const server = setupServer();
