const TIMEZONE = 'Asia/Tokyo';

const dateTimeFormat = new Intl.DateTimeFormat('ja-JP', {
  timeZone: TIMEZONE,
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
});

/**
 * UTC の時刻を日本時間の「MM/DD HH:mm」で表示する。未記録は「—」。
 */
export function formatAttendanceTime(value: string | null): string {
  if (!value) return '—';

  return dateTimeFormat.format(new Date(value));
}

/**
 * 勤務時間（分）を「n時間mm分」で表示する。退勤前は「—」。
 */
export function formatDuration(minutes: number | null): string {
  if (minutes === null) return '—';

  const hours = Math.floor(minutes / 60);
  const rest = String(minutes % 60).padStart(2, '0');

  return `${hours}時間${rest}分`;
}

export const STATUS_LABELS = {
  not_started: '出勤前',
  working: '勤務中',
  finished: '退勤済み',
} as const;
