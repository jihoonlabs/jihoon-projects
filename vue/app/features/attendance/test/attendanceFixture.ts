import type {
  AttendanceHistoryResponse,
  AttendanceRecordResponse,
  AttendanceStatus,
  AttendanceTodayResponse,
} from '../types';

/**
 * Laravel の AttendanceRecordResource と同じ形の勤怠記録（時刻は UTC）。
 * 既定は 2026-11-08 9:00〜18:00（日本時間）に勤務した記録。
 */
export function attendanceRecordFixture(
  overrides: Partial<AttendanceRecordResponse> = {},
): AttendanceRecordResponse {
  return {
    id: 1,
    work_date: '2026-11-08',
    clock_in_at: '2026-11-08T00:00:00+00:00',
    clock_out_at: '2026-11-08T09:00:00+00:00',
    duration_minutes: 540,
    ...overrides,
  };
}

/**
 * /api/attendance/today の応答。状態に合わせて記録を指定する。
 */
export function attendanceTodayFixture(
  status: AttendanceStatus,
  record: AttendanceRecordResponse | null,
  date = '2026-11-08',
): AttendanceTodayResponse {
  return {
    data: { date, timezone: 'Asia/Tokyo', status, record },
  };
}

/**
 * /api/attendance?page= の応答
 */
export function attendanceHistoryFixture(
  records: AttendanceRecordResponse[],
  page = { current: 1, last: 1 },
): AttendanceHistoryResponse {
  return {
    data: records,
    meta: { current_page: page.current, last_page: page.last },
  };
}

/** 出勤前の今日の状態 */
export const notStartedToday = () =>
  attendanceTodayFixture('not_started', null);

/** 勤務中（日本時間 9:00 出勤）の今日の状態 */
export const workingToday = () =>
  attendanceTodayFixture(
    'working',
    attendanceRecordFixture({ clock_out_at: null, duration_minutes: null }),
  );
