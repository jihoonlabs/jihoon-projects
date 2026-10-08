# Ticket Audit History — Child WORK

## Purpose
Prevent the loss of evidence that work existed when a Ticket is deleted. This Child does **not** enable permanent Project deletion.

## Branch and implementation
- Child: `feature/ticket-audit-history`, base: `feature/ticket`.
- A new append-only-by-convention `ticket_audit_events` table stores project ID/key, ticket ID/key, actor ID/name, event type, JSON snapshot and timestamp.
- The audit table deliberately uses **no foreign keys** so rows are not cascaded away with a live ticket, project, or user.
- Existing ticket DELETE endpoint writes an event and deletes the ticket **within the same DB transaction**, preserving existing read/write authorization.
- Snapshot includes title, description, status, priority, assignee user ID, original created time and deletion time. No new public audit read API yet; authorization and retention policy for that API must be reviewed.
- Test file: `laravel/tests/Feature/Ticket/TicketAuditHistoryTest.php`: deleted-ticket snapshot/actor, read-only denial, repeat delete.

## Not completed
- Auditing ticket creation/edits/moves/comment changes, project rename/archive/restore, member changes and leadership handover.
- Project creator ownership, project tombstones, key reservation, permanent deletion, user-facing work history, export, archive/retention schedule and database access policies.
- No hash-chain/WORM guarantee: application code and DB administrators can potentially modify records. Do not describe this as tamper-proof.
- No independent backup exists. Audit table alone does not protect against database loss or administrator intervention.
- Ticket descriptions may contain confidential information; audit read permissions must remain restricted to project members / administrators and retention rules must be agreed before exposing a read endpoint.
- Integration with lifecycle Child requires reconciling **shared TicketController edits**; do not overwrite its archive-state lock. Its archived read-only guarantees must remain intact.
- Other Child commits are unmerged; audit scope is independent.

## Validation (NOT RUN)
- In `laravel/`: `php artisan migrate`, `php artisan test --filter=TicketAuditHistoryTest`, existing Ticket feature regressions and `vendor/bin/pint --test`.
- On SQLite and MySQL verify migration; check ticket deletion with valid writer, read-only member, outsider and admin, missing ticket, failed audit insert/transaction rollback and project key preservation.
- Inspect FK cascade behavior and backup/restore, compare Child against Epic and record accepted SHA.
- All work currently remotely committed; **no tests executed and no merge**.

## Policy decision held for user
Default to reversible Archive, not hard deletion. Future deletion requires actor/key confirmation, creator/admin authorization, all tasks completed, immutable key reservation and a preserved project/ticket audit trail before purge.
