const API_URL = 'http://localhost:8000';

const getCookie = (name: string): string | null => {
  const cookies = document.cookie.split('; ');

  for (const cookie of cookies) {
    const [key, value] = cookie.split('=');

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
  await fetch(`${API_URL}/sanctum/csrf-cookie`, {
    credentials: 'include',
  });

  const xsrfToken = getCookie('XSRF-TOKEN');

  return fetch(`${API_URL}${input}`, {
    ...init,
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      'X-XSRF-TOKEN': xsrfToken ?? '',
      ...init.headers,
    },
  });
};