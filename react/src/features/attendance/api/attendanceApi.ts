import { fetchWithCsrf } from '@/shared/api/fetchWithCsrf';

import type {
  AttendanceBreak,
  AttendancePage,
  AttendanceRecord,
  AttendanceToday,
} from '../types/attendance';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
export const ATTENDANCE_ERROR_MESSAGE =
  '勤怠を処理できませんでした。時間をおいて再度お試しください。';

const CONFLICT_MESSAGES: Record<string, string> = {
  already_clocked_in: '本日はすでに出勤しています。',
  not_working: '退勤できる出勤記録がありません。',
  already_on_break: 'すでに休憩中です。',
  not_on_break: '終了できる休憩記録がありません。',
  break_in_progress: '休憩を終了してから退勤してください。',
};

interface BreakResponse {
  id: number;
  started_at: string;
  ended_at: string | null;
}

interface RecordResponse {
  id: number;
  work_date: string;
  clock_in_at: string;
  clock_out_at: string | null;
  breaks?: BreakResponse[];
  break_duration_minutes?: number;
  duration_seconds?: number | null;
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

function toBreak(value: BreakResponse): AttendanceBreak {
  return {
    id: value.id,
    startedAt: value.started_at,
    endedAt: value.ended_at,
  };
}

function toRecord(record: RecordResponse): AttendanceRecord {
  return {
    id: record.id,
    workDate: record.work_date,
    clockInAt: record.clock_in_at,
    clockOutAt: record.clock_out_at,
    breaks: (record.breaks ?? []).map(toBreak),
    breakDurationMinutes: record.break_duration_minutes ?? 0,
    durationSeconds: record.duration_seconds ?? null,
    durationMinutes: record.duration_minutes,
  };
}

async function json<T>(response: Response): Promise<T> {
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new AttendanceApiError(ATTENDANCE_ERROR_MESSAGE, response.status);
  }

  if (!response.ok) {
    const errorBody =
      typeof body === 'object' && body !== null && !Array.isArray(body)
        ? (body as Record<string, unknown>)
        : {};
    const code =
      typeof errorBody.code === 'string' ? errorBody.code : undefined;

    throw new AttendanceApiError(
      response.status === 409 && code && CONFLICT_MESSAGES[code]
        ? CONFLICT_MESSAGES[code]
        : ATTENDANCE_ERROR_MESSAGE,
      response.status,
      code,
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

export async function startBreak(): Promise<void> {
  await json<{ data: BreakResponse }>(
    await fetchWithCsrf('/api/attendance/break-start', { method: 'POST' }),
  );
}

export async function endBreak(): Promise<void> {
  await json<{ data: BreakResponse }>(
    await fetchWithCsrf('/api/attendance/break-end', { method: 'POST' }),
  );
}
