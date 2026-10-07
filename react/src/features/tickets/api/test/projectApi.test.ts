import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { addProjectMember, fetchProjectMembers, fetchProjects, removeProjectMember, updateProjectMember } from '../projectApi';

const url = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

describe('Project API boundary', () => {
  it('maps accessible Project and member resources to string IDs', async () => {
    server.use(
      http.get(`${url}/api/projects`, () => HttpResponse.json({ data: [{ id: 4, name: 'Product', board_version: 3 }] })),
      http.get(`${url}/api/projects/4/members`, () => HttpResponse.json({ data: [{ id: 7, name: 'Aki', email: 'aki@example.com', role: 'leader', permission: 'read' }] })),
    );
    await expect(fetchProjects()).resolves.toEqual([{ id: '4', name: 'Product', boardVersion: 3 }]);
    await expect(fetchProjectMembers('4')).resolves.toEqual([{ id: '7', name: 'Aki', email: 'aki@example.com', role: 'leader', permission: 'read' }]);
  });

  it('sends role and permission changes through the CSRF-protected API', async () => {
    server.use(
      http.post(`${url}/api/projects/4/members`, async ({ request }) => {
        expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
        expect(await request.json()).toEqual({ email: 'aki@example.com', role: 'member', permission: 'write' });
        return HttpResponse.json({ data: { id: 7, name: 'Aki', email: 'aki@example.com', role: 'member', permission: 'write' } }, { status: 201 });
      }),
      http.patch(`${url}/api/projects/4/members/7`, async ({ request }) => {
        expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
        expect(await request.json()).toEqual({ role: 'leader', permission: 'read' });
        return HttpResponse.json({ data: { id: 7, name: 'Aki', email: 'aki@example.com', role: 'leader', permission: 'read' } });
      }),
      http.delete(`${url}/api/projects/4/members/7`, ({ request }) => {
        expect(request.headers.get('X-XSRF-TOKEN')).toBe('test-csrf-token');
        return new HttpResponse(null, { status: 204 });
      }),
    );
    await expect(addProjectMember('4', { email: 'aki@example.com', role: 'member', permission: 'write' })).resolves.toMatchObject({ id: '7' });
    await expect(updateProjectMember('4', '7', { role: 'leader', permission: 'read' })).resolves.toMatchObject({ role: 'leader' });
    await expect(removeProjectMember('4', '7')).resolves.toBeUndefined();
  });

  it('rejects failed requests and malformed envelopes', async () => {
    server.use(http.get(`${url}/api/projects`, () => HttpResponse.json({ data: null })));
    await expect(fetchProjects()).rejects.toThrow('応答形式');
    server.use(http.get(`${url}/api/projects/4/members`, () => HttpResponse.json({}, { status: 403 })));
    await expect(fetchProjectMembers('4')).rejects.toThrow('403');
  });
});
