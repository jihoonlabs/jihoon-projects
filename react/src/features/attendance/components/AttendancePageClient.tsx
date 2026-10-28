'use client';

import { useCallback, useEffect, useState } from 'react';
import { CalendarClock, Coffee, LogIn, LogOut, Play } from 'lucide-react';

import {
  ATTENDANCE_ERROR_MESSAGE,
  AttendanceApiError,
  clockIn,
  clockOut,
  endBreak,
  startBreak,
  fetchAttendancePage,
  fetchAttendanceSchedule,
  fetchAttendanceToday,
  saveAttendanceSchedule,
} from '../api/attendanceApi';
import type {
  AttendancePage,
  AttendanceSchedule,
  AttendanceScheduleInput,
  AttendanceScheduleState,
  AttendanceToday,
} from '../types/attendance';

import styles from './AttendancePageClient.module.css';

const STATUS_LABELS = {
  not_started: '出勤前',
  working: '勤務中',
  on_break: '休憩中',
  finished: '退勤済み',
};

const WEEKDAY_LABELS = ['月', '火', '水', '木', '金', '土', '日'];

function scheduleInputFrom(
  state: AttendanceScheduleState,
): AttendanceScheduleInput {
  const source = state.upcoming ?? state.current;

  return {
    effectiveFrom: state.upcoming?.effectiveFrom ?? state.date,
    weekdays: source?.weekdays ?? [],
    startTime: source?.startTime ?? '',
    endTime: source?.endTime ?? '',
    plannedBreakMinutes: source?.plannedBreakMinutes ?? 0,
  };
}

function scheduleSummary(schedule: AttendanceSchedule): string {
  const weekdays = schedule.weekdays
    .map((day) => WEEKDAY_LABELS[day - 1])
    .join('・');

  return `${weekdays} ${schedule.startTime}〜${schedule.endTime}（予定休憩 ${schedule.plannedBreakMinutes}分）`;
}

