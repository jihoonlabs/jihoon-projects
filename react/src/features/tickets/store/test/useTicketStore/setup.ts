import { beforeEach, vi } from 'vitest';
import * as api from '../../../api/ticketApi';
import { useTicketStore } from '../../useTicketStore';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { state } from './helpers';

vi.mock('../../../api/ticketApi', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../../api/ticketApi')>()),
  fetchTickets: vi.fn(),
  createTicket: vi.fn(),
  updateTicketStatus: vi.fn(),
  moveTicket: vi.fn(),
  updateTicket: vi.fn(),
  deleteTicket: vi.fn(),
}));

beforeEach(() => {
  vi.resetAllMocks();
  useAuthStore.getState().logout();
  vi.mocked(api.fetchTickets).mockImplementation(async () => state().tickets);
  useTicketStore.setState({ tickets: [], error: null, isLoading: false });
});
