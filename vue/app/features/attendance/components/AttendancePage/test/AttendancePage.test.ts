import { screen, waitFor, within } from '@testing-library/vue';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import {
  attendanceHistoryFixture,
  attendanceRecordFixture,
  attendanceTodayFixture,
  notStartedToday,
  workingToday,
} from '~/features/attendance/api/test/attendanceFixture';
import type { AttendanceHistoryResponse } from '~/features/attendance/types/attendance';
import { useAuthStore } from '~/features/auth/store/useAuthStore';
import { attendanceApi } from '~/test/mocks/attendance/attendanceApiHandlers';
import { authApi } from '~/test/mocks/auth/authApiHandlers';
import { signInAs } from '~/test/auth/signInAs';
import { enableDemoMode } from '~/test/demoMode';
import { apiUrl } from '~/test/mocks/apiUrl';
import { overrideApi } from '~/test/mocks/overrideApi';
import { renderRoute } from '~/test/renderRoute';

const clockInButton = () => screen.getByRole('button', { name: '出勤' });
const clockOutButton = () => screen.getByRole('button', { name: '退勤' });
const todayPanel = () => screen.getByRole('region', { name: '今日の勤怠' });
const historyPanel = () =>
  screen.getByRole('region', { name: '自分の勤怠記録' });

const expectStatus = async (label: string) => {
  await waitFor(() => {
    expect(within(todayPanel()).getByRole('status')).toHaveTextContent(label);
  });
};

const historyRows = () =>
  within(historyPanel())
    .getAllByRole('row')
    .slice(1)
    .map((row) =>
      within(row)
        .getAllByRole('cell')
        .map((cell) => cell.textContent?.trim()),
    );

const emptyHistory = () => attendanceHistoryFixture([]);

