import { screen, waitFor, within } from '@testing-library/vue';
import { describe, expect, it } from 'vitest';

import { useAuthStore } from '~/features/auth/store/useAuthStore';
import { signInAs } from '~/test/auth/signInAs';
import { enableDemoMode } from '~/test/demoMode';
import { overrideApi } from '~/test/mocks/overrideApi';
import { ticketApi } from '~/test/mocks/tickets/ticketApiHandlers';
import { renderRoute } from '~/test/renderRoute';

import { projectFixture } from '../../../api/test/projectFixture';
import { ticketFixture } from '../../../api/test/ticketFixture';

const column = (name: string) => screen.getByRole('region', { name });
const projectSelect = () =>
  screen.getByRole('combobox', { name: 'プロジェクト' });

const twoProjects = () =>
  overrideApi(
    ticketApi.projects([
      projectFixture({ id: '1', name: 'Alpha', color: '#e3f2fd' }),
      projectFixture({ id: '2', name: 'Beta', color: '#fde68a' }),
    ]),
  );

const mixedTickets = () =>
  overrideApi(
    ticketApi.tickets([
      ticketFixture({ id: '1', project_id: '1', title: 'Alpha task' }),
      ticketFixture({
        id: '2',
        project_id: '2',
        title: 'Beta task',
        status: 'DONE',
        assignee: null,
      }),
    ]),
  );

