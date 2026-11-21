import { screen, within } from '@testing-library/vue';
import { describe, expect, it } from 'vitest';

import { signInAs } from '~/test/auth/signInAs';
import { overrideApi } from '~/test/mocks/overrideApi';
import { ticketApi } from '~/test/mocks/tickets/ticketApiHandlers';
import { renderRoute } from '~/test/renderRoute';

import { projectFixture } from '../../../api/test/projectFixture';
import { ticketFixture } from '../../../api/test/ticketFixture';

const openTicket = async (title: string) => {
  signInAs();
  overrideApi(ticketApi.projects([projectFixture({ id: '1', name: 'Alpha' })]));
  overrideApi(
    ticketApi.tickets([
      ticketFixture({
        id: '1',
        title,
        description: '1行目\n2行目',
        assignee: null,
        priority: 'HIGH',
      }),
    ]),
  );
  const { user } = await renderRoute('/tickets');
  await user.click(await screen.findByRole('button', { name: title }));
  return { user, dialog: await screen.findByRole('dialog') };
};

describe('チケット詳細モーダル', () => {
  it('カードのタイトルを押すと、詳細を表示すること', async () => {
    const { dialog } = await openTicket('Login bug');

    expect(
      within(dialog).getByRole('heading', { name: 'チケット詳細' }),
    ).toBeInTheDocument();
    expect(within(dialog).getByText('TICK-1')).toBeInTheDocument();
    expect(within(dialog).getByText('Login bug')).toBeInTheDocument();
    expect(within(dialog).getByText('TODO')).toBeInTheDocument();
    expect(within(dialog).getByText('高')).toBeInTheDocument();
    expect(within(dialog).getByText('未割り当て')).toBeInTheDocument();
  });

  it('説明の改行を保ったまま表示すること', async () => {
    const { dialog } = await openTicket('Docs');

    expect(within(dialog).getByText(/1行目/).textContent).toBe('1行目\n2行目');
  });

  it('閉じるボタンで閉じること', async () => {
    const { user } = await openTicket('Close me');

    await user.click(screen.getByRole('button', { name: '閉じる' }));

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('Escape キーで閉じること', async () => {
    const { user } = await openTicket('Escape me');

    await user.keyboard('{Escape}');

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('背景を押すと閉じること', async () => {
    const { user, dialog } = await openTicket('Backdrop');

    await user.click(dialog.parentElement!);

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});