function formatTime(value: string | null): string {
  if (!value) return '—';

  return new Intl.DateTimeFormat('ja-JP', {
    timeZone: 'Asia/Tokyo',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(new Date(value));
}

function formatDuration(minutes: number | null): string {
  if (minutes === null) return '—';
  return `${Math.floor(minutes / 60)}時間${String(minutes % 60).padStart(2, '0')}分`;
}

function errorMessage(error: unknown): string {
  return error instanceof AttendanceApiError
    ? error.message
    : ATTENDANCE_ERROR_MESSAGE;
}

export function AttendancePageClient() {
  const [today, setToday] = useState<AttendanceToday | null>(null);
  const [history, setHistory] = useState<AttendancePage | null>(null);
  const [schedule, setSchedule] = useState<AttendanceScheduleState | null>(null);
  const [scheduleInput, setScheduleInput] = useState<AttendanceScheduleInput>({
    effectiveFrom: '',
    weekdays: [],
    startTime: '',
    endTime: '',
    plannedBreakMinutes: 0,
  });
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (requestedPage: number) => {
    return Promise.all([
      fetchAttendanceToday(),
      fetchAttendancePage(requestedPage),
      fetchAttendanceSchedule(),
    ]);
  }, []);

  useEffect(() => {
    load(page)
      .then(([latestToday, latestHistory, latestSchedule]) => {
        setToday(latestToday);
        setHistory(latestHistory);
        setSchedule(latestSchedule);
        setScheduleInput(scheduleInputFrom(latestSchedule));
        setError(null);
      })
      .catch((loadError) => setError(errorMessage(loadError)))
      .finally(() => setIsLoading(false));
  }, [page, load]);

  const changePage = (nextPage: number) => {
    setIsLoading(true);
    setError(null);
    setPage(nextPage);
  };

  const recordAction = async (
    action: 'in' | 'out' | 'break-start' | 'break-end',
  ) => {
    if (isSubmitting || isLoading) return;

    setIsSubmitting(true);
    setError(null);
    try {
      if (action === 'in') {
        await clockIn();
      } else if (action === 'out') {
        await clockOut();
      } else if (action === 'break-start') {
        await startBreak();
      } else {
        await endBreak();
      }
      const [latestToday, latestHistory, latestSchedule] = await load(page);
      setToday(latestToday);
      setHistory(latestHistory);
      setSchedule(latestSchedule);
      setScheduleInput(scheduleInputFrom(latestSchedule));
    } catch (actionError) {
      setError(errorMessage(actionError));
      try {
        const [latestToday, latestHistory] = await load(page);
        setToday(latestToday);
        setHistory(latestHistory);
      } catch {
        // Keep the action error visible when the follow-up read also fails.
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleWeekday = (day: number) => {
    const weekdays = new Set(scheduleInput.weekdays);
    if (weekdays.has(day)) weekdays.delete(day);
    else weekdays.add(day);

    setScheduleInput({
      ...scheduleInput,
      weekdays: Array.from(weekdays).sort((left, right) => left - right),
    });
  };

  const saveSchedule = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (isSubmitting || isLoading) return;

    setIsSubmitting(true);
    setError(null);
    try {
      await saveAttendanceSchedule(scheduleInput);
      const latestSchedule = await fetchAttendanceSchedule();
      setSchedule(latestSchedule);
      setScheduleInput(scheduleInputFrom(latestSchedule));
    } catch (saveError) {
      setError(errorMessage(saveError));
    } finally {
      setIsSubmitting(false);
    }
  };

  const disabled = isLoading || isSubmitting || today === null;

  return (
    <main className={styles.page}>
      <h1>勤怠管理</h1>
      {process.env.NEXT_PUBLIC_DEMO_MODE === 'true' && (
        <p className={styles.demoNote}>
          「出勤」を押してから「退勤」を押すだけで試せます。共通デモのため記録は他の閲覧者にも表示されます。
        </p>
      )}

      <section className={styles.panel} aria-labelledby="today-heading">
        <h2 id="today-heading">今日の勤怠</h2>
        <p className={styles.status} role="status">
          {today ? STATUS_LABELS[today.status] : '読み込み中...'}
        </p>
        {today?.record && today.record.workDate !== today.date && (
          <p>勤務日: {today.record.workDate}（日付をまたいで勤務中）</p>
        )}
        <dl className={styles.times}>
          <div>
            <dt>出勤時刻</dt>
            <dd>{formatTime(today?.record?.clockInAt ?? null)}</dd>
          </div>
          <div>
            <dt>退勤時刻</dt>
            <dd>{formatTime(today?.record?.clockOutAt ?? null)}</dd>
          </div>
        </dl>
        {today?.status === 'on_break' && today.record && (
          <p>
            休憩開始:{' '}
            {formatTime(
              today.record.breaks.find(
                (breakRecord) => breakRecord.endedAt === null,
              )?.startedAt ?? null,
            )}
          </p>
        )}
        <div className={styles.actions}>
          <button
            type="button"
            className={styles.clockIn}
            disabled={disabled || today?.status !== 'not_started'}
            onClick={() => recordAction('in')}
          >
            <LogIn aria-hidden="true" size={20} strokeWidth={2} />
            出勤
          </button>
          <button
            type="button"
            className={styles.breakStart}
            disabled={disabled || today?.status !== 'working'}
            onClick={() => recordAction('break-start')}
          >
            <Coffee aria-hidden="true" size={20} strokeWidth={2} />
            休憩開始
          </button>
          <button
            type="button"
            className={styles.breakEnd}
            disabled={disabled || today?.status !== 'on_break'}
            onClick={() => recordAction('break-end')}
          >
            <Play aria-hidden="true" size={20} strokeWidth={2} />
            休憩終了
          </button>
          <button
            type="button"
            className={styles.clockOut}
            disabled={disabled || today?.status !== 'working'}
            onClick={() => recordAction('out')}
          >
            <LogOut aria-hidden="true" size={20} strokeWidth={2} />
            退勤
          </button>
        </div>
      </section>

      <section className={styles.panel} aria-labelledby="schedule-heading">
        <h2 id="schedule-heading">
          <CalendarClock aria-hidden="true" size={18} />
          予定勤務の設定
        </h2>
        <p className={styles.scheduleNote}>
          予定の目安として保存します。実際の打刻・休憩記録には影響せず、予定休憩も勤務時間から自動で差し引きません。
        </p>
        {schedule?.current && (
          <p>現在の予定: {scheduleSummary(schedule.current)}</p>
        )}
        {schedule?.upcoming && (
          <p>
            {schedule.upcoming.effectiveFrom} からの予定:{' '}
            {scheduleSummary(schedule.upcoming)}
          </p>
        )}
        <form className={styles.scheduleForm} onSubmit={saveSchedule}>
          <label>
            適用開始日
            <input
              type="date"
              required
              value={scheduleInput.effectiveFrom}
              disabled={disabled}
              onChange={(event) =>
                setScheduleInput({
                  ...scheduleInput,
                  effectiveFrom: event.currentTarget.value,
                })
              }
            />
          </label>
          <fieldset className={styles.weekdays}>
            <legend>勤務する曜日</legend>
            {WEEKDAY_LABELS.map((label, index) => (
              <label key={label}>
                <input
                  type="checkbox"
                  checked={scheduleInput.weekdays.includes(index + 1)}
                  disabled={disabled}
                  onChange={() => toggleWeekday(index + 1)}
                />
                {label}
              </label>
            ))}
          </fieldset>
          <div className={styles.scheduleFields}>
            <label>
              開始時刻
              <input
                type="time"
                required
                value={scheduleInput.startTime}
                disabled={disabled}
                onChange={(event) =>
                  setScheduleInput({
                    ...scheduleInput,
                    startTime: event.currentTarget.value,
                  })
                }
              />
            </label>
            <label>
              終了時刻
              <input
                type="time"
                required
                value={scheduleInput.endTime}
                disabled={disabled}
                onChange={(event) =>
                  setScheduleInput({
                    ...scheduleInput,
                    endTime: event.currentTarget.value,
                  })
                }
              />
            </label>
            <label>
              예정 휴식 (분)
              <input
                type="number"
                min="0"
                max="600"
                required
                value={scheduleInput.plannedBreakMinutes}
                disabled={disabled}
                onChange={(event) =>
                  setScheduleInput({
                    ...scheduleInput,
                    plannedBreakMinutes: Number(event.currentTarget.value),
                  })
                }
              />
            </label>
          </div>
          <button
            type="submit"
            className={styles.saveSchedule}
            disabled={
              disabled ||
              scheduleInput.weekdays.length === 0 ||
              !scheduleInput.startTime ||
              !scheduleInput.endTime
            }
          >
            일정 저장
          </button>
        </form>
      </section>

      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}

      <section className={styles.panel} aria-labelledby="history-heading">
        <h2 id="history-heading">自分の勤怠記録</h2>
        <div className={styles.tableScroll}>
          <table>
            <thead>
              <tr>
                <th scope="col">勤務日</th>
                <th scope="col">出勤時刻</th>
                <th scope="col">退勤時刻</th>
                <th scope="col">休憩時間</th>
                <th scope="col">勤務時間</th>
              </tr>
            </thead>
            <tbody>
              {history?.records.map((record) => (
                <tr key={record.id}>
                  <td>{record.workDate}</td>
                  <td>{formatTime(record.clockInAt)}</td>
                  <td>{formatTime(record.clockOutAt)}</td>
                  <td>{formatDuration(record.breakDurationMinutes)}</td>
                  <td>{formatDuration(record.durationMinutes)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {history?.records.length === 0 && <p>勤怠記録はまだありません。</p>}
        {history && history.lastPage > 1 && (
          <div className={styles.pagination}>
            <button
              type="button"
              disabled={isLoading || isSubmitting || page <= 1}
              onClick={() => changePage(page - 1)}
            >
              前へ
            </button>
            <span>
              {history.currentPage} / {history.lastPage}
            </span>
            <button
              type="button"
              disabled={isLoading || isSubmitting || page >= history.lastPage}
              onClick={() => changePage(page + 1)}
            >
              次へ
            </button>
          </div>
        )}
      </section>
    </main>
  );
}
