import { screen, waitFor } from '@testing-library/vue';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { deferred } from '~/test/deferred';
import { apiUrl } from '~/test/mocks/apiUrl';
import { overrideApi } from '~/test/mocks/overrideApi';

import { toTicket } from '../../../api/ticketMapper';
import {
  recordUpdates,
  renderModal,
  savedResponse,
  serverTicket,
  startEditing,
} from './modalFixture';

const FIELD_LABELS = ['タイトル', '説明', 'ステータス', '優先度', '担当者'];

/**
 * 保存の最中は入力欄を触れなくし、失敗したら入力を残したまま触れる状態に戻す
 */
const assertDraftFieldsUnlockAfterFailedSave = async (
  mode: 'create' | 'edit',
) => {
  const gate = deferred();
  const failing = async () => {
    await gate.promise;

    return HttpResponse.json({ message: 'Error' }, { status: 500 });
  };
  overrideApi(
    mode === 'create'
      ? http.post(apiUrl('/api/tickets'), failing)
      : recordUpdates(failing).handler,
  );
  const { user } = await renderModal({
    ticket: mode === 'create' ? null : toTicket(serverTicket),
  });
  if (mode === 'edit') await startEditing(user);

  const title = screen.getByLabelText('タイトル');
  await user.clear(title);
  await user.type(title, 'Submitted draft');
  await user.type(screen.getByLabelText('説明'), 'Draft description');
  await user.click(screen.getByRole('button', { name: '保存' }));

  for (const label of FIELD_LABELS) {
    expect(screen.getByLabelText(label)).toBeDisabled();
  }
  await user.type(title, ' unsent input');

  gate.resolve();
  await screen.findByRole('alert');

  expect(title).toHaveValue('Submitted draft');
  expect(screen.getByLabelText('説明')).toHaveValue('Draft description');
  for (const label of FIELD_LABELS) {
    expect(screen.getByLabelText(label)).toBeEnabled();
  }
  expect(screen.getByRole('button', { name: '保存' })).toBeEnabled();
};

describe('保存の流れ', () => {
  it('作成に失敗したら、入力を残したまま入力欄を操作できる状態に戻すこと', () =>
    assertDraftFieldsUnlockAfterFailedSave('create'));

  it('編集の保存に失敗したら、入力を残したまま入力欄を操作できる状態に戻すこと', () =>
    assertDraftFieldsUnlockAfterFailedSave('edit'));

  it('保存の最中は、背景のクリックや Escape で閉じないこと', async () => {
    const gate = deferred();
    overrideApi(
      recordUpdates(async () => {
        await gate.promise;

        return savedResponse({});
      }).handler,
    );
    const { user, onClose } = await renderModal();
    await startEditing(user);
    await user.click(screen.getByRole('button', { name: '保存' }));

    await user.click(screen.getByRole('dialog').parentElement!);
    await user.keyboard('{Escape}');

    expect(onClose).not.toHaveBeenCalled();
    gate.resolve();
    await screen.findByRole('heading', { name: 'チケット詳細' });
  });

  it('保存できた版を次の編集の基準にし、担当者を変えていなければ送らないこと', async () => {
    const updates = recordUpdates(() => savedResponse({ assignee: null }));
    overrideApi(updates.handler);
    const { user } = await renderModal();
    await startEditing(user);
    await user.selectOptions(screen.getByLabelText('担当者'), '未割り当て');
    await user.click(screen.getByRole('button', { name: '保存' }));

    await startEditing(user);
    expect(screen.getByLabelText('担当者')).toHaveValue('');
    await user.click(screen.getByRole('button', { name: '保存' }));

    await waitFor(() => expect(updates.bodies).toHaveLength(2));
    expect(updates.bodies[0]).toMatchObject({
      expected_version: 1,
      assignee_id: null,
    });
    expect(updates.bodies[1]).toMatchObject({ expected_version: 2 });
    expect(updates.bodies[1]).not.toHaveProperty('assignee_id');
  });

  it('応答の項目とバージョンを同じスナップショットとして採用すること', async () => {
    const updates = recordUpdates(() =>
      savedResponse({
        title: 'Canonical newer title',
        description: 'Server description',
        status: 'DONE',
        priority: 'LOW',
        assignee: null,
        version: 7,
      }),
    );
    overrideApi(updates.handler);
    const { user } = await renderModal();
    await startEditing(user);
    const title = screen.getByLabelText('タイトル');
    await user.clear(title);
    await user.type(title, 'Submitted title');
    await user.click(screen.getByRole('button', { name: '保存' }));
    expect(
      await screen.findByText('Canonical newer title'),
    ).toBeInTheDocument();

    await startEditing(user);

    expect(screen.getByLabelText('タイトル')).toHaveValue(
      'Canonical newer title',
    );
    expect(screen.getByLabelText('説明')).toHaveValue('Server description');
    expect(screen.getByLabelText('ステータス')).toHaveValue('DONE');
    expect(screen.getByLabelText('優先度')).toHaveValue('LOW');
    expect(screen.getByLabelText('担当者')).toHaveValue('');
    await user.click(screen.getByRole('button', { name: '保存' }));
    await waitFor(() => expect(updates.bodies).toHaveLength(2));
    expect(updates.bodies[1]).toMatchObject({
      title: 'Canonical newer title',
      expected_version: 7,
    });
  });
});
