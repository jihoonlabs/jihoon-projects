const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

const getCookie = (name: string): string | null => {
  const cookies = document.cookie.split('; ');

  for (const cookie of cookies) {
    const separatorIndex = cookie.indexOf('=');

    if (separatorIndex === -1) {
      continue;
    }

    const key = cookie.slice(0, separatorIndex);
    const value = cookie.slice(separatorIndex + 1);

    if (key === name) {
      return decodeURIComponent(value);
    }
  }

  return null;
};

export const fetchWithCsrf = async (
  input: string,
  init: RequestInit = {},
): Promise<Response> => {
  // Sanctum の CSRF Cookie を取得
  const csrfResponse = await fetch(`${API_URL}/sanctum/csrf-cookie`, {
    credentials: 'include',
  });

  if (!csrfResponse.ok) {
    throw new Error('CSRF Cookie の取得に失敗しました。');
  }

  const xsrfToken = getCookie('XSRF-TOKEN');

  if (!xsrfToken) {
    throw new Error('CSRF Token が見つかりません。');
  }

  return fetch(`${API_URL}${input}`, {
    ...init,
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      'X-XSRF-TOKEN': xsrfToken,
      ...init.headers,
    },
  });
};
