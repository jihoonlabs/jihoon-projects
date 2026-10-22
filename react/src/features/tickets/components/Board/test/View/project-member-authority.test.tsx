import './setup';
import { renderSelectedProject } from './helpers';
import { fireEvent, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import * as api from '../../../../api/ticketApi';
import { responseTicket } from '../../../../api/test/ticketFixture';
import { useTicketStore } from '../../../../store/useTicketStore';
import * as projectApi from '@/features/tickets/api/projectApi';

it('allows a read-only project leader to manage members without Ticket write controls', async () => {
  vi.mocked(api.fetchTickets).mockResolvedValue([api.toTicket(responseTicket)]);
  vi.mocked(projectApi.fetchProjectMembers).mockResolvedValue([
    {
      id: '7',
      name: 'Tester',
      email: 'tester@example.com',
      role: 'leader',
      permission: 'read',
    },
  ]);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });

  await renderSelectedProject();
  expect(
    await screen.findByRole('button', { name: 'メンバー管理' }),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: '+ チケット作成' }),
  ).not.toBeInTheDocument();
});

it('updates leader authority immediately after a successful transfer', async () => {
  const leader = {
    id: '7',
    name: 'Tester',
    email: 'tester@example.com',
    role: 'leader' as const,
    permission: 'write' as const,
  };
  const member = {
    id: '8',
    name: 'Ren',
    email: 'ren@example.com',
    role: 'member' as const,
    permission: 'write' as const,
  };
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  vi.mocked(projectApi.fetchProjectMembers).mockResolvedValue([leader, member]);
  vi.mocked(projectApi.transferProjectLeader).mockResolvedValue({
    ...member,
    role: 'leader',
  });
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  await renderSelectedProject();
  fireEvent.click(await screen.findByRole('button', { name: 'メンバー管理' }));
  fireEvent.click(
    await screen.findByRole('button', { name: 'Ren をリーダーにする' }),
  );
  vi.mocked(projectApi.fetchProjectMembers).mockResolvedValue([
    { ...leader, role: 'member' },
    { ...member, role: 'leader' },
  ]);
  fireEvent.click(
    screen.getByRole('button', { name: 'リーダー引き継ぎを確定' }),
  );
  expect(
    await screen.findByText(
      '管理権限が変更されました。現在はメンバー一覧の閲覧のみ可能です。',
    ),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: 'プロジェクト設定' }),
  ).not.toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: 'メンバー管理' }),
  ).not.toBeInTheDocument();
  expect(
    screen.getByRole('button', { name: '+ チケット作成' }),
  ).toBeInTheDocument();
});
