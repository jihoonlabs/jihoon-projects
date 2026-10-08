# Ticket V1 remote integration verification handoff

## Scope and safety
- Branch: `feature/ticket`; latest SHA must be checked with `git rev-parse HEAD`.
- Do not merge/push `main`, delete branches, reset/stash unrelated work, or overwrite dirty files.
- Work from a clean, isolated checkout. Keep `AGENTS.md` aligned with approved `main` rules.
- Earlier baseline: Laravel 109 tests / 487 assertions; React 129 tests, TypeScript, ESLint and build passed **before** the collision retry changes. Do not reuse those numbers as current results.

## Minimal verification (from repository root)
```bash
git fetch origin
git status --short
git rev-parse HEAD
git rev-parse origin/main
git rev-parse origin/feature/ticket
git diff --name-status origin/main...origin/feature/ticket
```
Only in a clean checkout on the Ticket branch:
```bash
cd laravel
php artisan test --filter=ProjectManagementTest
php artisan test --filter=ProjectTicketKeyMigrationTest
php artisan test --filter=TicketSeederTest
php artisan test
./vendor/bin/pint --test
cd ../react
npm run test:run
npx tsc --noEmit
npm run lint
npm run build
```
The React command above matches the checked `react/package.json` `test:run` script.

## Concurrency regression expectations
- Creating a project generates an uppercase three-letter key.
- Simulated DB UNIQUE collision for `project_key`: creation retries with a new key; the original project's key is unchanged.
- Five consecutive key collisions: retry is bounded, request fails, and no new project is persisted.
- Non-`project_key` unique violations are not retried.
- The test simulates an insert race using an Eloquent creating-event listener; it does **not** prove two independent MySQL sessions behave correctly.

## MySQL validation (isolated disposable DB only)
- Confirm migrations run against the intended MySQL version, including `project_key` unique index and `next_ticket_number`.
- Seed projects/tickets before applying the key migration; confirm backfill preserves ticket count and assigns distinct keys and per-project issue numbers.
- Confirm two independent connections creating projects concurrently cannot persist the same key; retry behavior must be observed.
- Confirm reseeding does not reset existing keys or counters, and deleting tickets never reuses numbers.
- Do not run destructive migrations or refresh on a shared/company DB.

## Main integration preflight
- `git merge-base origin/main origin/feature/ticket` and `git diff --name-status origin/feature/ticket...origin/main`.
- Main-only changes previously observed in `AGENTS.md`, `docs/agent/WORK.md`, and `docs/agent/MANUAL.md`. Recheck fresh refs.
- To simulate a merge, use a **separate clean disposable checkout** only with authorization for temporary worktree/branch creation; otherwise do not simulate.
- Review actual merge conflicts before claiming integration readiness. GitHub compare output alone does not prove a conflict-free merge.

## Verification record template
- Checked Ticket SHA / main SHA:
- Test environment (PHP, Laravel, DB engine/version, Node):
- ProjectManagementTest:
- Migration / Seeder tests:
- Full Laravel / Pint:
- React tests / TypeScript / ESLint / build:
- MySQL migration / independent-session race:
- Merge simulation / conflicts:
- Existing baseline vs newly executed:
- Remaining blockers:

## Known limitations
- Remote GitHub file inspection and commits do not execute tests.
- Current retry code detects `project_key` via the unique exception message. Confirm SQLite and MySQL driver error formats before approving production behavior.
- Main merge/push and branch deletion require separate approval.
