import { setupServer } from 'msw/node';

type TestServer = ReturnType<typeof setupServer>;

const SERVER_KEY = Symbol.for('vue-client.test.msw-server');

type ServerHolder = { [SERVER_KEY]?: TestServer };

const holder = globalThis as ServerHolder;

/**
 * テスト実行中に 1 つだけ存在する MSW サーバー。
 * setup ファイルとテストファイルの読み込み経路が違っても同じインスタンスを使うよう globalThis に保持し、
 * 応答の上書きが必ず待ち受け中のサーバーに登録されるようにする。
 * 既定の応答はテストごとに setup.ts で入れ直すため、ここでは空で作る。
 */
export const server: TestServer = (holder[SERVER_KEY] ??= setupServer());
