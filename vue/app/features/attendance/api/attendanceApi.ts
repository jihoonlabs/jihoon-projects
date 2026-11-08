import { useProtectedApi } from '~/features/auth/api/protectedRequest';
import { ApiError } from '~/shared/api/apiClient';

import type {
  AttendanceHistory,
  AttendanceHistoryResponse,
  AttendanceRecord,
  AttendanceRecordResponse,
  AttendanceToday,
  AttendanceTodayResponse,
  ClockAction,
} from '../types';

export const ATTENDANCE_ERROR_MESSAGE =
  '勤怠を処理できませんでした。時間をおいて再度お試しください。';

// Next.js 版と同じく、競合（409）のうち理由が分かるものだけ個別の文言にする
const CONFLICT_MESSAGES: Record<string, string> = {
  already_clocked_in: '本日はすでに出勤しています。',
  not_working: '退勤できる出勤記録がありません。',
};

/**
 * 画面にそのまま表示できる勤怠操作の失敗
 */
export class AttendanceError extends Error {
  constructor(
    message: string,
    readonly status?: number,
    readonly code?: string,
  ) {
    super(message);
    this.name = 'AttendanceError';
  }
}

export function toAttendanceRecord(
  record: AttendanceRecordResponse,
): AttendanceRecord {
  return {
    id: record.id,
    workDate: record.work_date,
    clockInAt: record.clock_in_at,
    clockOutAt: record.clock_out_at,
    durationMinutes: record.duration_minutes,
  };
}

const isAbortError = (error: unknown) =>
  error instanceof Error && error.name === 'AbortError';

const toAttendanceError = (error: unknown): AttendanceError => {
  if (!(error instanceof ApiError)) {
    return new AttendanceError(ATTENDANCE_ERROR_MESSAGE);
  }

  const conflictMessage =
    error.status === 409 && error.code
      ? CONFLICT_MESSAGES[error.code]
      : undefined;

  return new AttendanceError(
    conflictMessage ?? ATTENDANCE_ERROR_MESSAGE,
    error.status,
    error.code,
  );
};

// 中断（ログイン状態の変化・画面離脱）はそのまま伝え、それ以外は表示用の失敗に変える
const translate = async <T>(request: Promise<T>): Promise<T> => {
  try {
    return await request;
  } catch (error) {
    if (isAbortError(error)) {
      throw error;
    }

    throw toAttendanceError(error);
  }
};

export function useAttendanceApi() {
  const api = useProtectedApi();

  return {
    async fetchToday(signal?: AbortSignal): Promise<AttendanceToday> {
      const { data } = await translate(
        api.getJson<AttendanceTodayResponse>('/api/attendance/today', {
          signal,
        }),
      );

      return {
        date: data.date,
        status: data.status,
        record: data.record ? toAttendanceRecord(data.record) : null,
      };
    },

    async fetchHistory(
      page: number,
      signal?: AbortSignal,
    ): Promise<AttendanceHistory> {
      const response = await translate(
        api.getJson<AttendanceHistoryResponse>(`/api/attendance?page=${page}`, {
          signal,
        }),
      );

      return {
        records: response.data.map(toAttendanceRecord),
        currentPage: response.meta.current_page,
        lastPage: response.meta.last_page,
      };
    },

    async clock(action: ClockAction): Promise<AttendanceRecord> {
      const { data } = await translate(
        api.sendJson<{ data: AttendanceRecordResponse }>(
          'POST',
          `/api/attendance/${action}`,
        ),
      );

      return toAttendanceRecord(data);
    },
  };
}

export type AttendanceApi = ReturnType<typeof useAttendanceApi>;
