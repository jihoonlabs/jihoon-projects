import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { useAuthStore } from '~/features/auth/stores/authStore';
import { attendanceApi } from '~/test/attendance/attendanceApiHandlers';
import { signInAs } from '~/test/auth/signInAs';
import { apiUrl } from '~/test/msw/apiUrl';
import { overrideApi } from '~/test/msw/overrideApi';

import {
  attendanceHistoryFixture,
  attendanceRecordFixture,
  workingToday,
} from '../../test/attendanceFixture';
import { AttendanceError, useAttendanceApi } from '../attendanceApi';

describe('勤怠 API', () => {
  describe('今日の勤怠', () => {
    it('Laravel の応答を画面用の形に変換すること', async () => {
      signInAs();
      overrideApi(attendanceApi.today(workingToday()));

      await expect(useAttendanceApi().fetchToday()).resolves.toEqual({
        date: '2026-11-08',
        status: 'working',
        record: {
          id: 1,
          workDate: '2026-11-08',
          clockInAt: '2026-11-08T00:00:00+00:00',
          clockOutAt: null,
          durationMinutes: null,
        },
      });
    });
  });

  describe('勤怠記録の一覧', () => {
    it('指定したページを要求し、記録とページ情報を返すこと', async () => {
      signInAs();
      let requestedPage: string | null = null;
      overrideApi(
        http.get(apiUrl('/api/attendance'), ({ request }) => {
          requestedPage = new URL(request.url).searchParams.get('page');
          return HttpResponse.json(
            attendanceHistoryFixture(
              [attendanceRecordFixture({ id: 31, work_date: '2026-10-01' })],
              { current: 2, last: 3 },
            ),
          );
        }),
      );

      const history = await useAttendanceApi().fetchHistory(2);

      expect(requestedPage).toBe('2');
      expect(history.currentPage).toBe(2);
      expect(history.lastPage).toBe(3);
      expect(history.records.map((record) => record.id)).toEqual([31]);
    });
  });

  describe('出勤・退勤', () => {
    it('出勤を記録し、作成された記録を返すこと', async () => {
      signInAs();
      overrideApi(
        attendanceApi.clockSucceeds(
          '/api/attendance/clock-in',
          attendanceRecordFixture({
            id: 9,
            clock_out_at: null,
            duration_minutes: null,
          }),
        ),
      );

      const record = await useAttendanceApi().clock('clock-in');

      expect(record).toMatchObject({ id: 9, clockOutAt: null });
    });

    it('出勤済み（409 already_clocked_in）では出勤済みであることを伝えること', async () => {
      signInAs();
      overrideApi(
        attendanceApi.clockConflict(
          '/api/attendance/clock-in',
          'already_clocked_in',
          '出勤中、または本日はすでに出勤しています。',
        ),
      );

      const request = useAttendanceApi().clock('clock-in');

      await expect(request).rejects.toBeInstanceOf(AttendanceError);
      await expect(request).rejects.toMatchObject({
        message: '本日はすでに出勤しています。',
        status: 409,
        code: 'already_clocked_in',
      });
    });

    it('出勤記録がない退勤（409 not_working）では退勤できないことを伝えること', async () => {
      signInAs();
      overrideApi(
        attendanceApi.clockConflict(
          '/api/attendance/clock-out',
          'not_working',
          '退勤できる出勤記録がありません。',
        ),
      );

      await expect(useAttendanceApi().clock('clock-out')).rejects.toThrow(
        '退勤できる出勤記録がありません。',
      );
    });

    it('理由の分からない競合（409）は一般的な文言で伝えること', async () => {
      signInAs();
      overrideApi(
        attendanceApi.clockConflict(
          '/api/attendance/clock-in',
          'unknown_reason',
          '内部の詳細',
        ),
      );

      await expect(useAttendanceApi().clock('clock-in')).rejects.toThrow(
        '勤怠を処理できませんでした。時間をおいて再度お試しください。',
      );
    });

    it('サーバーエラーの内部情報を利用者向けの文言に含めないこと', async () => {
      signInAs();
      overrideApi(
        http.post(apiUrl('/api/attendance/clock-in'), () =>
          HttpResponse.json(
            { message: 'SQLSTATE[HY000] /Users/example/app.php' },
            { status: 500 },
          ),
        ),
      );

      const request = useAttendanceApi().clock('clock-in');

      await expect(request).rejects.toThrow(
        '勤怠を処理できませんでした。時間をおいて再度お試しください。',
      );
      await expect(request).rejects.not.toThrow(/SQLSTATE/);
    });
  });

  describe('セッション', () => {
    it('ログイン中に 401 が返ったらセッション期限切れにすること', async () => {
      signInAs();
      overrideApi(
        http.get(apiUrl('/api/attendance/today'), () =>
          HttpResponse.json({ message: 'Unauthenticated.' }, { status: 401 }),
        ),
      );

      await expect(useAttendanceApi().fetchToday()).rejects.toMatchObject({
        status: 401,
      });
      expect(useAuthStore().sessionExpired).toBe(true);
    });
  });
});
