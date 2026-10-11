# Ticket 詳細中心 UX WORK

## Ownership と基準
- Repository: `jihoonlabs/jihoon-projects`
- Child branch: `feature/ticket-detail-first-ux`
- Worktree: `/private/tmp/ticket-detail-first-ux-worktree`
- Epic base SHA: `fdccd96faa20bf9e5f424bd8ae47b1756b2978b6`
- Implementation base SHA: `fdccd96faa20bf9e5f424bd8ae47b1756b2978b6`
- Prior verified fix: `ed3cfa4ec5586f4734ca6a78d566ce07617681c1` exists only on local `ticket-preview`; it is not adopted by the Epic or public remote. Its relevant contracts are preserving concurrent successful edits/creations/deletions when a drag fails, and handling a rejected manual status update. Reapply and test these against the current Epic code; do not cherry-pick the old commit wholesale.
- `agent-guard` is unavailable in PATH and `bin/agent-guard` is absent. Ownership was checked manually: branch, worktree, base SHA, and this Child WORK agree.

## Responsibility
- Open Ticket detail from the card title or a detail action.
- Place edit and delete actions inside detail; remove direct edit/delete actions from cards.
- Keep a drag release from being interpreted as a detail click.
- Improve spacing, hierarchy, readability, and focus using existing UI patterns and project colors.
- Preserve keyboard access and existing role-based permissions.

## Out of scope
- Persisting project colors or changing duplicate-color policy.
- Applying a pale project-color background to the title region; this remains a design candidate.
- Refreshing detail from the latest server data or detecting concurrent edit conflicts.
- MySQL setup or row-lock validation.
- Epic/main changes, merge, and public push.

## Completion and verification
- Verify detail entry by pointer and keyboard, detail-local edit/delete, and read/write permission behavior.
- Verify drag activation does not open detail, including pointer release after an actual drag.
- Reproduce the prior drag rollback race with concurrent same-project edit/create/delete and verify confirmed writes survive; verify manual status failure is handled and retryable.
- Run affected React tests, the complete React test suite, TypeScript, ESLint, and production build. Run browser checks in an isolated environment when available.
- Request an independent review of click/drag boundaries. If unavailable, record it as unverified.
- Update this WORK and a concise user-facing MANUAL with only directly executed checks, remaining limitations, and the resulting Child SHA.

## Previous session verification (before this continuation)
- Session checkpoint: worktree `/private/tmp/ticket-detail-first-ux-worktree`, branch `feature/ticket-detail-first-ux`, implementation commit `884fccd3fb9c54b50cb17438dee5c5f6367956dc`. At checkpoint the worktree was clean and HEAD matched this commit. No code changes are pending; this document is being updated to record session handoff state.
- Implemented card-title/detail-button entry, detail-local edit and confirmed delete, editable detail fields, save/delete error handling, focus entry and return, and card/modal visual hierarchy using the existing project border color. The title-region project background remains unapplied.
- Reapplied the `ed3cfa4` drag-failure rollback protection against concurrent successful same-project edits, creations, and deletions; failed deletion is rethrown after rollback so the detail dialog can report the failure. Manual status failures are caught and surfaced for retry.
- Directly executed in this Child: React `pnpm test:run` (23 files, 141 tests passed), `pnpm exec tsc --noEmit` (passed), `pnpm lint` (passed), Prettier check for changed source/tests (passed), `git diff --check` (passed), and `pnpm build` (passed after sandbox network denial was resolved by approved network execution). No Laravel files changed, so Laravel tests/Pint were not run.
- Independent review was completed. It confirmed the detail controls stop pointer/key event propagation and keyboard detail entry is covered. It also found the current drag regression test invokes a mocked `onDragEnd` rather than performing a real pointer drag/release. Therefore actual pointer drag-release behavior remains unverified. Existing board configuration uses only `PointerSensor`; keyboard detail entry is verified, while keyboard drag-and-drop was not part of the prior setup and was not added here.
- Actual application browser verification was not run: the Child has no Playwright executable and Laravel dependencies (`laravel/vendor`) are absent, so an isolated full-stack browser session could not be started without expanding the environment setup. The installed Chrome binary alone was insufficient. MySQL concurrency/row-lock validation remains out of scope and unrun.
- Ticket V1 is not complete. Remaining follow-up includes real browser verification of pointer drag followed by release, and separately the existing Epic limitations around refreshing detail data and detecting edit conflicts.
- Process check: targeted process listing found no running Next.js, Laravel, or Playwright process for this Child; only the inspection command itself matched. The earlier `pgrep` attempt failed because the macOS `sysmond` service was unavailable.
- Next task: in this Child, add/execute a real pointer drag-and-release regression check (and full-stack browser validation if an isolated Laravel/Playwright environment is available), then update this WORK with direct results. Do not start color persistence, detail refresh/conflict detection, or Epic integration in this step.

