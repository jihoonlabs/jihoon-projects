# Project lifecycle API — Child WORK

## Context and scope
- Branch: `feature/ticket-project-lifecycle-api`; parent Epic: `feature/ticket`.
- Responsibility implemented so far: archive a project after all tickets reach DONE, hide it from the default project list, separately list archived projects, restore an archived project, and prevent writes on archived tickets/comments.
- Outside scope/not implemented: irreversible project deletion of completed tickets (including FK deletion, data retention and never-reuse-key strategy), creator ownership, React UI, leadership transfer, key search, Epic integration. Do not confuse archive with permanent deletion.

## API and persistence contract
- Migration: `2026_10_08_000001_add_archived_at_to_projects_table.php` adds nullable `projects.archived_at`.
- `GET /api/projects`: active projects only. `GET /api/projects?archived=1`: archived projects only. Existing membership scoping remains, and admins can list all accessible projects. `GET /api/projects/{id}` can still read archived projects if authorized.
- `POST /api/projects/{id}/archive`: system admin or current project leader only. Requires every ticket to have status `DONE` (zero tickets also allowed). Returns project with non-null `archived_at`. Transaction/project row lock coordinates with ticket-changing transactions.
- `POST /api/projects/{id}/restore`: system admin or current leader. Returns project with null `archived_at`.
- Project key/IDs and all tickets remain unchanged when archived. Ticket create/edit/move/delete APIs check archive state, including within project-row-locked transactions; comment mutations reject archived projects. Reads remain available.
- Existing `DELETE /api/projects/{id}` behavior is unchanged (admin only, rejects projects with any ticket). Permanent deletion should be handled as separate verified responsibility after ownership is modeled.

## Verification gate — IMPORTANT
- **Remote GitHub editing only. No PHP execution, migration, Pint, SQLite/MySQL, HTTP request tests, or browser tests run.**
- Run `php artisan migrate` on a disposable DB and `php artisan test --filter=ProjectManagementTest`, `vendor/bin/pint --test`, then Ticket and TicketComment feature regressions. No need to install packages on the company computer.
- Validate active/archived lists with admin and normal member; all DONE vs mixed ticket states; empty project; leader vs member vs admin; repeat archive/restore; ticket write and comment edit guards; project key / ticket sequence unchanged; migration rollback; MySQL schema compatibility.
- **Known risk:** comment mutations currently perform an archive-state check without a project row lock; a concurrent archive and comment write can race. Test and reconcile this before approval.
- **Known risk:** existing projects may have no leader; only admins can archive/restore them until ownership/leadership integration. Check integration with creator auto-enrollment and single-leader Child.
- **Known risk:** ticket `GET /api/tickets` still includes archived project tickets, intentionally preserving history for authorized readers; React must filter/display appropriately.
- **Known risk:** branch creation predates other Child changes; do not merge unverified work directly. Retest against the combined child contract before Epic integration.

## Status
Implementation + tests + docs committed on this Child for local Codex review. Tests remain unverified. Never merge into Epic/main without approval.
