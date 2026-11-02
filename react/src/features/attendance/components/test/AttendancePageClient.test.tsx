import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

import * as api from '../../api/attendanceApi';
import type { AttendanceRecord } from '../../types/attendance';
import {
  AttendancePageClient,
  isClockInAllowedAt,
} from '../AttendancePageClient';

vi.mock('../../api/attendanceApi', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('../../api/attendanceApi')>();

  return {
    ...actual,
    fetchAttendanceToday: vi.fn(),
    fetchAttendancePage: vi.fn(),
    clockIn: vi.fn(),
    clockOut: vi.fn(),
  };
});

const record: AttendanceRecord = {
  id: 1,
  workDate: '2026-10-20',
  clockInAt: '2026-10-20T00:00:00+00:00',
  clockOutAt: null,
  durationMinutes: null,
};

beforeEach(() => {
  vi.resetAllMocks();
  vi.spyOn(Date, 'now').mockReturnValue(
    new Date('2026-10-20T01:00:00Z').getTime(),
  );
  vi.mocked(api.fetchAttendancePage).mockResolvedValue({
    records: [record],
    currentPage: 1,
    lastPage: 1,
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

it('allows clock-in from exactly 06:00 in Japan time', () => {
  expect(isClockInAllowedAt(new Date('2026-10-20T20:59:59Z'))).toBe(false);
  expect(isClockInAllowedAt(new Date('2026-10-20T21:00:00Z'))).toBe(true);
});

it('disables clock-in and explains the opening time before 06:00', async () => {
  vi.spyOn(Date, 'now').mockReturnValue(
    new Date('2026-10-20T20:59:59Z').getTime(),
  );
  vi.mocked(api.fetchAttendanceToday).mockResolvedValue({
    date: '2026-10-21',
    timezone: 'Asia/Tokyo',
    status: 'not_started',
    record: null,
  });

  render(<AttendancePageClient />);

  expect(
    await screen.findByText('出勤受付は日本時間06:00に開始します。'),
  ).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '出勤' })).toBeDisabled();
});

it('enables only clock-in before work, then only clock-out after recording it', async () => {
  vi.mocked(api.fetchAttendanceToday)
    .mockResolvedValueOnce({
      date: '2026-10-20',
      timezone: 'Asia/Tokyo',
      status: 'not_started',
      record: null,
    })
    .mockResolvedValue({
      date: '2026-10-20',
      timezone: 'Asia/Tokyo',
      status: 'working',
      record,
    });
  vi.mocked(api.clockIn).mockResolvedValue(record);

  render(<AttendancePageClient />);
  const start = await screen.findByRole('button', { name: '出勤' });
  const finish = screen.getByRole('button', { name: '退勤' });
  await waitFor(() => expect(start).toBeEnabled());
  expect(finish).toBeDisabled();
  expect(
    screen.getByText('出勤は日本時間06:00から記録できます。'),
  ).toBeInTheDocument();

  await userEvent.click(start);
  await waitFor(() => expect(start).toBeDisabled());
  expect(finish).toBeEnabled();
  expect(api.clockIn).toHaveBeenCalledOnce();
});

it('disables both buttons after checkout and displays elapsed duration', async () => {
  vi.mocked(api.fetchAttendanceToday).mockResolvedValue({
    date: '2026-10-20',
    timezone: 'Asia/Tokyo',
    status: 'finished',
    record: {
      ...record,
      clockOutAt: '2026-10-20T01:31:00+00:00',
      durationMinutes: 91,
    },
  });
  vi.mocked(api.fetchAttendancePage).mockResolvedValue({
    records: [
      {
        ...record,
        clockOutAt: '2026-10-20T01:31:00+00:00',
        durationMinutes: 91,
      },
    ],
    currentPage: 1,
    lastPage: 1,
  });

  render(<AttendancePageClient />);
  await screen.findByText('退勤済み');
  expect(screen.getByRole('button', { name: '出勤' })).toBeDisabled();
  expect(screen.getByRole('button', { name: '退勤' })).toBeDisabled();
  expect(screen.getByText('1時間31分')).toBeInTheDocument();
});

it('keeps the original work date visible while an overnight shift is active', async () => {
  vi.mocked(api.fetchAttendanceToday).mockResolvedValue({
    date: '2026-10-21',
    timezone: 'Asia/Tokyo',
    status: 'working',
    record: {
      ...record,
      workDate: '2026-10-20',
    },
  });

  render(<AttendancePageClient />);
  await screen.findByText('勤務中');

  expect(
    screen.getByText('勤務日: 2026-10-20（日付をまたいで勤務中）'),
  ).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '出勤' })).toBeDisabled();
  expect(screen.getByRole('button', { name: '退勤' })).toBeEnabled();
});

it('does not display internal error details from the attendance API', async () => {
  vi.mocked(api.fetchAttendanceToday).mockRejectedValue(
    new Error('SQLSTATE[HY000] /Users/example/app/database/database.sqlite'),
  );

  render(<AttendancePageClient />);

  const alert = await screen.findByRole('alert');
  expect(alert).toHaveTextContent(
    '勤怠を処理できませんでした。時間をおいて再度お試しください。',
  );
  expect(alert).not.toHaveTextContent('SQLSTATE');
  expect(alert).not.toHaveTextContent('/Users/example');
});
