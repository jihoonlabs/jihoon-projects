# Ticket Audit History — Child WORK

## Purpose
Preserve evidence of Ticket creation, updates, board moves and deletion, even when the live Ticket is deleted. This Child does **not** enable permanent Project deletion.

## Branch and implementation
- Child: `feature/ticket-audit-history`, base: `feature/ticket`.
- A new append-only-by-convention `ticket_audit_events` table stores project ID/key, ticket ID/key, actor ID/name, event type, JSON snapshot and timestamp.
- The audit table deliberately uses **no foreign keys** so rows are not cascaded away with a live ticket, project, or user.
- Ticket create, update, board move and delete endpoints now write audit events **within their DB transactions**, preserving existing read/write authorization. Snapshots reflect the post-operation ticket state for non-delete actions; delete records a final pre-deletion state.
- Snapshot includes title, description, status, priority, assignee user ID, original created time and deletion time. No new public audit read API yet; authorization and retention policy for that API must be reviewed.
- Test file: `laravel/tests/Feature/Ticket/TicketAuditHistoryTest.php`: creation/update timeline, deleted-ticket snapshot/actor, read-only denial and repeat delete. Test code only; not run.

## Not completed
- Auditing project rename/archive/restore, member changes and leadership handover. Comment create/update/delete now also log snapshots; runtime verification remains outstanding. Ticket create/update/move/delete are implemented, but runtime validation is outstanding.
- Project creator ownership, project tombstones, key reservation, permanent deletion, user-facing work history, export, archive/retention schedule and database access policies.
- No hash-chain/WORM guarantee: application code and DB administrators can potentially modify records. Do not describe this as tamper-proof.
- No independent backup exists. Audit table alone does not protect against database loss or administrator intervention.
- Ticket descriptions may contain confidential information; audit read permissions must remain restricted to project members / administrators and retention rules must be agreed before exposing a read endpoint.
- Integration with lifecycle Child requires reconciling **shared TicketController edits**; do not overwrite its archive-state lock. Its archived read-only guarantees must remain intact.
- Other Child commits are unmerged; audit scope is independent.

## Validation (NOT RUN)
- In `laravel/`: `php artisan migrate`, `php artisan test --filter=TicketAuditHistoryTest`, existing Ticket feature regressions and `vendor/bin/pint --test`.
- On SQLite and MySQL verify migration; check ticket deletion with valid writer, read-only member, outsider and admin, missing ticket, failed audit insert/transaction rollback and project key preservation.
- Confirm create/update/move all write one corresponding event with correct actor and snapshot; verify no audit event for rejected operations, and rollback of a failed audit insert.
- Inspect FK cascade behavior and backup/restore, compare Child against Epic and record accepted SHA.
- All work currently remotely committed; **no tests executed and no merge**.

## Policy decision held for user
Default to reversible Archive, not hard deletion. Future deletion requires actor/key confirmation, creator/admin authorization, all tasks completed, immutable key reservation and a preserved project/ticket audit trail before purge.

## 2026-10-08 follow-up
- Added application-level ticket events: `ticket.created`, `ticket.updated`, `ticket.moved`, `ticket.deleted`.
- Each event captures a snapshot; this is a point-in-time history, not a computed before/after patch. Existing older tickets only begin recording changes after this code is deployed; no backfill is claimed.
- Project lifecycle Child edits the same controller; Codex must combine archive-state lock checks into every transaction before accepting either Child.

## Comment history follow-up
- Comment create/update/delete now each append `comment.created`, `comment.updated`, or `comment.deleted` to the existing ticket audit ledger. Snapshots contain comment ID, author ID, content and created-at; actor and project/ticket keys are stored in ledger columns. These are written in the same DB transaction as the comment mutation.
- Existing comment permission contract differs from Ticket edits: a project member with `read` may currently create a comment and edit/delete their own comment. That existing behavior is preserved, **but user expectation may require explicit policy review** before integration. Nonmembers cannot comment.
- **Integration blocker:** the lifecycle Child's `TicketCommentController` includes an archived-project check. This audit Child serializes by locking the project row but does NOT itself check `archived_at` (because its Epic base has no archive column). When combining branches, preserve both the lock and the lifecycle's 409 check, including delete.
- Comment bodies are sensitive and are preserved in the ledger even after live deletion. Keep audit read APIs private until role/privacy/retention rules and backup requirements are approved. Do not add unrestricted browse endpoints.
- New focused tests cover all three comment mutations and non-member denial. Still NOT RUN in remote GitHub.
