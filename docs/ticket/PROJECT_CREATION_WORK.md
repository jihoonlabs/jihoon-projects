# Ticket Project Creation Child — WORK

## Parent and responsibility
- Parent Epic: `feature/ticket`. This branch: `feature/ticket-project-creation`.
- Responsibility: project creation by an authenticated active user; automatically assign an immutable three-letter project key and enroll the creator as the initial `leader` with `write` permission, atomically.
- Outside scope: project-key search / URL routing / React project creation screen, leader handover, project archive / restore / irreversible deletion, role changes for existing members. Split those into separate Child branches if implemented.
- Invariants: retain numeric database project ID/FKs internally; project_key cannot be changed by renaming; Ticket numbering remains project-scoped. Unauthorized access to unrelated projects stays forbidden.

## Implementation state (2026-10-08)
- Imported two commits from Epic into this Child: `03a983f5c925a2ffaffcbf37e06de2182e0cacdb` (controller), `6e7614b06d8022b15cdd7ee06f841ceac4c90e0d` (test).
- `POST /api/projects` no longer admin-only, creation and initial membership use a DB transaction, creator becomes `leader/write`.
- Existing unique project_key retry behavior remains, and errors other than project_key conflicts are not retried.
- Existing `PATCH`/`DELETE` project API remains admin-only: modifications to these permissions are separate work.
- Tests added/changed, but **NOT executed** on this branch; no claims of successful validation.

## Verification and acceptance
- Run focused `php artisan test --filter=ProjectManagementTest` and `vendor/bin/pint --test` at an environment with existing dependencies, without installing packages solely for this work.
- Check active authenticated non-admin user: response 201, 3-letter immutable project_key, exact one leader/write membership for creator, new project appears in their own project list.
- Check admin creation, unauthorized/guest rejection, unrelated project visibility restrictions, key collision retry, failure rollback (no orphan Project or member).
- Run related Project/Ticket regression tests and review final diff. If verified, record exact test results and adopted Child SHA in the Epic MD before integration.
- Until then, keep Child unmerged.

## Future sibling Child candidates
- `feature/ticket-project-leadership`: single-leader invariant, transfer operation, permissions.
- `feature/ticket-project-discovery`: project-key search and project selection.
- `feature/ticket-project-lifecycle`: archive / restore / completed-ticket checks / hard-delete guardrails.
- UI changes could form a separate Child after the backend contracts are confirmed.
