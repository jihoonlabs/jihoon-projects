import { screen, waitFor } from '@testing-library/vue';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { deferred } from '~/test/deferred';
import { apiUrl } from '~/test/mocks/apiUrl';
import { overrideApi } from '~/test/mocks/overrideApi';
import { ticketApi } from '~/test/mocks/tickets/ticketApiHandlers';

import { ticketFixture } from '../../../api/test/ticketFixture';
import { toTicket } from '../../../api/ticketMapper';
import {
  recordUpdates,
  renderModal,
  savedResponse,
  serverTicket,
  startEditing,
} from './modalFixture';

describe('チケット詳細の取得（最新性）', () => {
  it('取得中はカードの古い内容を隠し、最新の内容で編集の基準バージョンを決めること', async () => {
    const gate = deferred();
    const updates = recordUpdates(() => savedResponse({}));
    overrideApi(
      http.get(apiUrl('/api/tickets/1'), async () => {
        await gate.promise;

        return HttpResponse.json({
          data: { ...serverTicket, title: 'Changed elsewhere', version: 8 },
        });
      }),
      updates.handler,
    );
    const { user } = await renderModal({ detail: null });

    expect(await screen.findByRole('status')).toHaveTextContent(
      '最新情報を取得中',
    );
    expect(screen.queryByText(serverTicket.title)).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: '編集' }),
    ).not.toBeInTheDocument();

    gate.resolve();
    expect(await screen.findByText('Changed elsewhere')).toBeInTheDocument();
    await startEditing(user);
    await user.click(screen.getByRole('button', { name: '保存' }));

    await waitFor(() => expect(updates.bodies).toHaveLength(1));
    expect(updates.bodies[0]).toMatchObject({ expected_version: 8 });
  });

  it.each([
    ['通信に失敗', 500, '最新のチケット情報を取得できませんでした'],
    ['削除済み', 404, '削除されたか、存在しません'],
    ['権限なし', 403, 'アクセス権限がありません'],
  ])(
    '%sのときは古い内容で編集させず、再試行で表示できること',
    async (_name, status, message) => {
      let calls = 0;
      overrideApi(
        http.get(apiUrl('/api/tickets/1'), () =>
          ++calls === 1
            ? HttpResponse.json({ message: 'Error' }, { status })
            : HttpResponse.json({ data: serverTicket }),
        ),
      );
      const { user } = await renderModal({ detail: null });

      expect(await screen.findByRole('alert')).toHaveTextContent(message);
      expect(
        screen.queryByRole('button', { name: '編集' }),
      ).not.toBeInTheDocument();

      await user.click(screen.getByRole('button', { name: '再試行' }));

      expect(await screen.findByText(serverTicket.title)).toBeInTheDocument();
    },
  );

  it('ログインの期限切れ（401）のときは権限なしの案内を出し、編集させないこと', async () => {
    overrideApi(ticketApi.ticketFail('1', 401));
    await renderModal({ detail: null });

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'アクセス権限がありません',
    );
    expect(
      screen.queryByRole('button', { name: '編集' }),
    ).not.toBeInTheDocument();
  });

  it('別のチケットに切り替えたら、前の要求を中断し、遅れて届いた応答で上書きしないこと', async () => {
    const first = deferred();
    let firstAborted = false;
    overrideApi(
      http.get(apiUrl('/api/tickets/1'), async ({ request }) => {
        request.signal.addEventListener('abort', () => {
          firstAborted = true;
        });
        await first.promise;

        return HttpResponse.json({
          data: { ...serverTicket, title: 'Late first' },
        });
      }),
      ticketApi.ticket(ticketFixture({ id: '2', title: 'Latest second' })),
    );
    const { rerender } = await renderModal({ detail: null });

    await rerender({
      ticket: toTicket(ticketFixture({ id: '2', title: 'Old second' })),
    });
    expect(await screen.findByText('Latest second')).toBeInTheDocument();
    await waitFor(() => expect(firstAborted).toBe(true));

    first.resolve();
    await new Promise((resolve) => setTimeout(resolve, 20));

    expect(screen.queryByText('Late first')).not.toBeInTheDocument();
    expect(screen.getByText('Latest second')).toBeInTheDocument();
  });

  it('切り替え前のチケットの失敗が遅れて届いても、エラーを表示しないこと', async () => {
    const first = deferred();
    overrideApi(
      http.get(apiUrl('/api/tickets/1'), async () => {
        await first.promise;

        return HttpResponse.json({ message: 'denied' }, { status: 403 });
      }),
      ticketApi.ticket(ticketFixture({ id: '2', title: 'Second ticket' })),
    );
    const { rerender } = await renderModal({ detail: null });

    await rerender({ ticket: toTicket(ticketFixture({ id: '2' })) });
    await screen.findByText('Second ticket');
    first.resolve();
    await new Promise((resolve) => setTimeout(resolve, 20));

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
