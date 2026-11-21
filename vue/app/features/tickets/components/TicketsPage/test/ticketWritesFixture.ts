import { http, HttpResponse, type RequestHandler } from 'msw';

import { signInAs } from '~/test/auth/signInAs';
import { apiUrl } from '~/test/mocks/apiUrl';
import { overrideApi } from '~/test/mocks/overrideApi';
import { ticketApi } from '~/test/mocks/tickets/ticketApiHandlers';
import { renderRoute } from '~/test/renderRoute';
import { userFixture } from '~/features/users/test/userFixture';

import {
  projectFixture,
  projectMemberFixture,
} from '../../../api/test/projectFixture';
import { ticketFixture } from '../../../api/test/ticketFixture';

export const CREATE_BUTTON = '+ チケット作成';

interface BoardOptions {
  permission?: 'read' | 'write';
  role?: 'user' | 'admin';
  /** 利用者がメンバーとして載るか（管理者の確認用） */
  member?: boolean;
  archived?: boolean;
  path?: string;
  twoProjects?: boolean;
  /** メンバー応答を自前のものに差し替える（再ログインなど、応答を順に変えたいとき） */
  membersHandler?: RequestHandler;
}

/**
 * 自分（ID 7）がプロジェクト 1 のメンバーになっているボードを開く。
 * 返す membersServed は、メンバー応答を返し終えたかどうか（権限の判定が済んだ後で確認するため）
 */
export async function openBoard(options: BoardOptions = {}) {
  signInAs(userFixture({ id: 7, role: options.role ?? 'user' }));
  let membersServed = false;

  overrideApi(
    ticketApi.projects([
      projectFixture({
        id: '1',
        name: 'Alpha',
        archived_at: options.archived ? '2026-11-01T00:00:00+00:00' : null,
      }),
      ...(options.twoProjects
        ? [projectFixture({ id: '2', name: 'Beta' })]
        : []),
    ]),
    options.membersHandler ??
      http.get(apiUrl('/api/projects/1/members'), () => {
        membersServed = true;

        return HttpResponse.json({
          data:
            options.member === false
              ? []
              : [
                  projectMemberFixture({
                    permission: options.permission ?? 'write',
                  }),
                ],
        });
      }),
    ticketApi.tickets([
      ticketFixture({ id: '1', project_id: '1', title: 'Alpha task' }),
    ]),
    ticketApi.ticket(
      ticketFixture({ id: '1', project_id: '1', title: 'Alpha task' }),
    ),
  );

  const view = await renderRoute(options.path ?? '/tickets?project=1');

  return { ...view, membersServed: () => membersServed };
}

/** メンバー応答が反映される時間を待つ（「出ない」ことの確認が空振りしないように） */
export const settle = () => new Promise((resolve) => setTimeout(resolve, 30));
