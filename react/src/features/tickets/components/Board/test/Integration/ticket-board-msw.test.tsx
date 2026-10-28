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

it('renders API ticket data and updates its status through the board', async () => {
  let statusRequest: unknown;
  let ticketStatus = responseTicket.status;
  server.use(
    http.get(`${url}/api/projects`, () =>
      HttpResponse.json({
        data: [
          {
            id: 1,
            name: 'General',
            project_key: 'GEN',
            board_version: 3,
          },
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
      HttpResponse.json({
        data: [{ ...responseTicket, status: ticketStatus }],
      }),
    ),
    http.patch(`${url}/api/tickets/1`, async ({ request }) => {
      statusRequest = await request.json();
      ticketStatus = 'DONE';
      return HttpResponse.json({
        data: { ...responseTicket, status: 'DONE' },
      });
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
      attendanceRole: 'employee',
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
  const title = await screen.findByRole('button', {
    name: 'TICK-1 の詳細を開く',
  });
  expect(title).toBeInTheDocument();

  const status = screen.getByRole('combobox', {
    name: 'First ticket のステータス',
  });
  expect(status).toHaveValue('TODO');
  await user.selectOptions(status, 'DONE');

  await waitFor(() => expect(statusRequest).toEqual({ status: 'DONE' }));
  await waitFor(() =>
    expect(
      screen.getByRole('combobox', {
        name: 'First ticket のステータス',
      }),
    ).toHaveValue('DONE'),
  );
});
