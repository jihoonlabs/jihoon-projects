import { http, HttpResponse } from 'msw';
import { expect, it } from 'vitest';
import { userEvent } from '@testing-library/user-event';
import { render, screen, waitFor } from '@testing-library/react';
import { TicketBoardView } from '../../View';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useTicketStore } from '@/features/tickets/store/useTicketStore';
import { server } from '@/test/mocks/server';
import { url } from '@/features/tickets/api/test/setup';

it('creates a project, loads its leader membership, and enables ticket creation', async () => {
  let projectRequest: unknown;
  let projects: Array<Record<string, unknown>> = [];
  server.use(
    http.get(`${url}/api/projects`, () =>
      HttpResponse.json({ data: projects }),
    ),
    http.post(`${url}/api/projects`, async ({ request }) => {
      projectRequest = await request.json();
      projects = [
        {
          id: 2,
          name: 'New team',
          project_key: 'NEW',
          board_version: 1,
          archived_at: null,
        },
      ];
      return HttpResponse.json({ data: projects[0] }, { status: 201 });
    }),
    http.get(`${url}/api/projects/2/members`, () =>
      HttpResponse.json({
        data: [
          {
            id: 7,
            name: 'Tester',
            email: 'tester@example.com',
            role: 'leader',
            permission: 'write',
          },
        ],
      }),
    ),
    http.get(`${url}/api/tickets`, () => HttpResponse.json({ data: [] })),
  );
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  useAuthStore.setState({
    user: {
      id: 7,
      name: 'Tester',
      email: 'tester@example.com',
      status: 'active',
      role: 'user',
      attendanceRole: 'employee',
      createdAt: '2026-09-24T00:00:00.000000Z',
    },
    isAuthenticated: true,
  });
  const user = userEvent.setup();
  render(<TicketBoardView />);

  await user.click(
    await screen.findByRole('button', { name: 'プロジェクト一覧・作成' }),
  );
  await user.type(screen.getByLabelText('プロジェクト名'), 'New team');
  await user.click(screen.getByRole('button', { name: 'プロジェクトを作成' }));

  await waitFor(() => expect(projectRequest).toEqual({ name: 'New team' }));
  expect(
    await screen.findByText(
      'New team を作成しました。メンバーを追加してチケット作成を開始できます。',
    ),
  ).toBeInTheDocument();
  expect(
    await screen.findByRole('combobox', { name: 'プロジェクト' }),
  ).toHaveValue('2');
  expect(
    await screen.findByRole('button', { name: 'メンバー管理' }),
  ).toBeInTheDocument();
  expect(
    await screen.findByRole('button', { name: '+ チケット作成' }),
  ).toBeEnabled();
});
