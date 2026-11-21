import { screen, waitFor, within } from '@testing-library/vue';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { useAuthStore } from '~/features/auth/store/useAuthStore';
import { deferred } from '~/test/deferred';
import { apiUrl } from '~/test/mocks/apiUrl';

import { projectMemberFixture } from '../../../api/test/projectFixture';
import { CREATE_BUTTON, openBoard, settle } from './ticketWritesFixture';

const createButton = () =>
  screen.queryByRole('button', { name: CREATE_BUTTON });
const openCard = async (user: { click: (el: Element) => Promise<void> }) => {
  await user.click(await screen.findByRole('button', { name: 'Alpha task' }));
  return screen.findByRole('dialog');
};

describe('チケットボードの書き込み権限', () => {
  describe('権限による表示', () => {
    it('書き込み権限があれば、作成ボタンを出し、詳細に編集・削除を出すこと', async () => {
      const { user } = await openBoard({ permission: 'write' });

      expect(
        await screen.findByRole('button', { name: CREATE_BUTTON }),
      ).toBeInTheDocument();
      const dialog = await openCard(user);
      expect(
        await within(dialog).findByRole('button', { name: '編集' }),
      ).toBeInTheDocument();
      expect(
        within(dialog).getByRole('button', { name: '削除' }),
      ).toBeInTheDocument();
    });

    it('読み取りだけなら、作成ボタンも編集・削除も出さないこと', async () => {
      const { user, membersServed } = await openBoard({ permission: 'read' });
      await screen.findByRole('button', { name: 'Alpha task' });
      await waitFor(() => expect(membersServed()).toBe(true));
      await settle();

      expect(createButton()).not.toBeInTheDocument();
      const dialog = await openCard(user);
      await within(dialog).findByText('Alpha task');
      expect(
        within(dialog).queryByRole('button', { name: '編集' }),
      ).not.toBeInTheDocument();
      expect(
        within(dialog).queryByRole('button', { name: '削除' }),
      ).not.toBeInTheDocument();
    });

    it('管理者は、メンバーでなくても作成できること', async () => {
      await openBoard({ role: 'admin', member: false });

      expect(
        await screen.findByRole('button', { name: CREATE_BUTTON }),
      ).toBeInTheDocument();
    });

    it('アーカイブ済みのプロジェクトでは、作成ボタンを出さないこと', async () => {
      const { membersServed } = await openBoard({ archived: true });
      await screen.findByRole('button', { name: 'Alpha task' });
      await waitFor(() => expect(membersServed()).toBe(true));
      await settle();

      expect(createButton()).not.toBeInTheDocument();
    });
  });

  describe('再ログイン後の権限', () => {
    it('再ログインして読み取りだけになったら、作成ボタンを隠すこと', async () => {
      let served = 0;
      await openBoard({
        membersHandler: http.get(apiUrl('/api/projects/1/members'), () =>
          HttpResponse.json({
            data: [
              projectMemberFixture({
                permission: ++served === 1 ? 'write' : 'read',
              }),
            ],
          }),
        ),
      });
      await screen.findByRole('button', { name: CREATE_BUTTON });

      useAuthStore().signIn(useAuthStore().user!);

      await waitFor(() => expect(served).toBe(2));
      await settle();
      expect(createButton()).not.toBeInTheDocument();
    });

    it('前のセッションのメンバー応答が遅れて届いても、新しい読み取り権限を維持すること', async () => {
      const gate = deferred();
      let served = 0;
      await openBoard({
        membersHandler: http.get(
          apiUrl('/api/projects/1/members'),
          async () => {
            if (++served === 1) {
              await gate.promise;

              return HttpResponse.json({
                data: [projectMemberFixture({ permission: 'write' })],
              });
            }

            return HttpResponse.json({
              data: [projectMemberFixture({ permission: 'read' })],
            });
          },
        ),
      });
      await screen.findByRole('button', { name: 'Alpha task' });

      useAuthStore().signIn(useAuthStore().user!);
      await waitFor(() => expect(served).toBe(2));
      await settle();
      gate.resolve();
      await settle();

      expect(createButton()).not.toBeInTheDocument();
    });
  });
});
