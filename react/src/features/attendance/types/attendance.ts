export interface AttendanceRecord {
  id: number;
  workDate: string;
  clockInAt: string;
  clockOutAt: string | null;
  durationMinutes: number | null;
}

export type AttendanceStatus = 'not_started' | 'working' | 'finished';

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
