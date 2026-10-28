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
    startBreak: vi.fn(),
    endBreak: vi.fn(),
  };
});

const record: AttendanceRecord = {
  id: 1,
  workDate: '2026-10-20',
  clockInAt: '2026-10-20T00:00:00+00:00',
  clockOutAt: null,
  breaks: [],
  breakDurationMinutes: 0,
  durationSeconds: null,
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

it('records break start and end, changes available actions, and shows break duration', async () => {
  vi.mocked(api.fetchAttendanceToday)
    .mockResolvedValueOnce({
      date: '2026-10-20',
      timezone: 'Asia/Tokyo',
      status: 'working',
      record,
    })
    .mockResolvedValueOnce({
      date: '2026-10-20',
      timezone: 'Asia/Tokyo',
      status: 'on_break',
      record: {
        ...record,
        breaks: [{ id: 1, startedAt: '2026-10-20T12:00:00+00:00', endedAt: null }],
      },
    })
    .mockResolvedValue({
      date: '2026-10-20',
      timezone: 'Asia/Tokyo',
      status: 'working',
      record: {
        ...record,
        breaks: [
          {
            id: 1,
            startedAt: '2026-10-20T12:00:00+00:00',
            endedAt: '2026-10-20T12:30:00+00:00',
          },
        ],
        breakDurationMinutes: 30,
      },
    });
  vi.mocked(api.fetchAttendancePage).mockResolvedValue({
    records: [{ ...record, breakDurationMinutes: 30 }],
    currentPage: 1,
    lastPage: 1,
  });

  render(<AttendancePageClient />);
  const start = await screen.findByRole('button', { name: '休憩開始' });
  const end = screen.getByRole('button', { name: '休憩終了' });
  const checkout = screen.getByRole('button', { name: '退勤' });

  expect(start).toBeEnabled();
  expect(end).toBeDisabled();
  expect(checkout).toBeEnabled();

  await userEvent.click(start);
  await waitFor(() => expect(api.startBreak).toHaveBeenCalledOnce());
  await waitFor(() => expect(end).toBeEnabled());
  expect(start).toBeDisabled();
  expect(checkout).toBeDisabled();
  expect(screen.getByText(/休憩開始:/)).toBeInTheDocument();

  await userEvent.click(end);
  await waitFor(() => expect(api.endBreak).toHaveBeenCalledOnce());
  await waitFor(() => expect(start).toBeEnabled());
  expect(end).toBeDisabled();
  expect(checkout).toBeEnabled();
  expect(screen.getByText('30分')).toBeInTheDocument();
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
