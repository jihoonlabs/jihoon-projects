import { screen } from '@testing-library/vue';
import { http, HttpResponse } from 'msw';
import { vi } from 'vitest';

import { signInAs } from '~/test/auth/signInAs';
import { apiUrl } from '~/test/mocks/apiUrl';
import { overrideApi } from '~/test/mocks/overrideApi';
import { renderScreen } from '~/test/renderScreen';

import { ticketFixture } from '../../../api/test/ticketFixture';
import { toTicket } from '../../../api/ticketMapper';
import type { ProjectMember } from '../../../types/project';
import type { TicketResponse } from '../../../types/ticket';
import TicketModal from '../TicketModal.vue';

/** サーバーが返すチケット（担当者は ID 7 の Tester、バージョン 1） */
export const serverTicket = ticketFixture();

export const writer: ProjectMember = {
  id: '7',
  name: 'Tester',
  email: 'tester@example.test',
  role: 'member',
  permission: 'write',
};

/**
 * 現在の内容を返す 1 件取得。呼ぶたびに最新の内容を返すので、再取得のテストで内容を差し替えられる
 */
export function serveTicket(current: () => TicketResponse) {
  return http.get(apiUrl(`/api/tickets/${serverTicket.id}`), () =>
    HttpResponse.json({ data: current() }),
  );
}

/** 更新（PATCH）を受け、送られた本文を bodies に残す */
export function recordUpdates(
  respond: (body: Record<string, unknown>) => Response | Promise<Response>,
  id = serverTicket.id,
) {
  const bodies: Array<Record<string, unknown>> = [];
  const handler = http.patch(
    apiUrl(`/api/tickets/${id}`),
    async ({ request }) => {
      const body = (await request.json()) as Record<string, unknown>;
      bodies.push(body);

      return respond(body);
    },
  );

  return { handler, bodies };
}

export const conflictResponse = () =>
  HttpResponse.json(
    { message: 'conflict', code: 'ticket_conflict' },
    { status: 409 },
  );

export const savedResponse = (changes: Partial<TicketResponse>) =>
  HttpResponse.json({ data: { ...serverTicket, version: 2, ...changes } });

interface RenderOptions {
  /** 開くチケット（null なら作成）。既定はカードの内容 */
  ticket?: ReturnType<typeof toTicket> | null;
  /** 最新取得の応答。null なら応答を用意しない */
  detail?: TicketResponse | null;
  readOnly?: boolean;
}

export async function renderModal(options: RenderOptions = {}) {
  signInAs();
  const detail = options.detail === undefined ? serverTicket : options.detail;
  if (detail) overrideApi(serveTicket(() => detail));

  const onClose = vi.fn();
  const view = await renderScreen(TicketModal, {
    props: {
      ticket:
        options.ticket === undefined ? toTicket(serverTicket) : options.ticket,
      projectId: '1',
      projectColor: null,
      projectMembers: [writer],
      projectChoice: null,
      readOnly: options.readOnly ?? false,
      onClose,
    },
  });

  return { ...view, onClose };
}

/** 詳細が表示されてから、編集モードに入る */
export async function startEditing(user: {
  click: (el: Element) => Promise<void>;
}) {
  await screen.findByRole('heading', { name: 'チケット詳細' });
  await user.click(screen.getByRole('button', { name: '編集' }));
}
