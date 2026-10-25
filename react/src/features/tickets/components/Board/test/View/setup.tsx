import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ComponentProps } from 'react';
import { afterEach, beforeEach, expect, vi } from 'vitest';
import * as api from '../../../../api/ticketApi';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useTicketStore } from '../../../../store/useTicketStore';
import { TicketBoardView } from '../../View';
import * as projectApi from '@/features/tickets/api/projectApi';

vi.mock('../../../../api/ticketApi', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../../../api/ticketApi')>()),
  fetchTickets: vi.fn(),
  fetchTicket: vi.fn(),
  updateTicketStatus: vi.fn(),
  moveTicket: vi.fn(),
  createTicket: vi.fn(),
  updateTicket: vi.fn(),
  deleteTicket: vi.fn(),
}));
vi.mock('../../../../api/ticketCommentApi', () => ({
  fetchTicketComments: vi.fn().mockResolvedValue([]),
  createTicketComment: vi.fn(),
  updateTicketComment: vi.fn(),
  deleteTicketComment: vi.fn(),
}));
vi.mock('@/features/tickets/api/projectApi', () => ({
  fetchProjects: vi
    .fn()
    .mockResolvedValue([
      { id: '1', name: 'General', projectKey: 'GEN', boardVersion: 3 },
    ]),
  fetchProjectMembers: vi.fn().mockResolvedValue([
    {
      id: '7',
      name: 'Tester',
      email: 'tester@example.com',
      role: 'member',
      permission: 'write',
    },
  ]),
  createProject: vi.fn(),
  renameProject: vi.fn(),
  archiveProject: vi.fn(),
  restoreProject: vi.fn(),
  transferProjectLeader: vi.fn(),
  addProjectMember: vi.fn(),
  updateProjectMember: vi.fn(),
  removeProjectMember: vi.fn(),
}));
vi.mock('@dnd-kit/core', async (importOriginal) => {
  const original = await importOriginal<typeof import('@dnd-kit/core')>();
  return {
    ...original,
    DndContext: ({
      children,
      onDragEnd,
    }: ComponentProps<typeof original.DndContext>) => (
      <>
        {children}
        {(['DONE', 'IN_REVIEW'] as const).map((status) => (
          <button
            key={status}
            onClick={() =>
              onDragEnd?.({
                active: { id: '1' },
                over: { id: status },
              } as Parameters<NonNullable<typeof onDragEnd>>[0])
            }
          >
            drop {status}
          </button>
        ))}
      </>
    ),
  };
});

export async function renderSelectedProject() {
  render(<TicketBoardView />);
  await waitFor(() =>
    expect(
      screen
        .getByRole('combobox', { name: 'プロジェクト' })
        .querySelector('option[value="1"]'),
    ).not.toBeNull(),
  );
  fireEvent.change(screen.getByRole('combobox', { name: 'プロジェクト' }), {
    target: { value: '1' },
  });
}

beforeEach(() => {
  window.history.replaceState(window.history.state, '', '/');
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
  vi.mocked(api.fetchTickets).mockResolvedValue([]);
  vi.mocked(projectApi.fetchProjectMembers).mockReset();
  vi.mocked(projectApi.fetchProjects).mockReset();
  vi.mocked(api.fetchTicket).mockImplementation(async (id) => {
    const ticket = useTicketStore
      .getState()
      .tickets.find((item) => item.id === id);
    if (!ticket) throw new Error('missing test ticket');
    return ticket;
  });
  vi.mocked(projectApi.fetchProjects).mockResolvedValue([
    { id: '1', name: 'General', projectKey: 'GEN', boardVersion: 3 },
  ]);
  vi.mocked(projectApi.fetchProjectMembers).mockResolvedValue([
    {
      id: '7',
      name: 'Tester',
      email: 'tester@example.com',
      role: 'member',
      permission: 'write',
    },
  ]);
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
});
afterEach(() => vi.restoreAllMocks());
