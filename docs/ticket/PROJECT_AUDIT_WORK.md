# Project Audit — Child WORK

## Responsibility
- Branch: `feature/ticket-project-audit-history`; parent: `feature/ticket`.
- Preserve project identity/action evidence on create, rename and current guarded deletion.
- No project archive/restore actions exist in this Child's base. Implement those audit events when integrating `feature/ticket-project-lifecycle-api`; do not claim them complete.

## Implemented contract
- New `project_audit_events` migration: project ID/key, actor ID/name, action, JSON snapshot, timestamp, no FK references to live rows.
- `project.created`: name and fixed project key are recorded together with live creation in a transaction. Retries still cover existing project_key unique collisions.
- `project.renamed`: prior/new names and actor are recorded in the same transaction as update; no event if name unchanged.
- `project.deleted`: last name, original creation timestamp, actor and fixed key remain after deletion. **Existing deletion restriction remains**: admin only, zero tickets.
- No public audit browse endpoint, so historical details are not exposed to unrelated users.
- Tests authored: `laravel/tests/Feature/Ticket/ProjectAuditHistoryTest.php` for create/rename, safe delete, rejection with tickets and normal-user denial.

## Critical integration blockers
- **Never reuse key:** this branch records deleted keys, but `Project::booted()` still only checks live `projects` rows when generating new keys. Update key generation / collision strategy to consult durable reservations or the ledger **before approving irreversible deletion**; add collision and exhaustion tests. Do not claim key-reuse protection is complete.
- **Creator vs leader:** `created_by` ownership is not modeled yet. Do not enable creator deletion before verified schema and authorization.
- **Lifecycle Child** modifies the same `ProjectController` for archive/restore and archived name-write guards. Manually reconcile transaction locks and append `project.archived` / `project.restored` events inside state-changing transactions; avoid lost updates or blind merge.
- **Creation Child** modifies the same `ProjectController` to allow all active users to create with leader/write membership. Keep atomic creator membership + audit insert inside its collision-retry transaction.
- **Key search Child** also changes `ProjectController`. Merge approval requires 3-way review of each action and tests, not only automatic resolution.
- Auditing project deletion cannot replace ticket history or a database backup. No tamper-proof guarantee, retention rules and access policy not finalized. Preserve confidential descriptions in appropriate restricted storage.

## Home Codex checklist
- Verify branch and diff, AGENTS.md, this work MD; run `php artisan migrate`, `php artisan test --filter=ProjectAuditHistoryTest`, `php artisan test --filter=ProjectManagementTest`, `vendor/bin/pint --test`.
- Test on SQLite and MySQL. Validate role denial, transaction rollback when audit insert fails, concurrent delete/update, FK cascades, and deletion when no tickets.
- After reconciling the dependent children, verify project visibility isolation, archived read-only, ownership, keys, ticket write rights, and audit record retention.
- Current status: remote commits and tests authored; runtime tests **NOT RUN**; **NOT MERGED**.
