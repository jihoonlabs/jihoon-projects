import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import {
  createProject,
  addProjectMember,
  fetchProjectMembers,
  fetchProjects,
  removeProjectMember,
  updateProjectMember,
} from '../projectApi';

const url = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

describe('Project API boundary', () => {
  it('maps accessible Project and member resources to string IDs', async () => {
    server.use(
      http.get(`${url}/api/projects`, () =>
        HttpResponse.json({
          data: [
            {
              id: 4,
              name: 'Product',
              project_key: 'PRD',
              board_version: 3,
              color: '#e3f2fd',
            },
          ],
        }),
      ),
      http.get(`${url}/api/projects/4/members`, () =>
        HttpResponse.json({
          data: [
            {
              id: 7,
              name: 'Aki',
              email: 'aki@example.com',
              role: 'leader',
              permission: 'read',
            },
          ],
        }),
      ),
    );
    await expect(fetchProjects()).resolves.toEqual([
      {
        id: '4',
        name: 'Product',
        projectKey: 'PRD',
        boardVersion: 3,
        color: '#e3f2fd',
      },
    ]);
    await expect(fetchProjectMembers('4')).resolves.toEqual([
      {
        id: '7',
        name: 'Aki',
        email: 'aki@example.com',
        role: 'leader',
        permission: 'read',
      },
    ]);
  });

  it('sends role and permission changes through the CSRF-protected API', async () => {
    server.use(
      http.post(`${url}/api/projects/4/members`, async ({ request }) => {
        expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
        expect(await request.json()).toEqual({
          email: 'aki@example.com',
          role: 'member',
          permission: 'write',
        });
        return HttpResponse.json(
          {
            data: {
              id: 7,
              name: 'Aki',
              email: 'aki@example.com',
              role: 'member',
              permission: 'write',
            },
          },
          { status: 201 },
        );
      }),
      http.patch(`${url}/api/projects/4/members/7`, async ({ request }) => {
        expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
        expect(await request.json()).toEqual({
          role: 'leader',
          permission: 'read',
        });
        return HttpResponse.json({
          data: {
            id: 7,
            name: 'Aki',
            email: 'aki@example.com',
            role: 'leader',
            permission: 'read',
          },
        });
      }),
      http.delete(`${url}/api/projects/4/members/7`, ({ request }) => {
        expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
        return new HttpResponse(null, { status: 204 });
      }),
    );
    await expect(
      addProjectMember('4', {
        email: 'aki@example.com',
        role: 'member',
        permission: 'write',
      }),
    ).resolves.toMatchObject({ id: '7' });
    await expect(
      updateProjectMember('4', '7', { role: 'leader', permission: 'read' }),
    ).resolves.toMatchObject({ role: 'leader' });
    await expect(removeProjectMember('4', '7')).resolves.toBeUndefined();
  });

  it('rejects failed requests and malformed envelopes', async () => {
    server.use(
      http.get(`${url}/api/projects`, () => HttpResponse.json({ data: null })),
    );
    await expect(fetchProjects()).rejects.toThrow('応答形式');
    server.use(
      http.get(`${url}/api/projects/4/members`, () =>
        HttpResponse.json({}, { status: 403 }),
      ),
    );
    await expect(fetchProjectMembers('4')).rejects.toThrow('403');
  });
});

it('creates a Project with only the trimmed name and the existing CSRF contract', async () => {
  server.use(
    http.post(`${url}/api/projects`, async ({ request }) => {
      expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
      expect(await request.json()).toEqual({ name: 'New team' });
      return HttpResponse.json(
        {
          data: {
            id: 9,
            name: 'New team',
            project_key: 'NEW',
            board_version: 1,
          },
        },
        { status: 201 },
      );
    }),
  );
  await expect(createProject('  New team  ')).resolves.toEqual({
    id: '9',
    name: 'New team',
    projectKey: 'NEW',
    boardVersion: 1,
  });
});

it('rejects a failed or malformed Project creation response', async () => {
  server.use(
    http.post(`${url}/api/projects`, () =>
      HttpResponse.json({}, { status: 403 }),
    ),
  );
  await expect(createProject('New team')).rejects.toThrow('403');
  server.use(
    http.post(`${url}/api/projects`, () => HttpResponse.json({ data: null })),
  );
  await expect(createProject('New team')).rejects.toThrow('応答形式');
});

it('maps archived Projects and uses existing CSRF routes for lifecycle and leadership', async () => {
  const resource = {
    id: 4,
    name: 'Product',
    project_key: 'PRD',
    board_version: 3,
    archived_at: null,
  };
  server.use(
    http.get(`${url}/api/projects`, ({ request }) => {
      expect(new URL(request.url).searchParams.get('archived')).toBe('1');
      return HttpResponse.json({
        data: [{ ...resource, archived_at: '2026-10-13T00:00:00Z' }],
      });
    }),
    http.patch(`${url}/api/projects/4`, async ({ request }) => {
      expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
      expect(await request.json()).toEqual({ name: 'Renamed' });
      return HttpResponse.json({ data: { ...resource, name: 'Renamed' } });
    }),
    http.post(`${url}/api/projects/4/archive`, ({ request }) => {
      expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
      return HttpResponse.json({
        data: { ...resource, archived_at: '2026-10-13T00:00:00Z' },
      });
    }),
    http.post(`${url}/api/projects/4/restore`, ({ request }) => {
      expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
      return HttpResponse.json({ data: resource });
    }),
    http.post(
      `${url}/api/projects/4/members/7/transfer-leader`,
      ({ request }) => {
        expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
        return HttpResponse.json({
          data: {
            id: 7,
            name: 'Aki',
            email: null,
            role: 'leader',
            permission: 'read',
          },
        });
      },
    ),
  );
  const api = await import('../projectApi');
  await expect(api.fetchProjects({ archived: true })).resolves.toEqual([
    {
      id: '4',
      name: 'Product',
      projectKey: 'PRD',
      boardVersion: 3,
      archivedAt: '2026-10-13T00:00:00Z',
    },
  ]);
  await expect(api.renameProject('4', ' Renamed ')).resolves.toMatchObject({
    name: 'Renamed',
    projectKey: 'PRD',
  });
  await expect(api.archiveProject('4')).resolves.toMatchObject({
    archivedAt: '2026-10-13T00:00:00Z',
  });
  await expect(api.restoreProject('4')).resolves.toMatchObject({
    archivedAt: null,
  });
  await expect(api.transferProjectLeader('4', '7')).resolves.toMatchObject({
    id: '7',
    role: 'leader',
    permission: 'read',
  });
});

it('explains incomplete-ticket archive refusal without treating it as success', async () => {
  server.use(
    http.post(`${url}/api/projects/4/archive`, () =>
      HttpResponse.json({}, { status: 409 }),
    ),
  );
  const api = await import('../projectApi');
  await expect(api.archiveProject('4')).rejects.toThrow('未完了のチケット');
});
