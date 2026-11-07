import { setupServer, type SetupServerApi } from 'msw/node';

const SERVER_KEY = Symbol.for('vue-client.test.msw-server');

type ServerHolder = { [SERVER_KEY]?: SetupServerApi };

const holder = globalThis as ServerHolder;

/**
 * テスト実行中に 1 つだけ存在する MSW サーバー。
 * Nuxt のテスト環境では setup ファイルとテストファイルが別のモジュールとして読み込まれることがあるため、
 * globalThis に保持して、応答の上書きが必ず待ち受け中のサーバーに登録されるようにする。
 * 既定の応答はテストごとに setup.ts で入れ直すため、ここでは空で作る。
 */
export const server: SetupServerApi = (holder[SERVER_KEY] ??= setupServer());
