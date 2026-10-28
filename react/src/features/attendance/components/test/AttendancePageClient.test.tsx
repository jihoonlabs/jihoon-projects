import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, it, vi } from 'vitest';

import * as api from '../../api/attendanceApi';
import type { AttendanceRecord } from '../../types/attendance';
import { useAuthStore } from '@/features/auth/store/useAuthStore';

import { AttendancePageClient } from '../AttendancePageClient';

vi.mock('../../api/attendanceApi', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('../../api/attendanceApi')>();

  return {
    ...actual,
    fetchAttendanceToday: vi.fn(),
    fetchAttendancePage: vi.fn(),
    fetchAttendanceSchedule: vi.fn(),
    fetchAttendanceScheduleUsers: vi.fn(),
    clockIn: vi.fn(),
    clockOut: vi.fn(),
    startBreak: vi.fn(),
    endBreak: vi.fn(),
    saveAttendanceSchedule: vi.fn(),
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
  useAuthStore.setState({
    user: {
      id: 1,
      name: 'Employee',
      email: 'employee@example.com',
      role: 'user',
      attendanceRole: 'employee',
      status: 'active',
      createdAt: '2026-10-20T00:00:00Z',
    },
  });
  vi.mocked(api.fetchAttendanceScheduleUsers).mockResolvedValue([
    { id: 7, name: 'Employee' },
  ]);
  vi.mocked(api.fetchAttendancePage).mockResolvedValue({
    records: [record],
    currentPage: 1,
    lastPage: 1,
  });
  vi.mocked(api.fetchAttendanceSchedule).mockResolvedValue({
    date: '2026-10-20',
    timezone: 'Asia/Tokyo',
    current: null,
    upcoming: null,
  });
  vi.mocked(api.saveAttendanceSchedule).mockResolvedValue({
    id: 4,
    effectiveFrom: '2026-10-20',
    weekdays: [1, 2, 3, 4, 5],
    startTime: '09:00',
    endTime: '18:00',
    plannedBreakMinutes: 60,
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
        breaks: [
          { id: 1, startedAt: '2026-10-20T12:00:00+00:00', endedAt: null },
        ],
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
  expect(screen.getByText('0時間30分')).toBeInTheDocument();
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

it('lets attendance admins save an employee schedule without changing punch data', async () => {
  useAuthStore.setState({
    user: {
      id: 2,
      name: 'Attendance Admin',
      email: 'admin@example.com',
      role: 'user',
      attendanceRole: 'admin',
      status: 'active',
      createdAt: '2026-10-20T00:00:00Z',
    },
  });
  vi.mocked(api.fetchAttendanceToday).mockResolvedValue({
    date: '2026-10-20',
    timezone: 'Asia/Tokyo',
    status: 'not_started',
    record: null,
  });

  render(<AttendancePageClient />);
  const save = await screen.findByRole('button', { name: '従業員の予定を保存' });
  expect(
    screen.getByText(/実際の休憩記録と分けて保管/),
  ).toBeInTheDocument();
  expect(save).toBeDisabled();

  fireEvent.change(screen.getByLabelText('適用開始日'), {
    target: { value: '2026-10-20' },
  });
  await userEvent.click(screen.getByRole('checkbox', { name: '月' }));
  fireEvent.change(screen.getByLabelText('開始時刻'), {
    target: { value: '09:00' },
  });
  fireEvent.change(screen.getByLabelText('終了時刻'), {
    target: { value: '18:00' },
  });
  fireEvent.change(screen.getByLabelText('予定休憩（分）'), {
    target: { value: '60' },
  });

  expect(save).toBeEnabled();
  await userEvent.click(save);

  await waitFor(() =>
    expect(api.saveAttendanceSchedule).toHaveBeenCalledWith(7, {
      effectiveFrom: '2026-10-20',
      weekdays: [1],
      startTime: '09:00',
      endTime: '18:00',
      plannedBreakMinutes: 60,
    }),
  );
});

it('keeps employee schedule controls read-only', async () => {
  vi.mocked(api.fetchAttendanceToday).mockResolvedValue({
    date: '2026-10-20',
    timezone: 'Asia/Tokyo',
    status: 'not_started',
    record: null,
  });

  render(<AttendancePageClient />);

  expect(await screen.findByText('予定勤務の設定・変更は出勤管理者が行います。')).toBeInTheDocument();
  expect(screen.queryByLabelText('適用開始日')).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '従業員の予定を保存' })).not.toBeInTheDocument();
  expect(api.fetchAttendanceScheduleUsers).not.toHaveBeenCalled();
});

it('keeps clock actions available when schedule loading fails', async () => {
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
  vi.mocked(api.fetchAttendanceSchedule).mockRejectedValue(
    new Error('SQLSTATE[HY000]'),
  );
  vi.mocked(api.clockIn).mockResolvedValue(record);

  render(<AttendancePageClient />);

  const clockIn = await screen.findByRole('button', { name: '出勤' });
  expect(await screen.findByRole('alert')).toHaveTextContent(
    '勤怠を処理できませんでした。時間をおいて再度お試しください。',
  );
  expect(clockIn).toBeEnabled();

  await userEvent.click(clockIn);
  await waitFor(() => expect(api.clockIn).toHaveBeenCalledOnce());
});