## Continuation verification — 2026-10-11
- Start: branch `feature/ticket-detail-first-ux`, HEAD `590d8b37b059f2fd2b3e8e85d4d4f98d5530bff9`, clean worktree. Ownership/base were manually checked; no new branch/worktree was created.
- Loaded GitHub private `main` rules and Epic WORK before local inspection. Epic WORK was used only for routing; this Child WORK owns the task. Internal main snapshot: `b6780322e9b1f81f7f5dd4d9b1aed15bba678557`.
- New independent read-only review of the starting HEAD found one regression: consecutive edits in the same detail compared assignee changes with the original ticket, omitting a request to restore the original assignee. Fixed comparison against the last successful saved values; added assigned → other → assigned and unassigned → other → unassigned regressions. Independent re-review found the fix/test appropriate and no additional blocker.
- Directly executed after the fix: affected View tests 20 passed; complete React suite 23 files / 143 tests passed; TypeScript and ESLint passed. Production build passed after the sandbox Google Fonts network failure was retried with approved network access. Changed source/tests Prettier and final diff checks passed.
- Real Chrome `155.0.8059.39` against this Child's rebuilt production frontend at `127.0.0.1:3217` passed: pointer title/detail entry, Space entry and focus return, actual PointerSensor activation (dragging opacity observed), release over the original title without opening detail, cross-column DONE drag with the actual move request/response and no detail opening, consecutive assignee saves, failed save/retry, read-only detail, and cancelled/confirmed deletion.
- Browser API responses were intercepted with isolated fixtures. No Laravel server or database was used; existing `.env`, DB, preview assets, prior verification documents and branches were untouched. This verifies real frontend pointer behavior, not server authorization, persistence, or full-stack integration.
- Browser evidence: `/private/tmp/ticket-detail-first-ux-browser-20261011/check.cjs`, `result.json`, `detail.png`. Initial harness runs failed on overlay/hidden-option locator ambiguity and optimistic-state timing; the completed run waited for the real move response and used dialog-scoped controls. These harness failures were not counted as passes.
- Remaining unverified/out of scope: Laravel/full-stack browser integration, MySQL concurrency/row locks, detail refresh and concurrent-edit conflict detection. Keyboard drag remains absent from the existing PointerSensor-only setup. Ticket V1 as a whole remains incomplete.
- Handoff: implementation plus the directly necessary assignee regression fix are ready for Parent evaluation; no push or Epic/main merge was performed. The resulting Child SHA is the commit containing this section (resolve with `git rev-parse HEAD`); Parent retains adoption ownership.

