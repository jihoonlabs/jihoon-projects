import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { apiUrl } from '../apiUrl';
import { overrideApi } from '../overrideApi';

describe('テスト用 API 応答', () => {
  describe('既定の応答', () => {
    it('CSRF Cookie の発行要求に 204 を返し、XSRF-TOKEN を設定すること', async () => {
      const response = await fetch(apiUrl('/sanctum/csrf-cookie'));

      expect(response.status).toBe(204);
      expect(document.cookie).toContain('XSRF-TOKEN=test-csrf-token');
    });
  });

  describe('既定のセッション', () => {
    it('セッション確認には未ログイン（401）を返すこと', async () => {
      const response = await fetch(apiUrl('/api/auth/me'));

      expect(response.status).toBe(401);
    });
  });

  describe('未定義の要求', () => {
    it('応答を定義していない API 要求は失敗させること', async () => {
      await expect(fetch(apiUrl('/api/undefined-endpoint'))).rejects.toThrow();
    });
  });

  // 同じファイル内のテストは定義順に実行される。上書きが次のテストへ残らないことを順に確認する。
  describe('テスト間の分離', () => {
    it('上書きした応答は、そのテストの中で使われること', async () => {
      overrideApi(
        http.get(apiUrl('/api/isolation-probe'), () =>
          HttpResponse.json({ data: 'overridden' }),
        ),
      );

      const response = await fetch(apiUrl('/api/isolation-probe'));

      expect(await response.json()).toEqual({ data: 'overridden' });
    });

    it('前のテストの上書きは次のテストに残らないこと', async () => {
      await expect(fetch(apiUrl('/api/isolation-probe'))).rejects.toThrow();
    });

    it('前のテストで設定された Cookie は次のテストに残らないこと', () => {
      expect(document.cookie).not.toContain('XSRF-TOKEN');
    });
  });
});