describe('勤怠画面', () => {
  describe('今日の勤怠', () => {
    it('出勤前は出勤だけを押せること', async () => {
      signInAs();
      overrideApi(
        attendanceApi.today(notStartedToday()),
        attendanceApi.history(emptyHistory()),
      );

      await renderRoute('/attendance');

      await expectStatus('出勤前');
      expect(clockInButton()).toBeEnabled();
      expect(clockOutButton()).toBeDisabled();
      expect(
        within(todayPanel()).getByText('出勤時刻').nextElementSibling,
      ).toHaveTextContent('—');
    });

    it('勤務中は出勤時刻を日本時間で表示し、退勤だけを押せること', async () => {
      signInAs();
      overrideApi(
        attendanceApi.today(workingToday()),
        attendanceApi.history(emptyHistory()),
      );

      await renderRoute('/attendance');

      await expectStatus('勤務中');
      expect(
        within(todayPanel()).getByText('出勤時刻').nextElementSibling,
      ).toHaveTextContent('11/08 09:00');
      expect(clockInButton()).toBeDisabled();
      expect(clockOutButton()).toBeEnabled();
    });

    it('退勤済みはどちらのボタンも押せないこと', async () => {
      signInAs();
      overrideApi(
        attendanceApi.today(
          attendanceTodayFixture('finished', attendanceRecordFixture()),
        ),
        attendanceApi.history(emptyHistory()),
      );

      await renderRoute('/attendance');

      await expectStatus('退勤済み');
      expect(clockInButton()).toBeDisabled();
      expect(clockOutButton()).toBeDisabled();
    });

    it('日付をまたいで勤務中なら、元の勤務日を表示すること', async () => {
      signInAs();
      overrideApi(
        attendanceApi.today(
          attendanceTodayFixture(
            'working',
            attendanceRecordFixture({
              work_date: '2026-11-07',
              clock_in_at: '2026-11-07T13:00:00+00:00',
              clock_out_at: null,
              duration_minutes: null,
            }),
            '2026-11-08',
          ),
        ),
        attendanceApi.history(emptyHistory()),
      );

      await renderRoute('/attendance');

      expect(
        await within(todayPanel()).findByText(
          '勤務日: 2026-11-07（日付をまたいで勤務中）',
        ),
      ).toBeInTheDocument();
    });
  });

  describe('出勤・退勤の記録', () => {
    it('出勤すると記録を送り、最新の状態を読み直して勤務中にすること', async () => {
      signInAs();
      let clockedIn = false;
      overrideApi(
        attendanceApi.todaySequence(notStartedToday(), workingToday()),
        attendanceApi.history(emptyHistory()),
        http.post(apiUrl('/api/attendance/clock-in'), () => {
          clockedIn = true;
          return HttpResponse.json(
            { data: workingToday().data.record },
            { status: 201 },
          );
        }),
      );
      const { user } = await renderRoute('/attendance');
      await expectStatus('出勤前');

      await user.click(clockInButton());

      await expectStatus('勤務中');
      expect(clockedIn).toBe(true);
      expect(clockOutButton()).toBeEnabled();
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('記録中は出勤・退勤のどちらも押せないこと', async () => {
      signInAs();
      let release: () => void = () => undefined;
      overrideApi(
        attendanceApi.today(notStartedToday()),
        attendanceApi.history(emptyHistory()),
        http.post(apiUrl('/api/attendance/clock-in'), async () => {
          await new Promise<void>((resolve) => {
            release = resolve;
          });
          return HttpResponse.json(
            { data: workingToday().data.record },
            { status: 201 },
          );
        }),
      );
      const { user } = await renderRoute('/attendance');
      await expectStatus('出勤前');

      await user.click(clockInButton());

      await waitFor(() => {
        expect(clockInButton()).toBeDisabled();
      });
      expect(clockOutButton()).toBeDisabled();

      // 記録と再読み込みが終わるまで待ち、次のテストへ処理を持ち越さない
      release();
      await waitFor(() => {
        expect(clockInButton()).toBeEnabled();
      });
    });

    it('すでに出勤済み（409）ならその旨を表示し、最新の状態に合わせること', async () => {
      signInAs();
      overrideApi(
        attendanceApi.todaySequence(notStartedToday(), workingToday()),
        attendanceApi.history(emptyHistory()),
        attendanceApi.clockConflict(
          '/api/attendance/clock-in',
          'already_clocked_in',
          '出勤中、または本日はすでに出勤しています。',
        ),
      );
      const { user } = await renderRoute('/attendance');
      await expectStatus('出勤前');

      await user.click(clockInButton());

      expect(await screen.findByRole('alert')).toHaveTextContent(
        '本日はすでに出勤しています。',
      );
      await expectStatus('勤務中');
    });

    it('退勤すると勤務時間付きの記録が一覧に入ること', async () => {
      signInAs();
      const finished = attendanceRecordFixture({
        clock_out_at: '2026-11-08T01:31:00+00:00',
        duration_minutes: 91,
      });
      let historyCall = 0;
      overrideApi(
        attendanceApi.todaySequence(
          workingToday(),
          attendanceTodayFixture('finished', finished),
        ),
        http.get(apiUrl('/api/attendance'), () => {
          historyCall += 1;
          return HttpResponse.json(
            historyCall === 1
              ? emptyHistory()
              : attendanceHistoryFixture([finished]),
          );
        }),
        attendanceApi.clockSucceeds('/api/attendance/clock-out', finished),
      );
      const { user } = await renderRoute('/attendance');
      await expectStatus('勤務中');

      await user.click(clockOutButton());

      await expectStatus('退勤済み');
      expect(historyRows()).toEqual([
        ['2026-11-08', '11/08 09:00', '11/08 10:31', '1時間31分'],
      ]);
    });
  });

  describe('勤怠記録の一覧', () => {
    it('記録がなければ、まだないことを表示すること', async () => {
      signInAs();
      overrideApi(
        attendanceApi.today(notStartedToday()),
        attendanceApi.history(emptyHistory()),
      );

      await renderRoute('/attendance');

      expect(
        await within(historyPanel()).findByText('勤怠記録はまだありません。'),
      ).toBeInTheDocument();
      expect(
        within(historyPanel()).queryByRole('navigation'),
      ).not.toBeInTheDocument();
    });

    it('次へを押すと次のページを読み込み、前へを押せるようにすること', async () => {
      signInAs();
      overrideApi(
        attendanceApi.today(notStartedToday()),
        http.get(apiUrl('/api/attendance'), ({ request }) => {
          const page = Number(new URL(request.url).searchParams.get('page'));
          return HttpResponse.json(
            attendanceHistoryFixture(
              [
                attendanceRecordFixture({
                  id: page,
                  work_date: page === 1 ? '2026-11-08' : '2026-10-08',
                }),
              ],
              { current: page, last: 2 },
            ),
          );
        }),
      );
      const { user } = await renderRoute('/attendance');
      const pages = await within(historyPanel()).findByRole('navigation', {
        name: '勤怠記録のページ',
      });
      expect(pages).toHaveTextContent('1 / 2');
      expect(
        within(pages).getByRole('button', { name: '前へ' }),
      ).toBeDisabled();

      await user.click(within(pages).getByRole('button', { name: '次へ' }));

      await waitFor(() => {
        expect(pages).toHaveTextContent('2 / 2');
      });
      expect(historyRows()[0]?.[0]).toBe('2026-10-08');
      expect(within(pages).getByRole('button', { name: '前へ' })).toBeEnabled();
      expect(
        within(pages).getByRole('button', { name: '次へ' }),
      ).toBeDisabled();
    });

    it('ページ移動中に前の読み込みが遅れて届いても、新しいページの表示を上書きしないこと', async () => {
      signInAs();
      const responses: Record<number, AttendanceHistoryResponse> = {
        1: attendanceHistoryFixture(
          [attendanceRecordFixture({ id: 1, work_date: '2026-11-08' })],
          { current: 1, last: 2 },
        ),
        2: attendanceHistoryFixture(
          [attendanceRecordFixture({ id: 2, work_date: '2026-10-08' })],
          { current: 2, last: 2 },
        ),
      };
      let firstPageRequests = 0;
      let releaseSlowFirstPage: () => void = () => undefined;
      overrideApi(
        attendanceApi.today(notStartedToday()),
        http.get(apiUrl('/api/attendance'), async ({ request }) => {
          const page = Number(new URL(request.url).searchParams.get('page'));

          // 2回目の1ページ目（「前へ」）だけを遅らせる
          if (page === 1 && ++firstPageRequests === 2) {
            await new Promise<void>((resolve) => {
              releaseSlowFirstPage = resolve;
            });
          }

          return HttpResponse.json(responses[page]);
        }),
      );
      const { user } = await renderRoute('/attendance');
      const pages = await within(historyPanel()).findByRole('navigation');
      await user.click(within(pages).getByRole('button', { name: '次へ' }));
      await waitFor(() => expect(pages).toHaveTextContent('2 / 2'));

      // 遅い「前へ」の読み込み中に、もう一度読み込みを始める（再ログイン後の再読み込みと同じ経路）
      await user.click(within(pages).getByRole('button', { name: '前へ' }));
      const auth = useAuthStore();
      const signedInUser = auth.user!;
      // 期限切れと再ログインが同じ tick に起きても読み直すこと
      auth.expireSession();
      auth.signIn(signedInUser);
      await waitFor(() => expect(firstPageRequests).toBe(3));
      releaseSlowFirstPage();

      await waitFor(() => expect(pages).toHaveTextContent('1 / 2'));
      expect(historyRows()[0]?.[0]).toBe('2026-11-08');
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  describe('エラー', () => {
    it('読み込みに失敗したら内部の詳細を出さずに失敗を伝えること', async () => {
      signInAs();
      overrideApi(
        http.get(apiUrl('/api/attendance/today'), () =>
          HttpResponse.json(
            { message: 'SQLSTATE[HY000] /Users/example' },
            { status: 500 },
          ),
        ),
        attendanceApi.history(emptyHistory()),
      );

      await renderRoute('/attendance');

      const alert = await screen.findByRole('alert');
      expect(alert).toHaveTextContent(
        '勤怠を処理できませんでした。時間をおいて再度お試しください。',
      );
      expect(alert).not.toHaveTextContent('SQLSTATE');
      expect(clockInButton()).toBeDisabled();
    });

    it('セッションが切れたら勤怠のエラーは出さず、再ログインを求めること', async () => {
      signInAs();
      overrideApi(
        http.get(apiUrl('/api/attendance/today'), () =>
          HttpResponse.json({ message: 'Unauthenticated.' }, { status: 401 }),
        ),
        attendanceApi.history(emptyHistory()),
      );

      await renderRoute('/attendance');

      expect(
        await screen.findByRole('region', { name: '再ログイン' }),
      ).toBeInTheDocument();
      expect(
        screen.queryByText(
          '勤怠を処理できませんでした。時間をおいて再度お試しください。',
        ),
      ).not.toBeInTheDocument();
    });

    it('再ログインすると勤怠を読み直して表示すること', async () => {
      const user = signInAs();
      let todayCalls = 0;
      overrideApi(
        http.get(apiUrl('/api/attendance/today'), () => {
          todayCalls += 1;
          return todayCalls === 1
            ? HttpResponse.json(
                { message: 'Unauthenticated.' },
                { status: 401 },
              )
            : HttpResponse.json(workingToday());
        }),
        attendanceApi.history(emptyHistory()),
        authApi.loginSucceeds(user),
      );
      const view = await renderRoute('/attendance');
      const relogin = await screen.findByRole('region', { name: '再ログイン' });

      await view.user.type(
        within(relogin).getByLabelText('メールアドレス'),
        'user@example.com',
      );
      await view.user.type(
        within(relogin).getByLabelText('パスワード'),
        'password123',
      );
      await view.user.click(
        within(relogin).getByRole('button', { name: 'ログイン' }),
      );

      await expectStatus('勤務中');
      expect(todayCalls).toBe(2);
    });
  });

  describe('公開デモ', () => {
    it('共通デモであることを案内すること', async () => {
      enableDemoMode();
      signInAs();
      overrideApi(
        attendanceApi.today(notStartedToday()),
        attendanceApi.history(emptyHistory()),
      );

      await renderRoute('/attendance');

      expect(
        screen.getByText(/共通デモのため記録は他の閲覧者にも表示されます。/),
      ).toBeInTheDocument();
    });
  });
});
