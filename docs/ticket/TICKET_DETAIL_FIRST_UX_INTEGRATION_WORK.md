# Ticket Detail UX Integration Candidate

owner_repo: jihoonlabs/jihoon-projects
owner_branch: integration/ticket-detail-first-ux-v1
role: integration_candidate
status: verified-not-adopted

## Contract and inputs
- Parent/Epic: `feature/ticket`, base `fdccd96faa20bf9e5f424bd8ae47b1756b2978b6`. Parent adoption is not performed in this task; `docs/ticket/TICKET.md` remains unchanged.
- Selected Child: `feature/ticket-detail-first-ux`, SHA `5c9c6e03a60b9b0ccba86e2d0915d2fbcbf0d99f`, based on the same Epic SHA. This contains reviewed original tip `5d534c7cdf201778c27e98006938248e478b3a0b` plus the Project-refresh rejection boundary fix.
- Apply the Child tip once. Its ancestry includes `884fccd`, `590d8b3`, `03eae7a`, `5d534c7`, and the final review fix. Do not apply those commits separately.
- `ed3cfa4ec5586f4734ca6a78d566ce07617681c1` is not a candidate input: relevant rollback/manual-status contracts were reimplemented in the selected Child. No wholesale cherry-pick or duplicate application.
- Existing candidates checked: `integration/ticket-epic` has obsolete base/worktree metadata; `feature/ticket-v1-integration` targets an earlier main integration and is already ancestral to this Epic; `feature/ticket-project-integration` is an adopted Project-only Child at `083e11c`. Their ownership/base/status do not fit this new candidate. No existing branch/worktree was reset, repaired or deleted.

## Maintained boundaries
- Card title/detail entry, detail-local actions, permissions, focus entry/return and drag-release isolation.
- Ticket/project API transport, color/key stability, optimistic move rollback, confirmed concurrent edit/create/delete preservation, and retryable failure feedback.
- Original move failure survives both tickets revalidation and rejected Project metadata refresh; a successful retry clears it.
- Candidate source tree matches the selected Child; no additional feature or dependency input is assembled.

## Verification plan and status
- Independent reviewer rejected the original `5d534c7` on Project metadata rejection, then passed the corrected source/test diff. Child focused tests: 2 passed (previous full suites were not repeated for review).
- Candidate checks: affected View/Main/store tests and type/lint; actual frontend/Laravel/temporary SQLite connections, including real Project metadata rejection. Then one Parent-scope React regression run as required by integration-v1.
- Laravel source is unchanged from the Epic/verified Child; execute relevant Ticket/Project contract tests rather than repeat the already-passed 136-test suite without cause.
- MySQL concurrency/row locks remain unverified. SQLite and request scheduling cannot establish those guarantees.
- Existing `.env`, DB, dirty/untracked, preview assets and prior verification evidence must remain untouched. Isolated temporary DB/storage/config and candidate-local dependency copies only.
- No Epic/main merge, public push or existing asset/branch/worktree deletion.

## Executed results and handoff
+- Candidate assembly SHA: `8d99e08d18620a8fc5c8ea590a4f68cb898cd678` (Epic base + selected Child, no conflict). Git tree comparison for `react`/`laravel` against `5c9c6e0` showed no differences. No integration source correction was needed.
+- Connection tests: View/Main/store 3 files / 48 tests passed. Laravel Ticket/Project contracts: 38 tests / 231 assertions passed (`BoardOrderTest`, `ProjectAccessTest`, `CsrfProtectionTest`, `ResourceContractTest`, `ProjectManagementTest`). The unchanged Laravel full suite was not repeated; its earlier Child result remains 136 tests / 638 assertions.
+- Actual candidate frontend → Laravel → fresh isolated SQLite verified eight prior contract scenarios once: detail actions and repeated assignee saves, same-column persisted order/reload, cross-column persisted status/release isolation, UI/server permission control, manual-status failure/retry, edit/delete failure/retry, failed-drag concurrent successful edit/create/delete preservation before deferred GET delivery, stale-board 409/revalidation/retry.
+- Additional focused real-network check passed: stale move returned 409, tickets revalidation succeeded, then an isolated fixture user suspension made Project metadata GET return a real 403. Original move guidance stayed visible and browser `pageerror` remained empty. Restoring the fixture user and logging in again via the real API allowed metadata recovery and a successful move; board guidance cleared. No API response was mocked.
+- The first eight browser scenarios passed in the initial candidate execution. The added ninth scenario was rerun alone after correcting a harness assertion that counted Next.js's shadow-DOM `__next-route-announcer__` (also `role=alert`) as board failure guidance. Final board-scoped assertion passed. Those failed harness attempts are retained and are not reported as product failures or passes.
+- Setup/check failures kept separate: a test launched before dependency copying finished could not find Vitest; after copying completed it passed. The first Laravel filter over-escaped namespace separators and selected zero tests; the corrected filter executed 38 tests successfully. Neither preliminary attempt counts as verification.
+- Final Parent-scope regression, executed once in this candidate per integration-v1: React 23 files / 145 tests passed. TypeScript, ESLint, changed source/test Prettier, production build and final diff checks passed. The full suite was not repeated during independent review.
+- Runtime evidence: `/private/tmp/ticket-detail-integration-check-20261011/summary.json`, `attempt-1-result.json` (first eight), `result.json` (final focused metadata boundary), `attempt-*-focused-result.json`, `check.cjs`, isolated bootstraps/config/storage, `browser.sqlite`, `laravel-tests.xml`, `final.png`. Existing Child evidence remains in its previous directory. Browser used Chrome `155.0.8059.39`; candidate APIs ran on 8128 and frontend on 3219. Both servers were stopped.
+- Candidate-local copies of locked dependency artifacts were used; candidate app code was loaded from this worktree. Existing environment/SQLite baseline hashes remained identical. Epic's existing untracked `ai/` and all prior workspaces/assets were untouched.
+- Remaining unverified: MySQL migration/concurrency/row locks, server canonical detail refresh/concurrent-edit conflict detection and keyboard drag. SQLite transactions and controlled request delivery do not establish MySQL concurrency guarantees.
+- Final candidate SHA is the commit containing this handoff (`git rev-parse HEAD`); app source remains the verified assembly SHA. Parent adoption is pending and belongs to the Parent. No Epic/main merge, push or cleanup was performed.
