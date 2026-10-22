import { http, HttpResponse } from 'msw';
import { expect, it } from 'vitest';
import { server } from '@/test/mocks/server';
import { url } from '../setup';

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
  const api = await import('../../projectApi');
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
  const api = await import('../../projectApi');
  await expect(api.archiveProject('4')).rejects.toThrow('未完了のチケット');
});
