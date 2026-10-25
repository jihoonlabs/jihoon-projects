import { http, HttpResponse } from 'msw';
import { expect, it, vi } from 'vitest';
import { userEvent } from '@testing-library/user-event';
import { render, screen, waitFor } from '@testing-library/react';
import { TicketBoardView } from '../../View';
import { responseTicket } from '@/features/tickets/api/test/ticketFixture';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useTicketStore } from '@/features/tickets/store/useTicketStore';
import { server } from '@/test/mocks/server';
import { url } from '@/features/tickets/api/test/setup';

const authenticateAsTicketWriter = () => {
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
};

const registerBoardReadHandlers = (
  getTickets: () => (typeof responseTicket)[],
) => {
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
      HttpResponse.json({ data: getTickets() }),
    ),
    http.get(`${url}/api/tickets/1`, () =>
      HttpResponse.json({ data: getTickets()[0] ?? responseTicket }),
    ),
    http.get(`${url}/api/tickets/1/comments`, () =>
      HttpResponse.json({ data: [] }),
    ),
  );
};

it('saves ticket detail edits through the API and displays the updated result', async () => {
  let updateRequest: unknown;
  let currentTicket = responseTicket;
  registerBoardReadHandlers(() =>
    currentTicket.id === '1' ? [currentTicket] : [],
  );
  server.use(
    http.patch(`${url}/api/tickets/1`, async ({ request }) => {
      updateRequest = await request.json();
      currentTicket = {
        ...currentTicket,
        title: 'Updated from detail',
        version: 2,
      };
      return HttpResponse.json({ data: currentTicket });
    }),
  );
  authenticateAsTicketWriter();
  const user = userEvent.setup();
  render(<TicketBoardView />);

  await user.selectOptions(
    await screen.findByRole('combobox', { name: 'プロジェクト' }),
    '1',
  );
  await user.click(
    await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' }),
  );
  await screen.findByRole('heading', { name: 'チケット詳細' });
  await user.click(await screen.findByRole('button', { name: '編集' }));
  const title = screen.getByRole('textbox', { name: 'タイトル' });
  await user.clear(title);
  await user.type(title, 'Updated from detail');
  await user.click(screen.getByRole('button', { name: '保存' }));

  await waitFor(() =>
    expect(updateRequest).toEqual({
      expected_version: 1,
      title: 'Updated from detail',
      description: null,
      status: 'TODO',
      priority: 'MEDIUM',
    }),
  );
  expect(
    await screen.findByRole('heading', { name: 'チケット詳細' }),
  ).toBeInTheDocument();
  expect(
    await screen.findByRole('heading', {
      name: 'Updated from detail',
      level: 3,
    }),
  ).toBeInTheDocument();
});

it('deletes a ticket from detail after confirmation and removes it from the board', async () => {
  let currentTicket: typeof responseTicket | null = responseTicket;
  let deleteRequestCount = 0;
  registerBoardReadHandlers(() => (currentTicket ? [currentTicket] : []));
  server.use(
    http.delete(`${url}/api/tickets/1`, () => {
      deleteRequestCount += 1;
      currentTicket = null;
      return new HttpResponse(null, { status: 204 });
    }),
  );
  authenticateAsTicketWriter();
  vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
  const user = userEvent.setup();
  render(<TicketBoardView />);

  await user.selectOptions(
    await screen.findByRole('combobox', { name: 'プロジェクト' }),
    '1',
  );
  await user.click(
    await screen.findByRole('button', { name: 'TICK-1 の詳細を開く' }),
  );
  await user.click(await screen.findByRole('button', { name: '削除' }));

  await waitFor(() => expect(deleteRequestCount).toBe(1));
  await waitFor(() =>
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
  );
  expect(
    screen.queryByRole('button', { name: 'TICK-1 の詳細を開く' }),
  ).not.toBeInTheDocument();
});
