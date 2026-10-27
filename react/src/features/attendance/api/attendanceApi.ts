import { fetchWithCsrf } from '@/shared/api/fetchWithCsrf';

import type {
  AttendancePage,
  AttendanceRecord,
  AttendanceToday,
} from '../types/attendance';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface RecordResponse {
  id: number;
  work_date: string;
  clock_in_at: string;
  clock_out_at: string | null;
  duration_minutes: number | null;
}

interface TodayResponse {
  date: string;
  timezone: 'Asia/Tokyo';
  status: AttendanceToday['status'];
  record: RecordResponse | null;
}

export class AttendanceApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
  ) {
    super(message);
    this.name = 'AttendanceApiError';
  }
}

function toRecord(record: RecordResponse): AttendanceRecord {
  return {
    id: record.id,
    workDate: record.work_date,
    clockInAt: record.clock_in_at,
    clockOutAt: record.clock_out_at,
    durationMinutes: record.duration_minutes,
  };
}

async function json<T>(response: Response): Promise<T> {
  const body = await response.json();

  if (!response.ok) {
    throw new AttendanceApiError(
      body.message ?? '勤怠情報を取得できませんでした。',
      response.status,
      body.code,
    );
  }

  return body as T;
}

export async function fetchAttendanceToday(): Promise<AttendanceToday> {
  const result = await json<{ data: TodayResponse }>(
    await fetch(`${API_URL}/api/attendance/today`, {
      credentials: 'include',
      headers: { Accept: 'application/json' },
    }),
  );

  return {
    ...result.data,
    record: result.data.record ? toRecord(result.data.record) : null,
  };
}

export async function fetchAttendancePage(page = 1): Promise<AttendancePage> {
  const result = await json<{
    data: RecordResponse[];
    meta: { current_page: number; last_page: number };
  }>(
    await fetch(`${API_URL}/api/attendance?page=${page}`, {
      credentials: 'include',
      headers: { Accept: 'application/json' },
    }),
  );

  return {
    records: result.data.map(toRecord),
    currentPage: result.meta.current_page,
    lastPage: result.meta.last_page,
  };
}

export async function clockIn(): Promise<AttendanceRecord> {
  const result = await json<{ data: RecordResponse }>(
    await fetchWithCsrf('/api/attendance/clock-in', { method: 'POST' }),
  );
  return toRecord(result.data);
}

export async function clockOut(): Promise<AttendanceRecord> {
  const result = await json<{ data: RecordResponse }>(
    await fetchWithCsrf('/api/attendance/clock-out', { method: 'POST' }),
  );
  return toRecord(result.data);
}
