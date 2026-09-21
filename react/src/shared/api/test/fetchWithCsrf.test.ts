import { afterEach, describe, expect, it, vi } from 'vitest';

import { fetchWithCsrf } from '../fetchWithCsrf';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

describe('fetchWithCsrf', () => {
  afterEach(() => {
    document.cookie = 'XSRF-TOKEN=; Max-Age=0; path=/';
    vi.unstubAllGlobals();
  });

  it('CSRF Cookieをデコードしてリクエストヘッダーに設定すること', async () => {
    document.cookie = 'XSRF-TOKEN=csrf-token%3Dvalue; path=/';

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ message: 'success' }), {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
          },
        }),
      );

    vi.stubGlobal('fetch', fetchMock);

    await fetchWithCsrf('/api/test', {
      method: 'POST',
      body: JSON.stringify({
        name: 'テスト',
      }),
    });

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      `${API_URL}/sanctum/csrf-cookie`,
      {
        credentials: 'include',
      },
    );

    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      `${API_URL}/api/test`,
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        headers: expect.objectContaining({
          Accept: 'application/json',
          'Content-Type': 'application/json',
          'X-XSRF-TOKEN': 'csrf-token=value',
        }),
      }),
    );
  });

  it('CSRF Cookieの取得に失敗した場合、APIリクエストを送信しないこと', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(null, {
        status: 500,
      }),
    );

    vi.stubGlobal('fetch', fetchMock);

    await expect(
      fetchWithCsrf('/api/test', {
        method: 'POST',
      }),
    ).rejects.toThrow('CSRF Cookie の取得に失敗しました。');

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('CSRF Tokenが見つからない場合、APIリクエストを送信しないこと', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(null, {
        status: 204,
      }),
    );

    vi.stubGlobal('fetch', fetchMock);

    await expect(
      fetchWithCsrf('/api/test', {
        method: 'POST',
      }),
    ).rejects.toThrow('CSRF Token が見つかりません。');

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
