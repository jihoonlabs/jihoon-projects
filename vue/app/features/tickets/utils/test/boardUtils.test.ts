import { describe, expect, it } from 'vitest';

import { toProject } from '../../api/projectMapper';
import { toTicket } from '../../api/ticketMapper';
import { projectFixture } from '../../api/test/projectFixture';
import { ticketFixture } from '../../api/test/ticketFixture';
import { groupByColumn } from '../boardColumns';
import { filterTickets, ticketsInScope } from '../filterTickets';
import { canManageProject, canWriteProject } from '../projectPermissions';
import { resolveInitialProjectId } from '../resolveProjectSelection';

const ticket = (overrides: Parameters<typeof ticketFixture>[0] = {}) =>
  toTicket(ticketFixture(overrides));

describe('ボードの列', () => {
  it('5 つの列に分け、各列を position の昇順に並べること', () => {
    const columns = groupByColumn([
      ticket({ id: 'b', status: 'TODO', position: 2 }),
      ticket({ id: 'a', status: 'TODO', position: 1 }),
      ticket({ id: 'c', status: 'DONE', position: 0 }),
    ]);

    expect(columns.map((column) => column.id)).toEqual([
      'BACKLOG',
      'TODO',
      'IN_PROGRESS',
      'IN_REVIEW',
      'DONE',
    ]);
    expect(columns[1]!.tickets.map((item) => item.id)).toEqual(['a', 'b']);
    expect(columns[4]!.tickets.map((item) => item.id)).toEqual(['c']);
  });

  it('渡された配列の順序を変えないこと', () => {
    const input = [
      ticket({ id: 'b', position: 2 }),
      ticket({ id: 'a', position: 1 }),
    ];

    groupByColumn(input);

    expect(input.map((item) => item.id)).toEqual(['b', 'a']);
  });
});

describe('チケットの絞り込み', () => {
  const mine = ticket({ id: '1', title: 'Login bug' });
  const unassigned = ticket({ id: '2', title: 'Docs', assignee: null });
  const keyed = ticket({ id: '3', issue_key: 'ABC-9', assignee: null });
  const all = [mine, unassigned, keyed];
  const base = { searchQuery: '', assigneeFilter: 'ALL' as const };

  it('タイトルと課題キーを大文字小文字を区別せず検索すること', () => {
    expect(
      filterTickets(all, { ...base, searchQuery: 'LOGIN', currentUserId: 7 }),
    ).toEqual([mine]);
    expect(
      filterTickets(all, { ...base, searchQuery: 'abc-9', currentUserId: 7 }),
    ).toEqual([keyed]);
  });

  it('自分の担当だけに絞り込むこと', () => {
    expect(
      filterTickets(all, { ...base, assigneeFilter: 'ME', currentUserId: 7 }),
    ).toEqual([mine]);
  });

  it('利用者が不明なとき、自分の担当は 0 件にすること', () => {
    expect(
      filterTickets(all, {
        ...base,
        assigneeFilter: 'ME',
        currentUserId: null,
      }),
    ).toEqual([]);
  });

  it('未割り当てだけに絞り込むこと', () => {
    expect(
      filterTickets(all, {
        ...base,
        assigneeFilter: 'UNASSIGNED',
        currentUserId: 7,
      }),
    ).toEqual([unassigned, keyed]);
  });
});

describe('表示するプロジェクトの範囲', () => {
  const inA = ticket({ id: '1', project_id: 'A' });
  const inB = ticket({ id: '2', project_id: 'B' });
  const hidden = ticket({ id: '3', project_id: 'Z' });
  const available = new Set(['A', 'B']);

  it('全体表示でも、一覧にないプロジェクトのチケットは出さないこと', () => {
    expect(ticketsInScope([inA, inB, hidden], 'ALL', available)).toEqual([
      inA,
      inB,
    ]);
  });

  it('プロジェクトを選んだら、そのチケットだけを出すこと', () => {
    expect(ticketsInScope([inA, inB, hidden], 'B', available)).toEqual([inB]);
  });
});

describe('最初に選ぶプロジェクト', () => {
  const projects = [
    toProject(projectFixture({ id: '1' })),
    toProject(projectFixture({ id: '2' })),
  ];

  it('URL で指定された、一覧にあるプロジェクトを選ぶこと', () => {
    expect(resolveInitialProjectId(projects, '2', false)).toBe('2');
  });

  it('一覧にない指定は全体表示にすること', () => {
    expect(resolveInitialProjectId(projects, '9', false)).toBe('ALL');
  });

  it('デモモードのときだけ先頭のプロジェクトを選ぶこと', () => {
    expect(resolveInitialProjectId(projects, null, true)).toBe('1');
    expect(resolveInitialProjectId(projects, null, false)).toBe('ALL');
    expect(resolveInitialProjectId([], null, true)).toBe('ALL');
  });
});

describe('プロジェクトの権限', () => {
  const project = toProject(projectFixture());
  const archived = toProject(projectFixture({ archived_at: '2026-11-01' }));
  const member = (role: 'leader' | 'member', permission: 'read' | 'write') => ({
    id: '7',
    name: 'Aki',
    email: null,
    role,
    permission,
  });
  const context = {
    project,
    membership: member('member', 'read'),
    isAdmin: false,
    sessionActive: true,
  };

  it('読み取りだけのメンバーは編集も運用もできないこと', () => {
    expect(canWriteProject(context)).toBe(false);
    expect(canManageProject(context)).toBe(false);
  });

  it('書き込み権限があれば編集でき、リーダーなら運用もできること', () => {
    expect(
      canWriteProject({ ...context, membership: member('member', 'write') }),
    ).toBe(true);
    expect(
      canManageProject({ ...context, membership: member('leader', 'read') }),
    ).toBe(true);
  });

  it('管理者はメンバーでなくても編集・運用できること', () => {
    const admin = { ...context, membership: undefined, isAdmin: true };

    expect(canWriteProject(admin)).toBe(true);
    expect(canManageProject(admin)).toBe(true);
  });

  it('アーカイブ済みは編集できないこと', () => {
    expect(
      canWriteProject({
        ...context,
        project: archived,
        membership: member('leader', 'write'),
      }),
    ).toBe(false);
  });

  it('セッションが切れている間、またはプロジェクト未選択なら何もできないこと', () => {
    const admin = { ...context, isAdmin: true };

    expect(canWriteProject({ ...admin, sessionActive: false })).toBe(false);
    expect(canManageProject({ ...admin, project: null })).toBe(false);
  });
});
