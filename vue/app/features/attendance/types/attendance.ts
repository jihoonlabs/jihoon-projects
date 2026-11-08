/**
 * Laravel の AttendanceRecordResource（snake_case）。時刻は UTC の ISO 8601。
 */
export interface AttendanceRecordResponse {
  id: number;
  work_date: string;
  clock_in_at: string;
  clock_out_at: string | null;
  duration_minutes: number | null;
}

export type AttendanceStatus = 'not_started' | 'working' | 'finished';

export interface AttendanceTodayResponse {
  data: {
    date: string;
    timezone: 'Asia/Tokyo';
    status: AttendanceStatus;
    record: AttendanceRecordResponse | null;
  };
}

export interface AttendanceHistoryResponse {
  data: AttendanceRecordResponse[];
  meta: { current_page: number; last_page: number };
}

/** 画面で使う勤怠記録 */
export interface AttendanceRecord {
  id: number;
  workDate: string;
  clockInAt: string;
  clockOutAt: string | null;
  durationMinutes: number | null;
}

export interface AttendanceToday {
  date: string;
  status: AttendanceStatus;
  record: AttendanceRecord | null;
}

export interface AttendanceHistory {
  records: AttendanceRecord[];
  currentPage: number;
  lastPage: number;
}

export type ClockAction = 'clock-in' | 'clock-out';
