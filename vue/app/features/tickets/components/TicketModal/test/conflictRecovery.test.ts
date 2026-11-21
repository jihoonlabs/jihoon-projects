import { screen, waitFor, within } from '@testing-library/vue';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { deferred } from '~/test/deferred';
import { apiUrl } from '~/test/mocks/apiUrl';
import { overrideApi } from '~/test/mocks/overrideApi';
import { ticketApi } from '~/test/mocks/tickets/ticketApiHandlers';

import { ticketFixture } from '../../../api/test/ticketFixture';
import { toTicket } from '../../../api/ticketMapper';
import type { TicketResponse } from '../../../types/ticket';
import {
  conflictResponse,
  recordUpdates,
  renderModal,
  savedResponse,
  serveTicket,
  serverTicket,
  startEditing,
} from './modalFixture';

const RELOAD = '最新情報を再取得';
const ADOPT = '最新情報で編集し直す（入力を置き換える）';

const field = (label: string) => screen.getByLabelText(label);

describe('競合（409）の回復', () => {
  it('競合しても入力を保ち、自動で再送せず、明示操作で最新の内容から編集し直せること', async () => {
    let current: TicketResponse = serverTicket;
    const updates = recordUpdates(conflictResponse);
    overrideApi(
      serveTicket(() => current),
      updates.handler,
    );
    const { user } = await renderModal({ detail: null });
    await startEditing(user);
    await user.clear(field('タイトル'));
    await user.type(field('タイトル'), 'My draft');
    await user.type(field('説明'), 'Draft description');
    await user.selectOptions(field('優先度'), '高');
    await user.selectOptions(field('担当者'), '未割り当て');
    await user.click(screen.getByRole('button', { name: '保存' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      '入力内容は保持',
    );
    expect(screen.getByRole('button', { name: '保存' })).toBeDisabled();

    current = { ...serverTicket, title: 'Other saved', version: 4 };
    await user.click(screen.getByRole('button', { name: RELOAD }));
    expect(
      await screen.findByText('タイトル: Other saved'),
    ).toBeInTheDocument();

    expect(field('タイトル')).toHaveValue('My draft');
    expect(field('説明')).toHaveValue('Draft description');
    expect(field('優先度')).toHaveValue('HIGH');
    expect(field('担当者')).toHaveValue('');
    expect(updates.bodies).toHaveLength(1);
    expect(screen.getByRole('button', { name: '保存' })).toBeDisabled();

    updates.bodies.length = 0;
    overrideApi(
      http.patch(apiUrl('/api/tickets/1'), async ({ request }) => {
        updates.bodies.push((await request.json()) as Record<string, unknown>);

        return savedResponse({ title: 'Other saved', version: 5 });
      }),
    );
    await user.click(screen.getByRole('button', { name: ADOPT }));
    expect(field('タイトル')).toHaveValue('Other saved');
    await user.click(screen.getByRole('button', { name: '保存' }));

    await waitFor(() => expect(updates.bodies).toHaveLength(1));
    expect(updates.bodies[0]).toMatchObject({ expected_version: 4 });
  });

  it('再取得に失敗・権限を失っても入力を保ち、保存を再び有効にしないこと', async () => {
    let reloads = 0;
    overrideApi(
      http.get(apiUrl('/api/tickets/1'), () => {
        reloads += 1;
        if (reloads === 1) return HttpResponse.json({ data: serverTicket });
        if (reloads === 2) {
          return HttpResponse.json({ message: 'Error' }, { status: 500 });
        }

        return HttpResponse.json({ message: 'denied' }, { status: 403 });
      }),
      recordUpdates(conflictResponse).handler,
    );
    const { user } = await renderModal({ detail: null });
    await startEditing(user);
    await user.clear(field('タイトル'));
    await user.type(field('タイトル'), 'Protected draft');
    await user.click(screen.getByRole('button', { name: '保存' }));
    await screen.findByRole('alert');

    await user.click(screen.getByRole('button', { name: RELOAD }));
    const panel = within(screen.getByRole('region', { name: '競合の解決' }));
    expect(await panel.findByRole('alert')).toHaveTextContent('取得できません');

    await user.click(screen.getByRole('button', { name: RELOAD }));
    await waitFor(() =>
      expect(panel.getByRole('alert')).toHaveTextContent('アクセス権限'),
    );
    expect(field('タイトル')).toHaveValue('Protected draft');
    expect(screen.getByRole('button', { name: '保存' })).toBeDisabled();
  });

  it('ticket_conflict ではない 409 は、版の競合として扱わないこと', async () => {
    overrideApi(
      recordUpdates(() =>
        HttpResponse.json({ message: 'Archived' }, { status: 409 }),
      ).handler,
    );
    const { user } = await renderModal();
    await startEditing(user);

    await user.click(screen.getByRole('button', { name: '保存' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('409');
    expect(
      screen.queryByRole('button', { name: RELOAD }),
    ).not.toBeInTheDocument();
  });

  const startSaveThenSwitchTicket = async (outcome: 'success' | 'conflict') => {
    const gate = deferred();
    overrideApi(
      recordUpdates(async () => {
        await gate.promise;

        return outcome === 'success'
          ? savedResponse({ title: 'Late save' })
          : conflictResponse();
      }).handler,
      ticketApi.ticket(ticketFixture({ id: '2', title: 'Second ticket' })),
    );
    const view = await renderModal();
    await startEditing(view.user);
    await view.user.click(screen.getByRole('button', { name: '保存' }));
    await view.rerender({ ticket: toTicket(ticketFixture({ id: '2' })) });
    await screen.findByText('Second ticket');
    gate.resolve();
    await new Promise((resolve) => setTimeout(resolve, 20));
  };

  it.each(['success', 'conflict'] as const)(
    '別のチケットに切り替えたあとに届いた保存の%s結果は、画面に反映しないこと',
    async (outcome) => {
      await startSaveThenSwitchTicket(outcome);

      expect(screen.getByText('Second ticket')).toBeInTheDocument();
      expect(screen.queryByText('Late save')).not.toBeInTheDocument();
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    },
  );

  it.each(['success', 'forbidden'] as const)(
    '別のチケットに切り替えたあとに届いた再取得の%s結果は、画面に反映しないこと',
    async (outcome) => {
      const gate = deferred();
      let reloads = 0;
      overrideApi(
        http.get(apiUrl('/api/tickets/1'), async () => {
          if (++reloads === 1) return HttpResponse.json({ data: serverTicket });
          await gate.promise;

          return outcome === 'success'
            ? HttpResponse.json({
                data: { ...serverTicket, title: 'Late reload', version: 9 },
              })
            : HttpResponse.json({ message: 'denied' }, { status: 403 });
        }),
        recordUpdates(conflictResponse).handler,
        ticketApi.ticket(ticketFixture({ id: '2', title: 'Second ticket' })),
      );
      const { user, rerender } = await renderModal({ detail: null });
      await startEditing(user);
      await user.click(screen.getByRole('button', { name: '保存' }));
      await screen.findByRole('alert');
      await user.click(screen.getByRole('button', { name: RELOAD }));
      await rerender({ ticket: toTicket(ticketFixture({ id: '2' })) });
      await screen.findByText('Second ticket');

      gate.resolve();
      await new Promise((resolve) => setTimeout(resolve, 20));

      expect(screen.getByText('Second ticket')).toBeInTheDocument();
      expect(screen.queryByText('Late reload')).not.toBeInTheDocument();
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    },
  );
});
