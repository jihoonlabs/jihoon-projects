import { http, HttpResponse } from 'msw';
import { expect, it } from 'vitest';
import { userEvent } from '@testing-library/user-event';
import { render, screen, waitFor } from '@testing-library/react';
import { TicketBoardView } from '../../View';
import { responseTicket } from '@/features/tickets/api/test/ticketFixture';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useTicketStore } from '@/features/tickets/store/useTicketStore';
import { server } from '@/test/mocks/server';
import { url } from '@/features/tickets/api/test/setup';

it('creates a ticket through the board and renders the server response', async () => {
  let createRequest: unknown;
  let tickets = [] as (typeof responseTicket)[];
  const createdTicket = {
    ...responseTicket,
    id: '2',
    issue_key: 'GEN-2',
    title: 'Created from board',
    assignee: null,
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
    http.get(`${url}/api/tickets`, () => HttpResponse.json({ data: tickets })),
    http.post(`${url}/api/tickets`, async ({ request }) => {
      createRequest = await request.json();
      tickets = [createdTicket];
      return HttpResponse.json({ data: createdTicket }, { status: 201 });
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
    await screen.findByRole('button', { name: '+ チケット作成' }),
  );
  expect(
    await screen.findByRole('heading', { name: 'チケット作成' }),
  ).toBeInTheDocument();

  await user.type(
    screen.getByRole('textbox', { name: 'タイトル' }),
    'Created from board',
  );
  await user.click(screen.getByRole('button', { name: '保存' }));

  await waitFor(() =>
    expect(createRequest).toEqual({
      title: 'Created from board',
      project_id: 1,
      description: null,
      status: 'TODO',
      priority: 'MEDIUM',
      assignee_id: null,
    }),
  );
  expect(
    await screen.findByRole('button', { name: 'GEN-2 の詳細を開く' }),
  ).toBeInTheDocument();
  expect(screen.getByText('Created from board')).toBeInTheDocument();
});
