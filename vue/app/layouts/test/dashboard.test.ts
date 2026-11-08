import { screen, waitFor } from '@testing-library/vue';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { useProtectedApi } from '~/features/auth/api/protectedRequest';
import { useAuthStore } from '~/features/auth/stores/authStore';
import { userFixture } from '~/features/auth/test/userFixture';
import { attendanceApi } from '~/test/attendance/attendanceApiHandlers';
import { authApi } from '~/test/auth/authApiHandlers';
import { signInAs, signedOut } from '~/test/auth/signInAs';
import { apiUrl } from '~/test/msw/apiUrl';
import { overrideApi } from '~/test/msw/overrideApi';
import { expectPath, renderRoute } from '~/test/renderRoute';

const expireByUnauthorizedResponse = async () => {
  overrideApi(
    http.get(apiUrl('/api/tickets'), () =>
      HttpResponse.json({ message: 'Unauthenticated.' }, { status: 401 }),
    ),
  );

  await useProtectedApi()
    .getJson('/api/tickets')
    .catch(() => undefined);
};

describe('ログインが必要な画面', () => {
  describe('セッション復元', () => {
    it('Laravel のセッションが有効なら、開いた画面をそのまま表示すること', async () => {
      overrideApi(authApi.currentUser(userFixture({ name: '佐藤 一郎' })));

      await renderRoute('/tickets');

      expect(
        await screen.findByRole('heading', { name: 'チケット管理' }),
      ).toBeInTheDocument();
      await expectPath('/tickets');
      expect(screen.getByRole('banner')).toHaveTextContent(
        'ようこそ、佐藤 一郎 さん（一般ユーザー）',
      );
    });

    it('未ログイン（401）ならログイン画面へ移すこと', async () => {
      overrideApi(authApi.unauthenticated());

      await renderRoute('/tickets');

      await expectPath('/login');
      expect(
        await screen.findByRole('button', { name: 'ログイン' }),
      ).toBeInTheDocument();
      expect(
        screen.queryByRole('heading', { name: 'チケット管理' }),
      ).not.toBeInTheDocument();
    });
  });

  describe('トップページ', () => {
    it('未ログインならログイン画面へ移すこと', async () => {
      signedOut();

      await renderRoute('/');

      await expectPath('/login');
    });

    it('ログイン済みなら勤怠画面へ移すこと', async () => {
      signInAs();
      overrideApi(...attendanceApi.emptyHome());

      await renderRoute('/');

      await expectPath('/attendance');
    });
  });

  describe('セッション期限切れ', () => {
    it('期限切れになると本文を隠して操作できなくし、同じ画面で再ログインを求めること', async () => {
      signInAs();
      await renderRoute('/tickets');
      await screen.findByRole('heading', { name: 'チケット管理' });

      await expireByUnauthorizedResponse();

      const relogin = await screen.findByRole('region', {
        name: '再ログイン',
      });
      expect(relogin).toHaveTextContent(
        'セッションの有効期限が切れました。再ログインしてください。',
      );
      expect(
        screen.queryByRole('heading', { name: 'チケット管理' }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole('button', { name: 'ログアウト' }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole('link', { name: 'Googleでログイン' }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole('link', { name: '新規会員登録へ' }),
      ).not.toBeInTheDocument();
      expect(document.querySelector('[inert]')).not.toBeNull();
      await expectPath('/tickets');
    });

    it('同じアカウントで再ログインすると、移動せずに元の画面へ戻ること', async () => {
      const original = signInAs(userFixture({ id: 9, name: '同じ利用者' }));
      const { user } = await renderRoute('/tickets');
      await screen.findByRole('heading', { name: 'チケット管理' });
      await expireByUnauthorizedResponse();
      await screen.findByRole('region', { name: '再ログイン' });
      overrideApi(authApi.loginSucceeds(original));

      await user.type(
        screen.getByLabelText('メールアドレス'),
        'same@example.com',
      );
      await user.type(screen.getByLabelText('パスワード'), 'password123');
      await user.click(screen.getByRole('button', { name: 'ログイン' }));

      expect(
        await screen.findByRole('heading', { name: 'チケット管理' }),
      ).toBeVisible();
      expect(
        screen.queryByRole('region', { name: '再ログイン' }),
      ).not.toBeInTheDocument();
      expect(useAuthStore().sessionExpired).toBe(false);
      await expectPath('/tickets');
    });
  });

  describe('ログアウト', () => {
    it('ログアウトするとログイン画面へ移り、ログイン状態を消すこと', async () => {
      signInAs();
      overrideApi(authApi.logoutSucceeds());
      const { user } = await renderRoute('/tickets');
      await screen.findByRole('heading', { name: 'チケット管理' });

      await user.click(screen.getByRole('button', { name: 'ログアウト' }));

      await expectPath('/login');
      expect(useAuthStore().isAuthenticated).toBe(false);
    });

    it('ログアウトに失敗したらエラーを表示し、画面とログイン状態を保つこと', async () => {
      signInAs();
      overrideApi(authApi.logoutFails());
      const { user } = await renderRoute('/tickets');
      await screen.findByRole('heading', { name: 'チケット管理' });

      await user.click(screen.getByRole('button', { name: 'ログアウト' }));

      expect(await screen.findByRole('alert')).toHaveTextContent(
        'ログアウトできませんでした。もう一度お試しください。',
      );
      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: 'ログアウト' }),
        ).toBeEnabled();
      });
      expect(useAuthStore().isAuthenticated).toBe(true);
      await expectPath('/tickets');
    });
  });
});
