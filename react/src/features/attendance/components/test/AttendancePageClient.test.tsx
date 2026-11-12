import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, it, vi } from 'vitest';

import * as api from '../../api/attendanceApi';
import type { AttendanceRecord } from '../../types/attendance';
import { AttendancePageClient } from '../AttendancePageClient';

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
  vi.mocked(api.fetchAttendancePage).mockResolvedValue({
    records: [record],
    currentPage: 1,
    lastPage: 1,
  });
});

it('出勤前は出勤ボタンのみ、出勤後は退勤ボタンのみ有効にする', async () => {
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

  await userEvent.click(start);
  await waitFor(() => expect(start).toBeDisabled());
  expect(finish).toBeEnabled();
  expect(api.clockIn).toHaveBeenCalledOnce();
});

it('退勤済みなら両方のボタンを無効にして勤務時間を表示する', async () => {
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

it('勤務が日付をまたいでも出勤した日を勤務日として表示する', async () => {
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

it('勤怠 API の内部エラーの詳細を画面に表示しない', async () => {
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
