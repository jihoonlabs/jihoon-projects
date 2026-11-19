import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { signInAs } from '~/test/auth/signInAs';
import { apiUrl } from '~/test/mocks/apiUrl';
import { overrideApi } from '~/test/mocks/overrideApi';

import { TicketApiError, TicketConflictError } from '../apiErrors';
import { useTicketWriteApi } from '../ticketWriteApi';
import { ticketFixture } from './ticketFixture';

describe('チケットの作成・更新・削除 API', () => {
  describe('作成', () => {
    it('snake_case で送り、作られたチケットを画面用の形で返すこと', async () => {
      signInAs();
      let sent: unknown;
      overrideApi(
        http.post(apiUrl('/api/tickets'), async ({ request }) => {
          sent = await request.json();
          return HttpResponse.json(
            { data: ticketFixture({ id: '9' }) },
            { status: 201 },
          );
        }),
      );

      const ticket = await useTicketWriteApi().createTicket({
        projectId: '1',
        title: 'New',
        status: 'TODO',
        assigneeId: '7',
      });

      expect(sent).toEqual({
        project_id: 1,
        title: 'New',
        description: null,
        status: 'TODO',
        assignee_id: 7,
      });
      expect(ticket.id).toBe('9');
    });

    it('プロジェクト ID が正の整数でなければ、送らずに失敗すること', async () => {
      signInAs();
      let called = false;
      overrideApi(
        http.post(apiUrl('/api/tickets'), () => {
          called = true;
          return HttpResponse.json({});
        }),
      );

      await expect(
        useTicketWriteApi().createTicket({ projectId: 'abc', title: 'x' }),
      ).rejects.toThrow('プロジェクトID');
      expect(called).toBe(false);
    });
  });

  describe('更新', () => {
    it('指定された項目と expected_version だけを送ること', async () => {
      signInAs();
      let sent: unknown;
      overrideApi(
        http.patch(apiUrl('/api/tickets/1'), async ({ request }) => {
          sent = await request.json();
          return HttpResponse.json({ data: ticketFixture({ version: 3 }) });
        }),
      );

      const ticket = await useTicketWriteApi().updateTicket('1', {
        expectedVersion: 2,
        title: 'Renamed',
        assigneeId: null,
      });

      expect(sent).toEqual({
        expected_version: 2,
        title: 'Renamed',
        assignee_id: null,
      });
      expect(ticket.version).toBe(3);
    });

    it('409 の ticket_conflict を競合エラーとして返すこと', async () => {
      signInAs();
      overrideApi(
        http.patch(apiUrl('/api/tickets/1'), () =>
          HttpResponse.json(
            { message: 'conflict', code: 'ticket_conflict' },
            { status: 409 },
          ),
        ),
      );

      const failure = await useTicketWriteApi()
        .updateTicket('1', { expectedVersion: 1, title: 'x' })
        .catch((error: unknown) => error);

      expect(failure).toBeInstanceOf(TicketConflictError);
    });

    it('その他の失敗は競合ではない表示用の失敗にすること', async () => {
      signInAs();
      overrideApi(
        http.patch(apiUrl('/api/tickets/1'), () =>
          HttpResponse.json({ message: 'Error' }, { status: 500 }),
        ),
      );

      const failure = await useTicketWriteApi()
        .updateTicket('1', { title: 'x' })
        .catch((error: unknown) => error);

      expect(failure).toBeInstanceOf(TicketApiError);
      expect(failure).not.toBeInstanceOf(TicketConflictError);
    });
  });

  describe('削除', () => {
    it('成功したら値を返さず完了すること', async () => {
      signInAs();
      overrideApi(
        http.delete(
          apiUrl('/api/tickets/1'),
          () => new HttpResponse(null, { status: 204 }),
        ),
      );

      await expect(
        useTicketWriteApi().deleteTicket('1'),
      ).resolves.toBeUndefined();
    });
  });
});
