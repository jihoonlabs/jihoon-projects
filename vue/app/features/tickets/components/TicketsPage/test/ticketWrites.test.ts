import { screen, waitFor, within } from '@testing-library/vue';
import { http, HttpResponse } from 'msw';
import { describe, expect, it, vi } from 'vitest';

import { apiUrl } from '~/test/mocks/apiUrl';
import { overrideApi } from '~/test/mocks/overrideApi';

import { projectMemberFixture } from '../../../api/test/projectFixture';
import { ticketFixture } from '../../../api/test/ticketFixture';
import { CREATE_BUTTON, openBoard } from './ticketWritesFixture';

const openCard = async (user: { click: (el: Element) => Promise<void> }) => {
  await user.click(await screen.findByRole('button', { name: 'Alpha task' }));
  return screen.findByRole('dialog');
};

describe('チケットボードの作成・編集・削除', () => {
  describe('作成', () => {
    it('プロジェクトを選んでいれば、入力して保存でき、保存したチケットが列に出ること', async () => {
      let sent: unknown;
      overrideApi(
        http.post(apiUrl('/api/tickets'), async ({ request }) => {
          sent = await request.json();

          return HttpResponse.json(
            {
              data: ticketFixture({
                id: '9',
                project_id: '1',
                title: 'Brand new',
                position: 5,
              }),
            },
            { status: 201 },
          );
        }),
      );
      const { user } = await openBoard();

      await user.click(
        await screen.findByRole('button', { name: CREATE_BUTTON }),
      );
      const dialog = await screen.findByRole('dialog');
      expect(
        within(dialog).getByRole('heading', { name: 'チケット作成' }),
      ).toBeInTheDocument();
      await user.type(within(dialog).getByLabelText('タイトル'), 'Brand new');
      await user.click(within(dialog).getByRole('button', { name: '保存' }));

      await waitFor(() =>
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
      );
      expect(sent).toMatchObject({ project_id: 1, title: 'Brand new' });
      expect(
        within(screen.getByRole('region', { name: '未対応' })).getByText(
          'Brand new',
        ),
      ).toBeInTheDocument();
    });

    it('全体表示からは、作成先を選ぶまで保存できず、選んでも入力を保つこと', async () => {
      const { user } = await openBoard({ path: '/tickets', twoProjects: true });
      await screen.findByRole('button', { name: 'Alpha task' });

      await user.click(
        await screen.findByRole('button', { name: CREATE_BUTTON }),
      );
      const dialog = await screen.findByRole('dialog');
      await user.type(within(dialog).getByLabelText('タイトル'), 'Draft title');
      expect(within(dialog).getByRole('status')).toHaveTextContent(
        '作成先のプロジェクトを選択してください。',
      );
      expect(
        within(dialog).getByRole('button', { name: '保存' }),
      ).toBeDisabled();

      await user.selectOptions(
        within(dialog).getByLabelText('作成先プロジェクト'),
        'Alpha',
      );

      await waitFor(() =>
        expect(
          within(dialog).getByRole('button', { name: '保存' }),
        ).toBeEnabled(),
      );
      expect(within(dialog).getByLabelText('タイトル')).toHaveValue(
        'Draft title',
      );
      expect(
        screen.getByRole('combobox', { name: 'プロジェクト' }),
      ).toHaveValue('1');
    });

    it('作成先を変えたら、別のプロジェクトの担当者を送らないよう担当者を選び直しにすること', async () => {
      overrideApi(
        http.get(apiUrl('/api/projects/2/members'), () =>
          HttpResponse.json({
            data: [projectMemberFixture({ id: '8', name: 'Beta member' })],
          }),
        ),
      );
      const { user } = await openBoard({ path: '/tickets', twoProjects: true });
      await screen.findByRole('button', { name: 'Alpha task' });
      await user.click(
        await screen.findByRole('button', { name: CREATE_BUTTON }),
      );
      const dialog = await screen.findByRole('dialog');
      const project = within(dialog).getByLabelText('作成先プロジェクト');
      await user.selectOptions(project, 'Alpha');
      await within(dialog).findByRole('option', { name: 'Aki' });
      await user.selectOptions(within(dialog).getByLabelText('担当者'), 'Aki');
      expect(within(dialog).getByLabelText('担当者')).toHaveValue('7');

      await user.selectOptions(project, 'Beta');

      await within(dialog).findByRole('option', { name: 'Beta member' });
      expect(within(dialog).getByLabelText('担当者')).toHaveValue('');
    });

    it('作成先が読み取りだけなら、理由を示して保存できないこと', async () => {
      const { user } = await openBoard({
        path: '/tickets',
        twoProjects: true,
        permission: 'read',
      });
      await screen.findByRole('button', { name: 'Alpha task' });
      await user.click(
        await screen.findByRole('button', { name: CREATE_BUTTON }),
      );
      const dialog = await screen.findByRole('dialog');
      await user.type(within(dialog).getByLabelText('タイトル'), 'Draft');

      await user.selectOptions(
        within(dialog).getByLabelText('作成先プロジェクト'),
        'Alpha',
      );

      expect(await within(dialog).findByRole('status')).toHaveTextContent(
        'このプロジェクトは閲覧のみです',
      );
      expect(
        within(dialog).getByRole('button', { name: '保存' }),
      ).toBeDisabled();
    });
  });

  describe('編集と削除', () => {
    it('編集して保存すると、詳細と列のカードが新しい内容になること', async () => {
      overrideApi(
        http.patch(apiUrl('/api/tickets/1'), () =>
          HttpResponse.json({
            data: ticketFixture({ id: '1', title: 'Renamed task', version: 2 }),
          }),
        ),
      );
      const { user } = await openBoard();
      const dialog = await openCard(user);

      await user.click(
        await within(dialog).findByRole('button', { name: '編集' }),
      );
      const title = within(dialog).getByLabelText('タイトル');
      await user.clear(title);
      await user.type(title, 'Renamed task');
      await user.click(within(dialog).getByRole('button', { name: '保存' }));

      expect(
        await within(dialog).findByText('Renamed task'),
      ).toBeInTheDocument();
      await user.click(within(dialog).getByRole('button', { name: '閉じる' }));
      expect(
        within(screen.getByRole('region', { name: '未対応' })).getByText(
          'Renamed task',
        ),
      ).toBeInTheDocument();
    });

    it('削除すると、モーダルを閉じて列からも消すこと', async () => {
      vi.spyOn(window, 'confirm').mockReturnValue(true);
      overrideApi(
        http.delete(
          apiUrl('/api/tickets/1'),
          () => new HttpResponse(null, { status: 204 }),
        ),
      );
      const { user } = await openBoard();
      const dialog = await openCard(user);

      await user.click(
        await within(dialog).findByRole('button', { name: '削除' }),
      );

      await waitFor(() =>
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
      );
      expect(screen.queryByText('Alpha task')).not.toBeInTheDocument();
    });
  });
});
