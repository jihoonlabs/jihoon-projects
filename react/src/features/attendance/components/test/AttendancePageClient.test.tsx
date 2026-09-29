import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, it, vi } from 'vitest';

import * as api from '../../api/attendanceApi';
import type { AttendanceRecord } from '../../types/attendance';
import { AttendancePageClient } from '../AttendancePageClient';

vi.mock('../../api/attendanceApi', () => ({
  fetchAttendanceToday: vi.fn(),
  fetchAttendancePage: vi.fn(),
  clockIn: vi.fn(),
  clockOut: vi.fn(),
}));

const record: AttendanceRecord = {
  id: 1,
  workDate: '2026-09-29',
  clockInAt: '2026-09-29T00:00:00+00:00',
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

it('enables only clock-in before work, then only clock-out after recording it', async () => {
  vi.mocked(api.fetchAttendanceToday)
    .mockResolvedValueOnce({
      date: '2026-09-29',
      timezone: 'Asia/Tokyo',
      status: 'not_started',
      record: null,
    })
    .mockResolvedValue({
      date: '2026-09-29',
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
  expect(screen.getByText('2026-09-29')).toBeInTheDocument();
});

it('disables both buttons after checkout and displays the elapsed duration', async () => {
  vi.mocked(api.fetchAttendanceToday).mockResolvedValue({
    date: '2026-09-29',
    timezone: 'Asia/Tokyo',
    status: 'finished',
    record: {
      ...record,
      clockOutAt: '2026-09-29T01:31:00+00:00',
      durationMinutes: 91,
    },
  });
  vi.mocked(api.fetchAttendancePage).mockResolvedValue({
    records: [
      {
        ...record,
        clockOutAt: '2026-09-29T01:31:00+00:00',
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
