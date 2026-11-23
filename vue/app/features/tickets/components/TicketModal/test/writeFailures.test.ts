import { screen } from '@testing-library/vue';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { apiUrl } from '~/test/mocks/apiUrl';
import { overrideApi } from '~/test/mocks/overrideApi';

import { WRITE_MESSAGE } from '../../../constants/ticketMessages';

import { toTicket } from '../../../api/ticketMapper';
import {
  recordUpdates,
  renderModal,
  serverTicket,
  startEditing,
} from './modalFixture';

const failWith = (status: number) => () =>
  HttpResponse.json({ message: 'internal detail' }, { status });

describe('書き込みの失敗の表示', () => {
  it.each([
    [403, 'アクセス権限がありません'],
    [404, '削除されたか、存在しません'],
  ])(
    '保存が %i で失敗したら、案内を表示して保存を無効にすること',
    async (status, message) => {
      overrideApi(recordUpdates(failWith(status)).handler);
      const { user } = await renderModal();
      await startEditing(user);

      await user.click(screen.getByRole('button', { name: '保存' }));

      expect(await screen.findByRole('alert')).toHaveTextContent(message);
      expect(screen.getByRole('button', { name: '保存' })).toBeDisabled();
    },
  );

  it('その他の保存の失敗は、内部の詳細を出さず、やり直せること', async () => {
    overrideApi(recordUpdates(failWith(500)).handler);
    const { user } = await renderModal();
    await startEditing(user);

    await user.click(screen.getByRole('button', { name: '保存' }));

    const alert = await screen.findByRole('alert');
    // 画面の文言は定数から出し、API の文言は使わない
    expect(alert).toHaveTextContent(`${WRITE_MESSAGE.saveFailed} (500)`);
    expect(alert).not.toHaveTextContent('internal detail');
    expect(alert).not.toHaveTextContent('チケット操作に失敗しました');
    expect(screen.getByRole('button', { name: '保存' })).toBeEnabled();
  });

  it('作成の失敗も、内部の詳細を出さず、入力を残すこと', async () => {
    overrideApi(http.post(apiUrl('/api/tickets'), failWith(500)));
    const { user } = await renderModal({ ticket: null });
    await user.type(screen.getByLabelText('タイトル'), 'Keep me');

    await user.click(screen.getByRole('button', { name: '保存' }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(`${WRITE_MESSAGE.saveFailed} (500)`);
    expect(alert).not.toHaveTextContent('internal detail');
    expect(screen.getByLabelText('タイトル')).toHaveValue('Keep me');
  });

  it('保存の失敗の表示では、取得したチケットは変えないこと', async () => {
    overrideApi(recordUpdates(failWith(500)).handler);
    const { user } = await renderModal({ ticket: toTicket(serverTicket) });
    await startEditing(user);

    await user.click(screen.getByRole('button', { name: '保存' }));
    await screen.findByRole('alert');
    await user.click(screen.getByRole('button', { name: 'キャンセル' }));

    expect(screen.getByText(serverTicket.title)).toBeInTheDocument();
  });
});