## Full-stack continuation — 2026-10-11
- Start: branch `feature/ticket-detail-first-ux`, HEAD `03eae7a0acbf9adab264f787b3004c8a6f848adc`, clean worktree. Latest private main rules and this Child WORK were loaded before execution; ownership remains this Child. No new branch/worktree was created.
- Authorized verification scope now includes actual frontend → Laravel → an isolated temporary SQLite DB. MySQL concurrency/row-lock validation and Epic/main adoption remain outside this Child.
- Environment: PHP 8.5.5 with `pdo_sqlite`; locked Composer dependencies installed with `--no-scripts` (no setup/key-generation/migration script against existing configuration). The initial sandbox download failed on DNS/network access; approved network installation completed.
- Isolation: `/private/tmp/ticket-detail-fullstack-20261011/browser.sqlite`, separate storage/session/log/view/cache paths, fresh ephemeral APP_KEY, explicit SQLite configuration and cleared DB_URL. The browser Laravel bootstrap used a separate empty environment file, not an existing `.env`. Migration and fixture creation targeted only this DB. Frontend used process-local `NEXT_PUBLIC_API_URL=http://127.0.0.1:8127` at `127.0.0.1:3218`; `.env` files were not edited. The baseline hashes of existing Child environment/SQLite files remained identical. Existing preview/feature-ticket workspaces, DBs and verification artifacts were not modified or deleted.
- Browser: real Chrome `155.0.8059.39`, real Laravel login/session/CSRF/CORS, no API response mocks. Eight scenarios passed: title/detail entry and detail editing; assignee changes and repeated saves persisted in DB; same-column reorder and reload order; cross-column status persistence and release over the title without detail opening; reader/outsider/admin UI plus real forbidden write/read responses; manual-status 403 rollback/retry; edit/delete 403 error retention and retry/cancel/confirmed deletion; failed drag retaining concurrent successful same-project edits/creations/deletions; stale-board 409 revalidation/retry (the last two belong to the failure-recovery checks).
- Rollback evidence: only delivery of real move/GET requests was paused using Playwright `route.continue`; no responses were replaced. Successful edit/create/delete requests committed to Laravel/SQLite while the move was pending. Permission revocation made Laravel return 403. Before allowing the deferred GET, the frontend still contained the successful edit/create, excluded the deleted ticket, and restored the dragged status. These invariants also held after revalidation/reload. This avoids counting a later server refresh as proof of local rollback protection.
- Executed failure found and fixed: successful concurrent writes scheduled a deferred GET that cleared the store's drag error. The real failed move therefore became invisible. View now retains the rejected move reason after refreshing project metadata and clears it on a successful retry. Added a regression test that exercises a pending move, concurrent creation, deferred revalidation and retry. The same full-stack scenario passed after the fix.
- Laravel tests: first executed run failed 11/136 because browser-specific FRONTEND_URL/stateful-domain overrides conflicted with test assumptions (redirect URL, session/CSRF). Separating test-only defaults while retaining isolated storage and in-memory SQLite resolved this; final result 136 tests / 638 assertions passed. These initial executed failures are distinct from the dependency/network setup failure.
- Harness-only executed failures: a TODO heading locator used the status instead of its Japanese column label; an admin started in General rather than the verification project. Both were corrected and their failed attempts were retained. Neither was a product defect. Final complete run: all eight scenarios passed, zero failed; real HTTP evidence includes 201 creation, nine 403 responses, and one 409 response.
- After the source fix, directly executed: affected View tests 21 passed; complete React suite 23 files / 144 tests passed; TypeScript, ESLint, changed source/test Prettier, production build and final diff checks passed. Laravel source was unchanged, so Pint was not required. Laravel full suite was directly executed in this continuation, not inherited from a previous report.
- Evidence retained outside Git: `/private/tmp/ticket-detail-fullstack-20261011/check.cjs`, `run.py`, bootstrap scripts, `fixtures.json`, `browser.sqlite`, `initial.sqlite`, `result.json`, `attempt-*-result*.json`, `laravel-tests.xml`, `final.png`, and prior failure screenshots. Started frontend/Laravel processes were stopped after verification.
- No requested SQLite/browser/Laravel-test item remains blocked by environment setup. MySQL concurrency/row locks are unverified; request scheduling in Chrome plus SQLite does not establish those guarantees. Detail refresh/canonical server values/concurrent-edit conflict detection and keyboard drag remain existing scope limitations. Ticket V1 overall completion/adoption belongs to the Parent.
- Handoff: the final verified Child SHA is the commit containing this section (`git rev-parse HEAD`). No push, Epic/main merge, existing asset deletion or other workspace mutation was performed.

## Independent final-error review — 2026-10-11
- Independent read-only test review of `5d534c7cdf201778c27e98006938248e478b3a0b` found a blocking boundary: a rejected Project metadata refresh prevented the original move error from being displayed and left the async drag handler rejected. Tickets revalidation and Project metadata refresh are distinct boundaries.
- Child fix: show the original move error before refreshing Project metadata; explicitly handle metadata refresh rejection while retaining that error. A successful drag retry still clears the message.
- Focused verification only: the parameterized failed-drag/deferred-tickets-GET/concurrent-create test passed with both successful and rejected Project metadata refresh (2 passed, 20 skipped). It checks visible error, confirmed creation preservation, no runner-reported unhandled rejection, and message clearance on successful retry. No previous full suite was repeated for this review.
- Independent re-review of the final source/test diff passed with no additional blocker. This was a separate reviewer, not self-review; the reviewer did not repeat tests. Existing store edit/delete regressions and real-Laravel evidence remain previous-session evidence.
- Handoff: apply this corrected Child tip, which contains `5d534c7`, only after candidate ownership/base checks. The exact selected SHA belongs in the candidate WORK. The original `5d534c7` alone did not pass this final review.
- MySQL concurrency/row locks remain unverified. Real-network Project metadata GET rejection is not established by the focused unit tests; validate that connection in the integration candidate if available.
