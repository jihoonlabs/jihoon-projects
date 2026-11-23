import { screen, waitFor } from '@testing-library/vue';
import { http, HttpResponse } from 'msw';
import { describe, expect, it, vi } from 'vitest';

import { deferred } from '~/test/deferred';
import { apiUrl } from '~/test/mocks/apiUrl';
import { overrideApi } from '~/test/mocks/overrideApi';

import { WRITE_MESSAGE } from '../../../constants/ticketMessages';

import {
  recordUpdates,
  renderModal,
  savedResponse,
  startEditing,
} from './modalFixture';

const deleteHandler = (respond: () => Response | Promise<Response>) => {
  const calls: string[] = [];
  const handler = http.delete(apiUrl('/api/tickets/1'), () => {
    calls.push('delete');

    return respond();
  });

  return { handler, calls };
};

const confirmAs = (answer: boolean) =>
  vi.spyOn(window, 'confirm').mockReturnValue(answer);

describe('チケットの削除', () => {
  it('確認に答えると削除し、モーダルを閉じること', async () => {
    const deletion = deleteHandler(
      () => new HttpResponse(null, { status: 204 }),
    );
    overrideApi(deletion.handler);
    const confirm = confirmAs(true);
    const { user, onClose } = await renderModal();

    await user.click(await screen.findByRole('button', { name: '削除' }));

    await waitFor(() => expect(onClose).toHaveBeenCalledTimes(1));
    expect(confirm).toHaveBeenCalledWith('TICK-1 を削除しますか？');
    expect(deletion.calls).toEqual(['delete']);
  });

  it('確認で取り消したら、削除しないこと', async () => {
    const deletion = deleteHandler(
      () => new HttpResponse(null, { status: 204 }),
    );
    overrideApi(deletion.handler);
    confirmAs(false);
    const { user, onClose } = await renderModal();

    await user.click(await screen.findByRole('button', { name: '削除' }));

    expect(deletion.calls).toEqual([]);
    expect(onClose).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: '編集' })).toBeEnabled();
  });

  it('削除に失敗したら、閉じずにエラーを表示すること', async () => {
    overrideApi(
      deleteHandler(() => HttpResponse.json({ message: 'x' }, { status: 500 }))
        .handler,
    );
    confirmAs(true);
    const { user, onClose } = await renderModal();

    await user.click(await screen.findByRole('button', { name: '削除' }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(`${WRITE_MESSAGE.deleteFailed} (500)`);
    expect(alert).not.toHaveTextContent('チケット操作に失敗しました');
    expect(onClose).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: '削除' })).toBeEnabled();
  });

  describe('削除の最中に編集へ入り、削除が失敗したとき', () => {
    const enterEditWhileDeleting = async () => {
      const gate = deferred();
      overrideApi(
        deleteHandler(async () => {
          await gate.promise;

          return HttpResponse.json({ message: 'x' }, { status: 500 });
        }).handler,
      );
      confirmAs(true);
      const view = await renderModal();
      await view.user.click(
        await screen.findByRole('button', { name: '削除' }),
      );
      expect(screen.getByRole('button', { name: '閉じる' })).toBeDisabled();
      expect(screen.getByRole('button', { name: '編集' })).toBeEnabled();

      await view.user.click(screen.getByRole('button', { name: '編集' }));
      expect(screen.getByRole('button', { name: '保存中...' })).toBeDisabled();
      gate.resolve();
      expect(await screen.findByRole('alert')).toHaveTextContent('500');
      await waitFor(() =>
        expect(screen.getByRole('button', { name: '保存' })).toBeEnabled(),
      );

      return view;
    };

    it('後の保存の失敗を表示し、削除のエラーは残さないこと', async () => {
      const gate = deferred();
      const updates = recordUpdates(async () => {
        await gate.promise;

        return HttpResponse.json({ message: 'y' }, { status: 503 });
      });
      overrideApi(updates.handler);
      const { user } = await enterEditWhileDeleting();

      await user.click(screen.getByRole('button', { name: '保存' }));
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: '保存中...' })).toBeDisabled();
      gate.resolve();

      expect(await screen.findByRole('alert')).toHaveTextContent('503');
      expect(screen.queryByText(/\(500\)/)).not.toBeInTheDocument();
      expect(updates.bodies).toHaveLength(1);
    });

    it('後の保存が成功したら、削除のエラーを消すこと', async () => {
      overrideApi(
        recordUpdates(() => savedResponse({ title: 'Saved' })).handler,
      );
      const { user } = await enterEditWhileDeleting();

      await user.click(screen.getByRole('button', { name: '保存' }));

      expect(await screen.findByText('Saved')).toBeInTheDocument();
      expect(
        screen.getByRole('heading', { name: 'チケット詳細' }),
      ).toBeInTheDocument();
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  it('編集の取り消しで、入力を最後に保存できた内容へ戻すこと', async () => {
    const { user } = await renderModal();
    await startEditing(user);
    await user.clear(screen.getByLabelText('タイトル'));
    await user.type(screen.getByLabelText('タイトル'), 'Draft');

    await user.click(screen.getByRole('button', { name: 'キャンセル' }));
    await startEditing(user);

    expect(screen.getByLabelText('タイトル')).toHaveValue('First ticket');
  });
});
