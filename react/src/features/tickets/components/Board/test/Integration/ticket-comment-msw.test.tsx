import { http, HttpResponse } from 'msw';
import { expect, it } from 'vitest';
import { userEvent } from '@testing-library/user-event';
import { render, screen, waitFor, within } from '@testing-library/react';
import { TicketBoardView } from '../../View';
import { responseTicket } from '@/features/tickets/api/test/ticketFixture';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useTicketStore } from '@/features/tickets/store/useTicketStore';
import { server } from '@/test/mocks/server';
import { url } from '@/features/tickets/api/test/setup';

it('posts a comment from ticket details through the comment API', async () => {
  let commentRequest: unknown;
  const savedComment = {
    id: '9',
    body: 'A comment submitted from the board',
    author: { id: 7, name: 'Tester', avatar_url: null },
    created_at: '2026-09-24T01:00:00.000000Z',
    updated_at: '2026-09-24T01:00:00.000000Z',
  };
  server.use(
    http.get(`${url}/api/projects`, () =>
      HttpResponse.json({
        data: [
          { id: 1, name: 'General', project_key: 'GEN', board_version: 3 },
        ],
      }),
    ),
    http.get(`${url}/api/projects/1/members`, () =>
      HttpResponse.json({
        data: [
          {
            id: 7,
            name: 'Tester',
            email: 'tester@example.com',
            role: 'member',
            permission: 'write',
          },
        ],
      }),
    ),
    http.get(`${url}/api/tickets`, () =>
      HttpResponse.json({ data: [responseTicket] }),
    ),
    http.get(`${url}/api/tickets/1`, () =>
      HttpResponse.json({ data: responseTicket }),
    ),
    http.get(`${url}/api/tickets/1/comments`, () =>
      HttpResponse.json({ data: [] }),
    ),
    http.post(`${url}/api/tickets/1/comments`, async ({ request }) => {
      commentRequest = await request.json();
      return HttpResponse.json({ data: savedComment }, { status: 201 });
    }),
  );
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  useAuthStore.setState({
    user: {
      id: 7,
      name: 'Tester',
      email: 'tester@example.com',
      status: 'active',
      role: 'user',
      createdAt: '2026-09-24T00:00:00.000000Z',
    },
    isAuthenticated: true,
  });
  const user = userEvent.setup();
  render(<TicketBoardView />);

  await user.selectOptions(
    await screen.findByRole('combobox', { name: 'プロジェクト' }),
    '1',
  );
  await user.click(
    await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' }),
  );
  expect(
    await screen.findByRole('heading', { name: 'チケット詳細' }),
  ).toBeInTheDocument();
  await screen.findByText('コメントはまだありません。');
  await user.type(
    screen.getByRole('textbox', { name: 'コメントを追加' }),
    'A comment submitted from the board',
  );
  await user.click(screen.getByRole('button', { name: '送信' }));

  await waitFor(() =>
    expect(commentRequest).toEqual({
      body: 'A comment submitted from the board',
    }),
  );
  expect(
    await screen.findByText('A comment submitted from the board'),
  ).toBeInTheDocument();
  expect(
    within(screen.getByRole('region', { name: 'コメント' })).getByText(
      'Tester',
    ),
  ).toBeInTheDocument();
});
