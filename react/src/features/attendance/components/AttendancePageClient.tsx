'use client';

import { useCallback, useEffect, useState } from 'react';
import { CalendarDays, Clock3, History, LogIn, LogOut } from 'lucide-react';

import {
  ATTENDANCE_ERROR_MESSAGE,
  AttendanceApiError,
  clockIn,
  clockOut,
  fetchAttendancePage,
  fetchAttendanceToday,
} from '../api/attendanceApi';
import type { AttendancePage, AttendanceToday } from '../types/attendance';

import styles from './AttendancePageClient.module.css';

const STATUS_LABELS = {
  not_started: '出勤前',
  working: '勤務中',
  finished: '退勤済み',
};

const STATUS_CLASSES = {
  not_started: styles.statusIdle,
  working: styles.statusWorking,
  finished: styles.statusFinished,
};

function isClockInAllowedAt(date: Date): boolean {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Tokyo',
    hour: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(date);
  const hour = Number(parts.find((part) => part.type === 'hour')?.value);

  return hour >= 6;
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
  return (
    Math.floor(minutes / 60) +
    '時間' +
    String(minutes % 60).padStart(2, '0') +
    '分'
  );
}

function errorMessage(error: unknown): string {
  return error instanceof AttendanceApiError
    ? error.message
    : ATTENDANCE_ERROR_MESSAGE;
}

export function AttendancePageClient() {
  const [today, setToday] = useState<AttendanceToday | null>(null);
  const [history, setHistory] = useState<AttendancePage | null>(null);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isClockInAllowed, setIsClockInAllowed] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (requestedPage: number) => {
    return Promise.all([
      fetchAttendanceToday(),
      fetchAttendancePage(requestedPage),
    ]);
  }, []);

  useEffect(() => {
    const updateClockInAvailability = () => {
      const next = isClockInAllowedAt(new Date(Date.now()));
      setIsClockInAllowed((current) => (current === next ? current : next));
    };

    updateClockInAvailability();
    const timer = window.setInterval(updateClockInAvailability, 15_000);

    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    load(page)
      .then(([latestToday, latestHistory]) => {
        setToday(latestToday);
        setHistory(latestHistory);
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

  const recordAction = async (action: 'in' | 'out') => {
    if (isSubmitting || isLoading) return;

    setIsSubmitting(true);
    setError(null);
    try {
      if (action === 'in') {
        await clockIn();
      } else {
        await clockOut();
      }
      const [latestToday, latestHistory] = await load(page);
      setToday(latestToday);
      setHistory(latestHistory);
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

  const disabled = isLoading || isSubmitting || today === null;

  return (
    <main className={styles.page}>
      <header className={styles.pageHeader}>
        <div className={styles.pageIcon} aria-hidden="true">
          <CalendarDays size={24} strokeWidth={1.8} />
        </div>
        <div>
          <p className={styles.eyebrow}>ATTENDANCE</p>
          <h1>勤怠管理</h1>
          <p className={styles.lead}>今日の出勤状況と記録を確認できます。</p>
        </div>
      </header>

      {process.env.NEXT_PUBLIC_DEMO_MODE === 'true' && (
        <p className={styles.demoNote}>
          日本時間06:00以降に出勤を記録できます。共通デモのため記録は他の閲覧者にも表示されます。
        </p>
      )}

      <section className={styles.panel} aria-labelledby="today-heading">
        <div className={styles.panelHeading}>
          <div>
            <p className={styles.eyebrow}>TODAY</p>
            <h2 id="today-heading">今日の勤怠</h2>
          </div>
          <span className={styles.date}>
            <CalendarDays aria-hidden="true" size={16} />
            {today?.date ?? '—'}
          </span>
        </div>
        <p
          className={
            styles.status +
            ' ' +
            (today ? STATUS_CLASSES[today.status] : styles.statusLoading)
          }
          role="status"
        >
          {today ? STATUS_LABELS[today.status] : '読み込み中...'}
        </p>
        {today?.record && today.record.workDate !== today.date && (
          <p className={styles.overnightNote}>
            勤務日: {today.record.workDate}（日付をまたいで勤務中）
          </p>
        )}
        <dl className={styles.times}>
          <div>
            <dt>
              <LogIn aria-hidden="true" size={16} />
              出勤時刻
            </dt>
            <dd>{formatTime(today?.record?.clockInAt ?? null)}</dd>
          </div>
          <div>
            <dt>
              <LogOut aria-hidden="true" size={16} />
              退勤時刻
            </dt>
            <dd>{formatTime(today?.record?.clockOutAt ?? null)}</dd>
          </div>
        </dl>
        <p
          className={
            styles.clockInHint +
            (isClockInAllowed ? '' : ' ' + styles.clockInHintWaiting)
          }
        >
          <Clock3 aria-hidden="true" size={16} />
          {isClockInAllowed
            ? '出勤は日本時間06:00から記録できます。'
            : '出勤受付は日本時間06:00に開始します。'}
        </p>
        <div className={styles.actions}>
          <button
            type="button"
            className={styles.clockIn}
            disabled={
              disabled || today?.status !== 'not_started' || !isClockInAllowed
            }
            onClick={() => recordAction('in')}
          >
            <LogIn aria-hidden="true" size={19} strokeWidth={2} />
            出勤
          </button>
          <button
            type="button"
            className={styles.clockOut}
            disabled={disabled || today?.status !== 'working'}
            onClick={() => recordAction('out')}
          >
            <LogOut aria-hidden="true" size={19} strokeWidth={2} />
            退勤
          </button>
        </div>
      </section>

      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}

      <section className={styles.panel} aria-labelledby="history-heading">
        <div className={styles.panelHeading}>
          <div>
            <p className={styles.eyebrow}>HISTORY</p>
            <h2 id="history-heading">
              <History aria-hidden="true" size={18} />
              自分の勤怠記録
            </h2>
          </div>
        </div>
        <div className={styles.tableScroll}>
          <table>
            <thead>
              <tr>
                <th scope="col">勤務日</th>
                <th scope="col">出勤時刻</th>
                <th scope="col">退勤時刻</th>
                <th scope="col">勤務時間</th>
              </tr>
            </thead>
            <tbody>
              {history?.records.map((record) => (
                <tr key={record.id}>
                  <td>{record.workDate}</td>
                  <td>{formatTime(record.clockInAt)}</td>
                  <td>{formatTime(record.clockOutAt)}</td>
                  <td>{formatDuration(record.durationMinutes)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {history?.records.length === 0 && (
          <p className={styles.emptyState}>勤怠記録はまだありません。</p>
        )}
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

export { isClockInAllowedAt };
