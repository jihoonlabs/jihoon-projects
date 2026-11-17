import { createError } from '#imports';
import { mockNuxtImport } from '@nuxt/test-utils/runtime';
import { screen, waitFor } from '@testing-library/vue';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import ErrorPage from '~/error.vue';
import { renderScreen } from '~/test/renderScreen';

const { clearErrorMock } = vi.hoisted(() => ({ clearErrorMock: vi.fn() }));
mockNuxtImport('clearError', () => clearErrorMock);

const renderErrorPage = (statusCode: number, message: string) =>
  renderScreen(ErrorPage, {
    props: { error: createError({ statusCode, message }) },
  });

describe('エラー画面', () => {
  beforeEach(() => {
    clearErrorMock.mockClear();
  });

  it('ページがなければ、見つからないことを伝えること', async () => {
    await renderErrorPage(404, 'Page not found: /no-such-page');

    expect(
      screen.getByRole('heading', { name: 'ページが見つかりません' }),
    ).toBeInTheDocument();
    expect(
      screen.getByText('URL が正しいかご確認ください。'),
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(document.title).toBe('ページが見つかりません | タスク管理');
    });
  });

  it('それ以外のエラーでは、内部の詳細を出さずに失敗を伝えること', async () => {
    await renderErrorPage(500, 'SQLSTATE[HY000]: connection refused');

    expect(
      screen.getByRole('heading', { name: 'エラーが発生しました' }),
    ).toBeInTheDocument();
    expect(
      screen.getByText('時間をおいて、もう一度お試しください。'),
    ).toBeInTheDocument();
    expect(screen.queryByText(/SQLSTATE/)).not.toBeInTheDocument();
    await waitFor(() => {
      expect(document.title).toBe('エラーが発生しました | タスク管理');
    });
  });

  it('トップへ戻ると、エラーを消してトップへ移すこと', async () => {
    const { user } = await renderErrorPage(404, 'Page not found: /x');

    await user.click(screen.getByRole('button', { name: 'トップへ戻る' }));

    expect(clearErrorMock).toHaveBeenCalledTimes(1);
    expect(clearErrorMock).toHaveBeenCalledWith({ redirect: '/' });
  });
});
