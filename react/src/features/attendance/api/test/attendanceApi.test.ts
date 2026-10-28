import { http, HttpResponse } from 'msw';
import { expect, it } from 'vitest';

import { server } from '@/test/mocks/server';

import {
  AttendanceApiError,
  clockIn,
  clockOut,
  fetchAttendancePage,
  fetchAttendanceSchedule,
  fetchAttendanceScheduleUsers,
  fetchAttendanceToday,
  saveAttendanceSchedule,
} from '../attendanceApi';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

const record = {
  id: 3,
  work_date: '2026-10-20',
  clock_in_at: '2026-10-20T00:00:00+00:00',
  clock_out_at: null,
  duration_minutes: null,
};

it("loads today's state and the authenticated user's paginated records", async () => {
  server.use(
    http.get(`${API_URL}/api/attendance/today`, () =>
      HttpResponse.json({
        data: {
          date: '2026-10-20',
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
    record: { workDate: '2026-10-20', clockOutAt: null },
  });
  expect(await fetchAttendancePage(2)).toMatchObject({
    currentPage: 2,
    lastPage: 3,
    records: [{ id: 3, workDate: '2026-10-20' }],
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

  expect(await clockIn()).toMatchObject({ id: 3, workDate: '2026-10-20' });
  await expect(clockOut()).rejects.toMatchObject({
    name: 'AttendanceApiError',
    status: 409,
    code: 'not_working',
    message: '退勤できる出勤記録がありません。',
  } satisfies Partial<AttendanceApiError>);
});

it('hides server debug details from internal errors', async () => {
  server.use(
    http.get(`${API_URL}/api/attendance/today`, () =>
      HttpResponse.json(
        {
          message:
            'SQLSTATE[HY000]: no such table: attendance_records at /Users/example/app/database.sqlite',
        },
        { status: 500 },
      ),
    ),
  );

  await expect(fetchAttendanceToday()).rejects.toMatchObject({
    name: 'AttendanceApiError',
    status: 500,
    message: '勤怠を処理できませんでした。時間をおいて再度お試しください。',
  });
});

it('loads and saves a recurring schedule without treating planned breaks as actual breaks', async () => {
  const saved = {
    id: 8,
    effective_from: '2026-10-20',
    weekdays: [1, 2, 3, 4, 5],
    start_time: '09:00',
    end_time: '18:00',
    planned_break_minutes: 60,
  };
  server.use(
    http.get(`${API_URL}/api/attendance/schedule?user_id=7`, () =>
      HttpResponse.json({
        data: {
          date: '2026-10-20',
          timezone: 'Asia/Tokyo',
          current: saved,
          upcoming: null,
        },
      }),
    ),
    http.get(`${API_URL}/api/attendance/schedule-users`, () =>
      HttpResponse.json({ data: [{ id: 7, name: 'Employee' }] }),
    ),
    http.put(`${API_URL}/api/attendance/schedule`, async ({ request }) => {
      expect(await request.json()).toEqual({
        user_id: 7,
        effective_from: '2026-10-20',
        weekdays: [1, 2, 3, 4, 5],
        start_time: '09:00',
        end_time: '18:00',
        planned_break_minutes: 60,
      });
      return HttpResponse.json({ data: saved });
    }),
  );

  expect(await fetchAttendanceSchedule(7)).toMatchObject({
    date: '2026-10-20',
    current: {
      effectiveFrom: '2026-10-20',
      weekdays: [1, 2, 3, 4, 5],
      plannedBreakMinutes: 60,
    },
    upcoming: null,
  });
  expect(
    await saveAttendanceSchedule(7, {
      effectiveFrom: '2026-10-20',
      weekdays: [1, 2, 3, 4, 5],
      startTime: '09:00',
      endTime: '18:00',
      plannedBreakMinutes: 60,
    }),
  ).toMatchObject({ startTime: '09:00', plannedBreakMinutes: 60 });
  await expect(fetchAttendanceScheduleUsers()).resolves.toEqual([
    { id: 7, name: 'Employee' },
  ]);
});
