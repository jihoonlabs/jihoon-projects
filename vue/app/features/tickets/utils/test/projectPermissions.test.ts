import { describe, expect, it } from 'vitest';

import { toProject } from '../../api/projectMapper';
import { projectFixture } from '../../api/test/projectFixture';
import type { ProjectMember } from '../../types/project';
import {
  canManageMembers,
  canManageProject,
  canWriteProject,
  resolveCurrentMembership,
} from '../projectPermissions';

const project = (overrides: Parameters<typeof projectFixture>[0] = {}) =>
  toProject(projectFixture(overrides));

const member = (
  role: ProjectMember['role'],
  permission: ProjectMember['permission'],
): ProjectMember => ({
  id: '7',
  name: 'Aki',
  email: 'aki@example.com',
  role,
  permission,
});

const base = {
  project: project(),
  membership: undefined,
  isAdmin: false,
  sessionActive: true,
};

describe('プロジェクトの権限判定', () => {
  it('リーダーだけがプロジェクトを運用でき、書き込み権限のある人は運用できないこと', () => {
    expect(
      canManageProject({ ...base, membership: member('leader', 'read') }),
    ).toBe(true);
    expect(
      canManageProject({ ...base, membership: member('member', 'write') }),
    ).toBe(false);
  });

  it('書き込み権限のある人だけがチケットを編集できること', () => {
    expect(
      canWriteProject({ ...base, membership: member('member', 'write') }),
    ).toBe(true);
    expect(
      canWriteProject({ ...base, membership: member('leader', 'read') }),
    ).toBe(false);
  });

  it('管理者は、所属していなくても運用と編集ができること', () => {
    expect(canManageProject({ ...base, isAdmin: true })).toBe(true);
    expect(canWriteProject({ ...base, isAdmin: true })).toBe(true);
  });

  it('アーカイブ済みのプロジェクトでは、編集もメンバー管理もできないこと', () => {
    const archived = {
      ...base,
      project: project({ archived_at: '2026-11-01' }),
    };

    expect(canWriteProject({ ...archived, isAdmin: true })).toBe(false);
    expect(
      canManageMembers({
        ...archived,
        membership: member('leader', 'write'),
      }),
    ).toBe(false);
  });

  it('セッションが切れている、またはプロジェクトが未選択なら、どの権限もないこと', () => {
    expect(
      canWriteProject({ ...base, isAdmin: true, sessionActive: false }),
    ).toBe(false);
    expect(canManageProject({ ...base, isAdmin: true, project: null })).toBe(
      false,
    );
    expect(canManageMembers({ ...base, isAdmin: true, project: null })).toBe(
      false,
    );
  });

  it('リーダーは、未アーカイブのプロジェクトでメンバーを管理できること', () => {
    expect(
      canManageMembers({ ...base, membership: member('leader', 'read') }),
    ).toBe(true);
    expect(
      canManageMembers({ ...base, membership: member('member', 'write') }),
    ).toBe(false);
  });
});

describe('自分のメンバー情報の解決', () => {
  const members = [
    member('member', 'read'),
    { ...member('leader', 'write'), id: '8' },
  ];
  const current = {
    members,
    membersProjectId: '1',
    selectedProjectId: '1',
    membersSession: 3,
    sessionRevision: 3,
    userId: 7,
  };

  it('同じプロジェクト・同じセッションの応答から、自分のメンバー情報を返すこと', () => {
    expect(resolveCurrentMembership(current)).toEqual(members[0]);
  });

  it('プロジェクトを切り替えた後の古い応答は使わないこと', () => {
    expect(
      resolveCurrentMembership({ ...current, selectedProjectId: '2' }),
    ).toBeUndefined();
  });

  it('再ログインなどでセッションが変わった後の古い応答は使わないこと', () => {
    expect(
      resolveCurrentMembership({ ...current, sessionRevision: 4 }),
    ).toBeUndefined();
  });

  it('利用者が不明、または自分が一覧にいない場合は undefined を返すこと', () => {
    expect(
      resolveCurrentMembership({ ...current, userId: null }),
    ).toBeUndefined();
    expect(
      resolveCurrentMembership({ ...current, userId: 99 }),
    ).toBeUndefined();
  });
});
