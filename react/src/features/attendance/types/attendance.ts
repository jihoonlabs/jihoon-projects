export interface AttendanceBreak {
  id: number;
  startedAt: string;
  endedAt: string | null;
}

export interface AttendanceRecord {
  id: number;
  workDate: string;
  clockInAt: string;
  clockOutAt: string | null;
  breaks: AttendanceBreak[];
  breakDurationMinutes: number;
  durationSeconds: number | null;
  durationMinutes: number | null;
}

export type AttendanceStatus = 'not_started' | 'working' | 'on_break' | 'finished';

export interface AttendanceToday {
  date: string;
  timezone: 'Asia/Tokyo';
  status: AttendanceStatus;
  record: AttendanceRecord | null;
}

export interface AttendancePage {
  records: AttendanceRecord[];
  currentPage: number;
  lastPage: number;
}
