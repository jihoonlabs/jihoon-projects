import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { signInAs } from '~/test/auth/signInAs';
import { apiUrl } from '~/test/mocks/apiUrl';
import { overrideApi } from '~/test/mocks/overrideApi';
import { ticketApi } from '~/test/mocks/tickets/ticketApiHandlers';

import { TicketApiError } from '../apiErrors';
import { useTicketApi } from '../ticketApi';
import { toTicket } from '../ticketMapper';
import { ticketFixture } from './ticketFixture';

describe('チケット API', () => {
  describe('応答の変換', () => {
    it('snake_case・null 項目・数値の担当者 ID を画面用の形にすること', () => {
      expect(toTicket(ticketFixture({ position: 12 }))).toEqual({
        id: '1',
        projectId: '1',
        issueKey: 'TICK-1',
        title: 'First ticket',
        description: null,
        status: 'TODO',
        priority: 'MEDIUM',
        assignee: { id: '7', name: 'Tester', avatarUrl: undefined },
        position: 12,
        version: 1,
        createdAt: '2026-11-01T00:00:00+00:00',
        updatedAt: '2026-11-01T00:00:00+00:00',
      });
    });

    it('課題キー・担当者・日時が null でも変換できること', () => {
      expect(
        toTicket(
          ticketFixture({
            issue_key: null,
            assignee: null,
            created_at: null,
            updated_at: null,
          }),
        ),
      ).toMatchObject({
        issueKey: null,
        assignee: null,
        createdAt: null,
        updatedAt: null,
      });
    });

    it.each([
      ['欠けている', undefined],
      ['0', 0],
      ['小数', 1.5],
      ['文字列', '1'],
    ])('version が%sチケットを受け付けないこと', (_label, version) => {
      expect(() => toTicket(ticketFixture({ version } as never))).toThrow(
        'バージョン',
      );
    });
  });

  describe('一覧の取得', () => {
    it('data を読み、API が返す順を保つこと', async () => {
      signInAs();
      overrideApi(
        ticketApi.tickets([
          ticketFixture(),
          ticketFixture({ id: '2', position: 1 }),
        ]),
      );

      const tickets = await useTicketApi().fetchTickets();

      expect(tickets.map((ticket) => [ticket.id, ticket.position])).toEqual([
        ['1', 0],
        ['2', 1],
      ]);
    });

    it.each([401, 403, 500])(
      '%i の応答を表示用の失敗にすること',
      async (status) => {
        signInAs();
        overrideApi(ticketApi.ticketsFail(status));

        const failure = await useTicketApi()
          .fetchTickets()
          .catch((error: unknown) => error);

        expect(failure).toBeInstanceOf(TicketApiError);
        expect((failure as TicketApiError).message).toContain(String(status));
      },
    );

    it.each([
      ['data がない', {}],
      ['data が null', { data: null }],
      ['data が配列でない', { data: {} }],
    ])('%s応答を受け付けないこと', async (_label, body) => {
      signInAs();
      overrideApi(
        http.get(apiUrl('/api/tickets'), () => HttpResponse.json(body)),
      );

      await expect(useTicketApi().fetchTickets()).rejects.toThrow(
        '応答形式が不正',
      );
    });
  });
});
