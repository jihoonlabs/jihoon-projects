import { screen, waitFor } from '@testing-library/vue';
import { describe, expect, it } from 'vitest';

import { signInAs, signedOut } from '~/test/auth/signInAs';
import { attendanceApi } from '~/test/mocks/attendance/attendanceApiHandlers';
import { overrideApi } from '~/test/mocks/overrideApi';
import { expectPath, renderRoute } from '~/test/renderRoute';

const expectTabTitle = async (title: string) => {
  await waitFor(() => {
    expect(document.title).toBe(title);
  });
};

describe('タブの画面名', () => {
  it.each([
    ['/login', 'ログイン | タスク管理'],
    ['/register', '会員登録 | タスク管理'],
    ['/forgot-password', 'パスワードをお忘れの方 | タスク管理'],
    [
      '/reset-password?email=user%40example.com&token=reset-token',
      'パスワード再設定 | タスク管理',
    ],
  ])(
    '未ログインで %s を開くと、タブに「%s」と出すこと',
    async (path, title) => {
      signedOut();

      await renderRoute(path);

      await expectTabTitle(title);
    },
  );

  it.each([
    ['/attendance', '勤怠管理 | タスク管理'],
    ['/tickets', 'チケット管理 | タスク管理'],
  ])(
    'ログイン済みで %s を開くと、タブに「%s」と出すこと',
    async (path, title) => {
      signInAs();
      overrideApi(...attendanceApi.emptyHome());

      await renderRoute(path);

      await expectTabTitle(title);
    },
  );

  it('別の画面へ移ると、移った先の画面名に変わること', async () => {
    signedOut();
    const { router } = await renderRoute('/login');
    await expectTabTitle('ログイン | タスク管理');

    await router.push('/register');

    await expectPath('/register');
    expect(
      await screen.findByRole('heading', { name: '会員登録' }),
    ).toBeInTheDocument();
    await expectTabTitle('会員登録 | タスク管理');
  });
});
