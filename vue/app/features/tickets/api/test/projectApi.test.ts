import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { signInAs } from '~/test/auth/signInAs';
import { apiUrl } from '~/test/mocks/apiUrl';
import { overrideApi } from '~/test/mocks/overrideApi';
import { ticketApi } from '~/test/mocks/tickets/ticketApiHandlers';

import { ProjectApiError } from '../apiErrors';
import { useProjectApi } from '../projectApi';
import { projectFixture, projectMemberFixture } from './projectFixture';

describe('プロジェクト API', () => {
  it('プロジェクトとメンバーの ID を文字列にそろえること', async () => {
    signInAs();
    overrideApi(
      ticketApi.projects([projectFixture({ id: 4 })]),
      ticketApi.members('4', [projectMemberFixture({ id: 7, role: 'leader' })]),
    );
    const api = useProjectApi();

    await expect(api.fetchProjects()).resolves.toEqual([
      {
        id: '4',
        name: 'Product',
        projectKey: 'PRD',
        color: '#e3f2fd',
        boardVersion: 1,
        archivedAt: null,
      },
    ]);
    await expect(api.fetchProjectMembers('4')).resolves.toEqual([
      {
        id: '7',
        name: 'Aki',
        email: 'aki@example.com',
        role: 'leader',
        permission: 'write',
      },
    ]);
  });

  it('色のない古い応答は色を null にすること', async () => {
    signInAs();
    const {
      color: _color,
      archived_at: _archived,
      ...legacy
    } = projectFixture();
    overrideApi(ticketApi.projects([legacy]));

    const [project] = await useProjectApi().fetchProjects();

    expect(project).toMatchObject({ color: null, archivedAt: null });
  });

  it('archived を指定したときだけ archived=1 を付けること', async () => {
    signInAs();
    const queries: Array<string | null> = [];
    overrideApi(
      http.get(apiUrl('/api/projects'), ({ request }) => {
        queries.push(new URL(request.url).searchParams.get('archived'));
        return HttpResponse.json({ data: [] });
      }),
    );
    const api = useProjectApi();

    await api.fetchProjects();
    await api.fetchProjects({ archived: true });

    expect(queries).toEqual([null, '1']);
  });

  it('403 は権限のメッセージ、それ以外は状態コード付きにすること', async () => {
    signInAs();
    overrideApi(ticketApi.projectsFail(403), ticketApi.membersFail('4', 500));
    const api = useProjectApi();

    await expect(api.fetchProjects()).rejects.toThrow('操作権限がありません');
    const failure = await api
      .fetchProjectMembers('4')
      .catch((error: unknown) => error);
    expect(failure).toBeInstanceOf(ProjectApiError);
    expect((failure as ProjectApiError).message).toContain('500');
  });

  it.each([
    ['プロジェクト', {}],
    ['プロジェクト', { data: null }],
    ['プロジェクト', { data: {} }],
  ])('%s一覧の不正な応答を受け付けないこと', async (_label, body) => {
    signInAs();
    overrideApi(
      http.get(apiUrl('/api/projects'), () => HttpResponse.json(body)),
    );

    await expect(useProjectApi().fetchProjects()).rejects.toThrow(
      '応答形式が不正',
    );
  });

  it('メンバー一覧の不正な応答を受け付けないこと', async () => {
    signInAs();
    overrideApi(
      http.get(apiUrl('/api/projects/4/members'), () =>
        HttpResponse.json({ data: null }),
      ),
    );

    await expect(useProjectApi().fetchProjectMembers('4')).rejects.toThrow(
      '応答形式が不正',
    );
  });
});
