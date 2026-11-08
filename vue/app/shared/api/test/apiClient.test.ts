import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { apiUrl } from '~/test/msw/apiUrl';
import { overrideApi } from '~/test/msw/overrideApi';

import { ApiError, createApiClient, useApiClient } from '../apiClient';

const TEST_ORIGIN = 'http://api.test';

describe('API クライアント', () => {
  describe('GET 要求', () => {
    it('接続先 URL にパスを連結し、Cookie 付きで JSON を要求すること', async () => {
      let received: Request | undefined;
      overrideApi(
        http.get(`${TEST_ORIGIN}/api/notices`, ({ request }) => {
          received = request.clone();
          return HttpResponse.json({ data: [] });
        }),
      );

      await createApiClient(TEST_ORIGIN).getJson('/api/notices');

      expect(received?.url).toBe('http://api.test/api/notices');
      expect(received?.credentials).toBe('include');
      expect(received?.headers.get('Accept')).toBe('application/json');
    });

    it('応答の JSON をそのまま返すこと', async () => {
      overrideApi(
        http.get(`${TEST_ORIGIN}/api/notices`, () =>
          HttpResponse.json({ data: [{ id: 1, title: 'お知らせ' }] }),
        ),
      );

      const body = await createApiClient(TEST_ORIGIN).getJson('/api/notices');

      expect(body).toEqual({ data: [{ id: 1, title: 'お知らせ' }] });
    });

    it('接続先 URL の末尾のスラッシュを重ねないこと', async () => {
      let receivedUrl: string | undefined;
      overrideApi(
        http.get(`${TEST_ORIGIN}/api/notices`, ({ request }) => {
          receivedUrl = request.url;
          return HttpResponse.json({ data: [] });
        }),
      );

      const client = createApiClient(`${TEST_ORIGIN}/`);
      await client.getJson('/api/notices');

      expect(client.baseUrl).toBe('http://api.test');
      expect(receivedUrl).toBe('http://api.test/api/notices');
    });
  });

  describe('パスの検証', () => {
    it('"/" で始まらないパスは要求を送らずに拒否すること', async () => {
      let requested = false;
      overrideApi(
        http.get(`${TEST_ORIGIN}/*`, () => {
          requested = true;
          return HttpResponse.json({});
        }),
      );

      await expect(
        createApiClient(TEST_ORIGIN).getJson('api/notices'),
      ).rejects.toThrow('API のパスは "/" から始めてください: api/notices');
      expect(requested).toBe(false);
    });

    it('別のホストを指すプロトコル相対パスは拒否すること', async () => {
      await expect(
        createApiClient(TEST_ORIGIN).getJson('//evil.example/api'),
      ).rejects.toThrow(
        'API のパスは "/" から始めてください: //evil.example/api',
      );
    });
  });

  describe('失敗応答', () => {
    it('HTTP エラーではステータスとエラーコードを持つ ApiError を投げること', async () => {
      overrideApi(
        http.get(`${TEST_ORIGIN}/api/tickets/1`, () =>
          HttpResponse.json(
            { code: 'board_version_conflict', message: '競合しました。' },
            { status: 409 },
          ),
        ),
      );

      const request = createApiClient(TEST_ORIGIN).getJson('/api/tickets/1');

      await expect(request).rejects.toBeInstanceOf(ApiError);
      await expect(request).rejects.toMatchObject({
        message: 'API 要求に失敗しました (409)',
        status: 409,
        code: 'board_version_conflict',
      });
    });

    it('本文が JSON でなくてもステータスを保持し、コードは持たないこと', async () => {
      overrideApi(
        http.get(
          `${TEST_ORIGIN}/api/tickets`,
          () => new HttpResponse('Server Error', { status: 500 }),
        ),
      );

      const request = createApiClient(TEST_ORIGIN).getJson('/api/tickets');

      await expect(request).rejects.toMatchObject({
        status: 500,
        code: undefined,
      });
    });

    it('エラーコードが文字列でなければコードを持たないこと', async () => {
      overrideApi(
        http.get(`${TEST_ORIGIN}/api/tickets`, () =>
          HttpResponse.json({ code: 422 }, { status: 422 }),
        ),
      );

      const request = createApiClient(TEST_ORIGIN).getJson('/api/tickets');

      await expect(request).rejects.toMatchObject({
        status: 422,
        code: undefined,
      });
    });

    it('ネットワークエラーは ApiError に変換せず呼び出し元へ伝えること', async () => {
      overrideApi(
        http.get(`${TEST_ORIGIN}/api/tickets`, () => HttpResponse.error()),
      );

      const request = createApiClient(TEST_ORIGIN).getJson('/api/tickets');

      await expect(request).rejects.toBeInstanceOf(TypeError);
    });
  });

  describe('変更要求', () => {
    it('CSRF Cookie を取得してから、トークンと JSON 本文を付けて送ること', async () => {
      const calls: string[] = [];
      let received: Request | undefined;
      overrideApi(
        http.get(`${TEST_ORIGIN}/sanctum/csrf-cookie`, () => {
          calls.push('csrf');
          document.cookie = 'XSRF-TOKEN=token%3D1; path=/';
          return new HttpResponse(null, { status: 204 });
        }),
        http.post(`${TEST_ORIGIN}/api/tickets`, ({ request }) => {
          calls.push('post');
          received = request.clone();
          return HttpResponse.json({ id: 10 }, { status: 201 });
        }),
      );

      const body = await createApiClient(TEST_ORIGIN).sendJson(
        'POST',
        '/api/tickets',
        { title: '新しいチケット' },
      );

      expect(calls).toEqual(['csrf', 'post']);
      expect(body).toEqual({ id: 10 });
      expect(received?.credentials).toBe('include');
      expect(received?.headers.get('X-XSRF-TOKEN')).toBe('token=1');
      expect(received?.headers.get('Content-Type')).toBe('application/json');
      expect(await received?.json()).toEqual({ title: '新しいチケット' });
    });

    it('本文を渡さないときは本文なしで送ること', async () => {
      let receivedBody: string | undefined;
      overrideApi(
        http.get(`${TEST_ORIGIN}/sanctum/csrf-cookie`, () => {
          document.cookie = 'XSRF-TOKEN=token; path=/';
          return new HttpResponse(null, { status: 204 });
        }),
        http.post(`${TEST_ORIGIN}/api/auth/logout`, async ({ request }) => {
          receivedBody = await request.text();
          return HttpResponse.json({ message: 'ログアウトしました。' });
        }),
      );

      await createApiClient(TEST_ORIGIN).sendJson('POST', '/api/auth/logout');

      expect(receivedBody).toBe('');
    });

    it('本文のない成功応答（204）は undefined を返すこと', async () => {
      overrideApi(
        http.get(`${TEST_ORIGIN}/sanctum/csrf-cookie`, () => {
          document.cookie = 'XSRF-TOKEN=token; path=/';
          return new HttpResponse(null, { status: 204 });
        }),
        http.delete(
          `${TEST_ORIGIN}/api/tickets/1`,
          () => new HttpResponse(null, { status: 204 }),
        ),
      );

      const body = await createApiClient(TEST_ORIGIN).sendJson(
        'DELETE',
        '/api/tickets/1',
      );

      expect(body).toBeUndefined();
    });

    it('CSRF Cookie の取得に失敗したら、変更要求を送らずに失敗すること', async () => {
      let posted = false;
      overrideApi(
        http.get(
          `${TEST_ORIGIN}/sanctum/csrf-cookie`,
          () => new HttpResponse(null, { status: 500 }),
        ),
        http.post(`${TEST_ORIGIN}/api/tickets`, () => {
          posted = true;
          return HttpResponse.json({});
        }),
      );

      await expect(
        createApiClient(TEST_ORIGIN).sendJson('POST', '/api/tickets', {}),
      ).rejects.toThrow('CSRF Cookie の取得に失敗しました。');
      expect(posted).toBe(false);
    });

    it('CSRF トークンの Cookie がなければ、変更要求を送らずに失敗すること', async () => {
      let posted = false;
      overrideApi(
        http.get(
          `${TEST_ORIGIN}/sanctum/csrf-cookie`,
          () => new HttpResponse(null, { status: 204 }),
        ),
        http.post(`${TEST_ORIGIN}/api/tickets`, () => {
          posted = true;
          return HttpResponse.json({});
        }),
      );

      await expect(
        createApiClient(TEST_ORIGIN).sendJson('POST', '/api/tickets', {}),
      ).rejects.toThrow('CSRF Token が見つかりません。');
      expect(posted).toBe(false);
    });

    it('入力エラー（422）の項目別メッセージとサーバーのメッセージを保持すること', async () => {
      overrideApi(
        http.get(`${TEST_ORIGIN}/sanctum/csrf-cookie`, () => {
          document.cookie = 'XSRF-TOKEN=token; path=/';
          return new HttpResponse(null, { status: 204 });
        }),
        http.post(`${TEST_ORIGIN}/api/auth/login`, () =>
          HttpResponse.json(
            {
              message: '入力内容を確認してください。',
              errors: {
                email: ['メールアドレス及びパスワードが違います。'],
                password: [123],
              },
            },
            { status: 422 },
          ),
        ),
      );

      const request = createApiClient(TEST_ORIGIN).sendJson(
        'POST',
        '/api/auth/login',
        {},
      );

      await expect(request).rejects.toMatchObject({
        status: 422,
        serverMessage: '入力内容を確認してください。',
        fieldErrors: {
          email: ['メールアドレス及びパスワードが違います。'],
          password: [],
        },
      });
    });
  });

  describe('中断', () => {
    it('中断済みの信号を渡すと AbortError で終わること', async () => {
      overrideApi(
        http.get(`${TEST_ORIGIN}/api/tickets`, () =>
          HttpResponse.json({ data: [] }),
        ),
      );
      const controller = new AbortController();
      controller.abort();

      const request = createApiClient(TEST_ORIGIN).getJson('/api/tickets', {
        signal: controller.signal,
      });

      await expect(request).rejects.toMatchObject({ name: 'AbortError' });
    });
  });

  describe('useApiClient', () => {
    it('runtimeConfig の接続先へ要求すること', async () => {
      overrideApi(
        http.get(apiUrl('/api/notices'), () =>
          HttpResponse.json({ data: ['runtime'] }),
        ),
      );

      const client = useApiClient();
      const body = await client.getJson('/api/notices');

      expect(client.baseUrl).toBe('http://localhost:8000');
      expect(body).toEqual({ data: ['runtime'] });
    });
  });
});
