import { http, HttpResponse } from 'msw';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export const handlers = [
  http.get(`${API_URL}/sanctum/csrf-cookie`, () => {
    document.cookie = 'XSRF-TOKEN=test-csrf-token; path=/';

    return new HttpResponse(null, { status: 204 });
  }),
];