describe('チケットボード', () => {
  describe('表示', () => {
    it('状態ごとの列に、position の順でチケットを並べること', async () => {
      signInAs();
      twoProjects();
      overrideApi(
        ticketApi.tickets([
          ticketFixture({ id: '2', title: 'Second', position: 2 }),
          ticketFixture({ id: '1', title: 'First', position: 1 }),
          ticketFixture({ id: '3', title: 'Done one', status: 'DONE' }),
        ]),
      );

      await renderRoute('/tickets');

      const todo = column('未対応');
      await within(todo).findByText('First');
      expect(
        within(todo)
          .getAllByRole('article')
          .map((card) => card.textContent),
      ).toEqual([
        expect.stringContaining('First'),
        expect.stringContaining('Second'),
      ]);
      expect(within(column('完了')).getByText('Done one')).toBeInTheDocument();
      expect(column('バックログ')).toHaveTextContent('0');
    });

    it('プロジェクトの色をカードの縁に使い、不正な色は使わないこと', async () => {
      signInAs();
      overrideApi(
        ticketApi.projects([
          projectFixture({ id: '1', color: '#e3f2fd' }),
          projectFixture({ id: '2', color: 'url(example)' }),
        ]),
        ticketApi.tickets([
          ticketFixture({ id: '1', project_id: '1', title: 'Colored' }),
          ticketFixture({ id: '2', project_id: '2', title: 'Neutral' }),
        ]),
      );

      await renderRoute('/tickets');

      const colored = (await screen.findByText('Colored')).closest('article');
      const neutral = screen.getByText('Neutral').closest('article');
      expect(colored?.style.getPropertyValue('--project-color')).toBe(
        '#e3f2fd',
      );
      expect(neutral?.style.getPropertyValue('--project-color')).toBe('');
    });

    it('プロジェクト一覧にないプロジェクトのチケットは全体表示でも出さないこと', async () => {
      signInAs();
      twoProjects();
      overrideApi(
        ticketApi.tickets([
          ticketFixture({ id: '1', project_id: '1', title: 'Visible' }),
          ticketFixture({ id: '9', project_id: '9', title: 'Hidden' }),
        ]),
      );

      await renderRoute('/tickets');

      expect(await screen.findByText('Visible')).toBeInTheDocument();
      expect(screen.queryByText('Hidden')).not.toBeInTheDocument();
    });

    it('プロジェクトが 1 つもないときは案内を出すこと', async () => {
      signInAs();
      overrideApi(ticketApi.projects([]));

      await renderRoute('/tickets');

      expect(
        await screen.findByText(/利用可能なプロジェクトがありません。/),
      ).toBeInTheDocument();
    });
  });

  describe('プロジェクトの選択', () => {
    it('選んだプロジェクトのチケットだけを表示し、URL に反映すること', async () => {
      signInAs();
      twoProjects();
      mixedTickets();
      const { user, currentPath } = await renderRoute('/tickets');
      await screen.findByText('Alpha task');

      await user.selectOptions(projectSelect(), 'Beta');

      await waitFor(() => expect(currentPath()).toBe('/tickets?project=2'));
      expect(screen.queryByText('Alpha task')).not.toBeInTheDocument();
      expect(screen.getByText('Beta task')).toBeInTheDocument();
    });

    it('URL の ?project= から選択を復元すること', async () => {
      signInAs();
      twoProjects();
      mixedTickets();

      await renderRoute('/tickets?project=2');

      await waitFor(() => expect(projectSelect()).toHaveValue('2'));
      expect(await screen.findByText('Beta task')).toBeInTheDocument();
      expect(screen.queryByText('Alpha task')).not.toBeInTheDocument();
    });

    it('URL の指定が一覧になければ全体表示にし、URL からも外すこと', async () => {
      signInAs();
      twoProjects();
      mixedTickets();

      const { currentPath } = await renderRoute('/tickets?project=99');

      await screen.findByText('Alpha task');
      expect(projectSelect()).toHaveValue('ALL');
      await waitFor(() => expect(currentPath()).toBe('/tickets'));
    });

    it('デモモードでは URL の指定がなければ先頭のプロジェクトを選ぶこと', async () => {
      enableDemoMode();
      signInAs();
      twoProjects();
      mixedTickets();

      await renderRoute('/tickets');

      await waitFor(() => expect(projectSelect()).toHaveValue('1'));
    });
  });

  describe('絞り込み', () => {
    it('検索語でタイトルを絞り込むこと', async () => {
      signInAs();
      twoProjects();
      mixedTickets();
      const { user } = await renderRoute('/tickets');
      await screen.findByText('Alpha task');

      await user.type(
        screen.getByRole('searchbox', { name: 'チケット検索' }),
        'beta',
      );

      expect(screen.queryByText('Alpha task')).not.toBeInTheDocument();
      expect(screen.getByText('Beta task')).toBeInTheDocument();
    });

    it('「未割り当て」で担当者のいないチケットだけを出すこと', async () => {
      signInAs();
      twoProjects();
      mixedTickets();
      const { user } = await renderRoute('/tickets');
      await screen.findByText('Alpha task');

      await user.selectOptions(
        screen.getByRole('combobox', { name: '担当者フィルター' }),
        '未割り当て',
      );

      expect(screen.queryByText('Alpha task')).not.toBeInTheDocument();
      expect(screen.getByText('Beta task')).toBeInTheDocument();
    });

    it('「自分に割り当て」でログイン中の利用者のチケットだけを出すこと', async () => {
      const me = signInAs();
      twoProjects();
      overrideApi(
        ticketApi.tickets([
          ticketFixture({
            id: '1',
            title: 'Mine',
            assignee: { id: me.id, name: me.name, avatar_url: null },
          }),
          ticketFixture({
            id: '2',
            title: 'Theirs',
            assignee: { id: me.id + 1, name: 'Other', avatar_url: null },
          }),
        ]),
      );
      const { user } = await renderRoute('/tickets');
      await screen.findByText('Mine');

      await user.selectOptions(
        screen.getByRole('combobox', { name: '担当者フィルター' }),
        '自分に割り当て',
      );

      expect(screen.getByText('Mine')).toBeInTheDocument();
      expect(screen.queryByText('Theirs')).not.toBeInTheDocument();
    });

    it('プロジェクトを切り替えると絞り込みを戻すこと', async () => {
      signInAs();
      twoProjects();
      mixedTickets();
      const { user } = await renderRoute('/tickets');
      await screen.findByText('Alpha task');
      await user.type(
        screen.getByRole('searchbox', { name: 'チケット検索' }),
        'zzz',
      );

      await user.selectOptions(projectSelect(), 'Alpha');

      expect(
        screen.getByRole('searchbox', { name: 'チケット検索' }),
      ).toHaveValue('');
      expect(await screen.findByText('Alpha task')).toBeInTheDocument();
    });
  });

  describe('失敗からの回復', () => {
    it('チケット一覧の取得に失敗したら、再取得で回復できること', async () => {
      signInAs();
      twoProjects();
      overrideApi(ticketApi.ticketsFail(500));
      const { user } = await renderRoute('/tickets');
      expect(await screen.findByRole('alert')).toHaveTextContent('500');

      mixedTickets();
      await user.click(
        screen.getByRole('button', { name: 'チケット一覧を再取得' }),
      );

      expect(await screen.findByText('Alpha task')).toBeInTheDocument();
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('プロジェクト一覧の取得に失敗したら、案内を出さずに再取得できること', async () => {
      signInAs();
      overrideApi(ticketApi.projectsFail(500), ticketApi.tickets([]));
      const { user } = await renderRoute('/tickets');
      expect(await screen.findByRole('alert')).toHaveTextContent('500');
      expect(
        screen.queryByText(/利用可能なプロジェクトがありません。/),
      ).not.toBeInTheDocument();

      twoProjects();
      await user.click(
        screen.getByRole('button', { name: 'プロジェクトを再取得' }),
      );

      await waitFor(() =>
        expect(within(projectSelect()).getByText('Alpha')).toBeInTheDocument(),
      );
    });

    it('メンバーの取得に失敗したら、再取得で回復できること', async () => {
      signInAs();
      twoProjects();
      overrideApi(ticketApi.membersFail('2', 500));
      const { user } = await renderRoute('/tickets?project=2');
      expect(await screen.findByRole('alert')).toHaveTextContent('500');

      overrideApi(ticketApi.members('2', []));
      await user.click(
        screen.getByRole('button', { name: 'メンバーと権限を再取得' }),
      );

      await waitFor(() =>
        expect(screen.queryByRole('alert')).not.toBeInTheDocument(),
      );
    });
  });

  describe('ログイン状態の変化', () => {
    it('ログアウトしたあとは、取得済みのチケットを残さないこと', async () => {
      signInAs();
      twoProjects();
      mixedTickets();
      await renderRoute('/tickets');
      await screen.findByText('Alpha task');

      useAuthStore().signOut();

      await waitFor(() =>
        expect(screen.queryByText('Alpha task')).not.toBeInTheDocument(),
      );
    });
  });
});
