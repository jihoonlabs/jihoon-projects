# Project UI Child — WORK

## Responsibility and status
- Branch: `feature/ticket-project-ui`; parent: `feature/ticket`.
- Actual feature added: authenticated user can open a Project creation dialog from the Ticket board, submit a project name, select the returned project immediately, see its immutable three-letter key in the project selector, and filter available projects by name or key.
- API client now retains `project_key` as `projectKey` and calls `POST /api/projects` using the existing Sanctum/CSRF helper. The form displays server failures, blocks duplicate submits, and clears project search after successful creation.
- Focused React component tests authored for create success/failure and project selector key search.
- **No runtime test executed, no browser verified, no merge.** GitHub connector commits are already remote.

## Required dependency and integration contract
- This UI depends on Child `feature/ticket-project-creation` for ordinary users creating projects and automatic creator leader/write enrollment. The Epic baseline still restricts project creation to admin, so the new button will get 403 for non-admin users until those children are integrated.
- `feature/ticket-project-discovery-api` provides server-side project search, but this UI currently filters only the already fetched project list. Do not confuse this with paginated server-side search.
- `feature/ticket-project-lifecycle-api` hides archived projects in the default list. This UI has **no archive/restore UI** yet.
- `feature/ticket-project-leadership` changes member-role semantics. Existing `ProjectMembersDialog` still offers direct leader promotion, so this UI must be reconciled with the dedicated transfer endpoint before integration.
- Existing React mocks/tests that construct `Project` objects must be updated to supply `projectKey` if TypeScript reports errors. Do not alter unrelated modules without identifying a concrete failure.

## Home Codex validation
1. Check branch/diff and `AGENTS.md`, then `docs/ticket/PROJECT_UI_WORK.md`.
2. From `react/`, run `pnpm test:run`, `pnpm exec tsc --noEmit`, `pnpm lint`, `pnpm build` (existing dependencies only).
3. Verify project creation dialog, success auto-selection, CSRF/auth failure, empty name, duplicate-click protection, key/name search and no-project state in browser.
4. In an isolated integration environment, combine with the **verified** creation API Child; verify new project creator is leader/write and can create ticket `ABC-01`. Record test results and selected Child SHAs.
5. Never merge to Epic/main without explicit user approval.

## Risks
- Existing projects without `project_key` would show an empty key; current API migration should populate keys.
- Client-side search loads all active projects; for growth, use server-side paginated search in a separate scoped task.
- No actual end-to-end flow has been verified in this remote-only environment.
