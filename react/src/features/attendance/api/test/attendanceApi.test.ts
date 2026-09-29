import { http, HttpResponse } from 'msw';
import { expect, it } from 'vitest';

import { server } from '@/test/mocks/server';

import {
  AttendanceApiError,
  clockIn,
  clockOut,
  fetchAttendancePage,
  fetchAttendanceToday,
} from '../attendanceApi';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

const record = {
  id: 3,
  work_date: '2026-09-29',
  clock_in_at: '2026-09-29T00:00:00+00:00',
  clock_out_at: null,
  duration_minutes: null,
};

it("loads today's state and only the authenticated user's paginated records", async () => {
  server.use(
    http.get(`${API_URL}/api/attendance/today`, () =>
      HttpResponse.json({
        data: {
          date: '2026-09-29',
          timezone: 'Asia/Tokyo',
          status: 'working',
          record,
        },
      }),
    ),
    http.get(`${API_URL}/api/attendance`, ({ request }) => {
      expect(new URL(request.url).searchParams.get('page')).toBe('2');
      return HttpResponse.json({
        data: [record],
        meta: { current_page: 2, last_page: 3 },
      });
    }),
  );

  expect(await fetchAttendanceToday()).toMatchObject({
    status: 'working',
    record: { workDate: '2026-09-29', clockOutAt: null },
  });
  expect(await fetchAttendancePage(2)).toMatchObject({
    currentPage: 2,
    lastPage: 3,
    records: [{ id: 3, workDate: '2026-09-29' }],
  });
});

it('uses the existing CSRF flow for clock actions and surfaces conflicts', async () => {
  server.use(
    http.post(`${API_URL}/api/attendance/clock-in`, ({ request }) => {
      expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
      return HttpResponse.json({ data: record }, { status: 201 });
    }),
    http.post(`${API_URL}/api/attendance/clock-out`, () =>
      HttpResponse.json(
        { message: '退勤できる出勤記録がありません。', code: 'not_working' },
        { status: 409 },
      ),
    ),
  );

  expect(await clockIn()).toMatchObject({ id: 3, workDate: '2026-09-29' });
  await expect(clockOut()).rejects.toMatchObject({
    name: 'AttendanceApiError',
    status: 409,
    code: 'not_working',
  } satisfies Partial<AttendanceApiError>);
});
