# Project audit history — Codex handoff

Project creation, rename, and the existing admin-only deletion of **empty projects** now leave database audit events. A record keeps the 3-letter key, project ID, actor, date and name/snapshot even after its live row is deleted.

This branch does **not** allow deleting projects with tickets, and it does **not** yet guarantee non-reuse of a deleted key. That requires a reservation-aware key generator before a broader purge workflow can be enabled. Archive/restore events must be integrated with the separate lifecycle Child; creator membership requires the creation Child.

Branch: `feature/ticket-project-audit-history`. All changes committed on remote Child, never merged. Laravel tests, migration and integration **not executed remotely**. See `PROJECT_AUDIT_WORK.md` for validation and merge conflict boundaries.
