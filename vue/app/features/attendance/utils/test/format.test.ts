import { describe, expect, it } from 'vitest';

import { formatAttendanceTime, formatDuration } from '../format';

describe('勤怠の表示形式', () => {
  describe('時刻', () => {
    it('UTC の時刻を日本時間の月日・時分で表示すること', () => {
      expect(formatAttendanceTime('2026-11-08T00:05:00+00:00')).toBe(
        '11/08 09:05',
      );
    });

    it('日本時間で日付が変わる時刻は翌日として表示すること', () => {
      expect(formatAttendanceTime('2026-11-08T15:30:00+00:00')).toBe(
        '11/09 00:30',
      );
    });

    it('未記録は「—」で表示すること', () => {
      expect(formatAttendanceTime(null)).toBe('—');
    });
  });

  describe('勤務時間', () => {
    it('分を時間と2桁の分で表示すること', () => {
      expect(formatDuration(91)).toBe('1時間31分');
    });

    it('1時間未満は0時間として表示すること', () => {
      expect(formatDuration(5)).toBe('0時間05分');
    });

    it('退勤前（null）は「—」で表示すること', () => {
      expect(formatDuration(null)).toBe('—');
    });
  });
});
