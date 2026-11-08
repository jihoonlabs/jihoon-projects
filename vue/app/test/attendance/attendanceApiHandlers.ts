import { http, HttpResponse } from 'msw';

import type {
  AttendanceHistoryResponse,
  AttendanceRecordResponse,
  AttendanceTodayResponse,
} from '~/features/attendance/types';

import { apiUrl } from '../msw/apiUrl';

type ClockPath = '/api/attendance/clock-in' | '/api/attendance/clock-out';

/**
 * 勤怠 API の応答。各テストで overrideApi に渡して使う。
 */
export const attendanceApi = {
  today(response: AttendanceTodayResponse) {
    return http.get(apiUrl('/api/attendance/today'), () =>
      HttpResponse.json(response),
    );
  },

  /**
   * 呼ばれるたびに順番に応答を返す（出勤の前後で状態が変わる場面用）。最後の応答はその後も返し続ける。
   */
  todaySequence(...responses: AttendanceTodayResponse[]) {
    let call = 0;

    return http.get(apiUrl('/api/attendance/today'), () => {
      const response = responses[Math.min(call, responses.length - 1)];
      call += 1;
      return HttpResponse.json(response);
    });
  },

  history(response: AttendanceHistoryResponse) {
    return http.get(apiUrl('/api/attendance'), () =>
      HttpResponse.json(response),
    );
  },

  clockSucceeds(path: ClockPath, record: AttendanceRecordResponse) {
    return http.post(apiUrl(path), () =>
      HttpResponse.json({ data: record }, { status: 201 }),
    );
  },

  clockConflict(path: ClockPath, code: string, message: string) {
    return http.post(apiUrl(path), () =>
      HttpResponse.json({ code, message }, { status: 409 }),
    );
  },
};
