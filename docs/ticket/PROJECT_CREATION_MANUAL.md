# Project creation — home Codex manual

## What changed
Any authenticated active user can create a project and becomes its first leader with write permission. The project's 3-letter key is separate from its numeric ID. New projects now also persist an original creator ID (`created_by`) independently of who is currently leader.

## Why
Leadership may be transferred, but the original creator must remain identifiable for future guarded permanent-deletion authorization. A caller cannot choose or change `created_by` through project create/update APIs. Old projects have `created_by = null` until a deliberate legacy ownership policy is approved.

## Validation and limitations
- Branch: `feature/ticket-project-creation`; no Epic merge.
- Run `php artisan migrate`, `php artisan test --filter=ProjectManagementTest`, project feature regressions and `vendor/bin/pint --test` from `laravel/`.
- Tests have been authored, **not run** in the remote environment.
- This does not grant creators new delete privileges or implement key confirmation, audit retention, archive/restore or purge.
- When integrating with `feature/ticket-project-audit-history`, preserve creator assignment, initial leader membership and audit insert in one transaction; reconcile both branches' `ProjectController` changes. See `PROJECT_CREATION_WORK.md`.
