import { useProtectedApi } from '~/features/auth/api/protectedRequest';
import { ApiError } from '~/shared/api/apiClient';

import type {
  CreateTicketInput,
  Ticket,
  TicketResponse,
  UpdateTicketInput,
} from '../types/ticket';
import {
  TICKET_ERROR_MESSAGE,
  TicketApiError,
  TicketConflictError,
  translateFailure,
} from './apiErrors';
import { toTicket } from './ticketMapper';

const toWriteError = (error: unknown): Error => {
  if (error instanceof ApiError) {
    if (error.status === 409 && error.code === 'ticket_conflict') {
      return new TicketConflictError();
    }

    return new TicketApiError(
      `${TICKET_ERROR_MESSAGE} (${error.status})`,
      error.status,
      error.code,
    );
  }

  return new TicketApiError(TICKET_ERROR_MESSAGE);
};

/**
 * 画面の文字列 ID を、API に送る正の整数へ変える。送る前に弾く。
 */
const toPositiveId = (value: string, label: string): number => {
  const id = Number(value);
  if (!Number.isSafeInteger(id) || id <= 0) {
    throw new TicketApiError(`${label}が不正です。`);
  }

  return id;
};

const toAssigneeId = (
  value: string | null | undefined,
): number | null | undefined => {
  if (value === undefined) return undefined;
  if (value === null) return null;

  return toPositiveId(value, '担当者ID');
};

/**
 * チケットの作成・更新・削除。Laravel の snake_case に合わせて送り、応答を画面用の形に変える。
 */
export function useTicketWriteApi() {
  const api = useProtectedApi();

  return {
    async createTicket(
      input: CreateTicketInput,
      signal?: AbortSignal,
    ): Promise<Ticket> {
      const body = {
        project_id: toPositiveId(input.projectId, 'プロジェクトID'),
        title: input.title,
        description: input.description ?? null,
        ...(input.status !== undefined ? { status: input.status } : {}),
        ...(input.priority !== undefined ? { priority: input.priority } : {}),
        assignee_id: toAssigneeId(input.assigneeId) ?? null,
      };

      const response = await translateFailure(
        api.sendJson<{ data?: TicketResponse | null }>(
          'POST',
          '/api/tickets',
          body,
          { signal },
        ),
        toWriteError,
      );

      return readTicket(response);
    },

    async updateTicket(
      id: string,
      input: UpdateTicketInput,
      signal?: AbortSignal,
    ): Promise<Ticket> {
      const assigneeId = toAssigneeId(input.assigneeId);
      const body = {
        ...(input.expectedVersion !== undefined
          ? { expected_version: input.expectedVersion }
          : {}),
        ...(input.title !== undefined ? { title: input.title } : {}),
        ...(input.description !== undefined
          ? { description: input.description }
          : {}),
        ...(input.status !== undefined ? { status: input.status } : {}),
        ...(input.priority !== undefined ? { priority: input.priority } : {}),
        ...(assigneeId !== undefined ? { assignee_id: assigneeId } : {}),
      };

      const response = await translateFailure(
        api.sendJson<{ data?: TicketResponse | null }>(
          'PATCH',
          `/api/tickets/${encodeURIComponent(id)}`,
          body,
          { signal },
        ),
        toWriteError,
      );

      return readTicket(response);
    },

    async deleteTicket(id: string, signal?: AbortSignal): Promise<void> {
      await translateFailure(
        api.sendJson<unknown>(
          'DELETE',
          `/api/tickets/${encodeURIComponent(id)}`,
          undefined,
          { signal },
        ),
        toWriteError,
      );
    },
  };
}

function readTicket(body: { data?: TicketResponse | null } | null): Ticket {
  if (!body || !body.data) {
    throw new TicketApiError('チケットの応答形式が不正です。');
  }

  return toTicket(body.data);
}
