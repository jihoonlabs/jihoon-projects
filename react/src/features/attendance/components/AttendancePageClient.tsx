'use client';

import { useCallback, useEffect, useState } from 'react';

import {
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
  return error instanceof Error
    ? error.message
    : '勤怠情報を取得できませんでした。';
}

export function AttendancePageClient() {
  const [today, setToday] = useState<AttendanceToday | null>(null);
  const [history, setHistory] = useState<AttendancePage | null>(null);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (requestedPage: number) => {
    return Promise.all([
      fetchAttendanceToday(),
      fetchAttendancePage(requestedPage),
    ]);
  }, []);

  useEffect(() => {
    load(page)
      .then(([latestToday, latestHistory]) => {
        setToday(latestToday);
        setHistory(latestHistory);
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
      <h1>勤怠管理</h1>

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
        <div className={styles.actions}>
          <button
            type="button"
            disabled={disabled || today?.status !== 'not_started'}
            onClick={() => recordAction('in')}
          >
            出勤
          </button>
          <button
            type="button"
            disabled={disabled || today?.status !== 'working'}
            onClick={() => recordAction('out')}
          >
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
        <h2 id="history-heading">自分の勤怠記録</h2>
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
