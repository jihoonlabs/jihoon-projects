# Ticket Acceptance Stabilization

owner_repo: jihoonlabs/jihoon-projects
owner_branch: feature/ticket-acceptance-v1
role: child
status: verified-awaiting-user-acceptance
parent_branch: feature/ticket
base_sha: 17a9447730ada87ea759766a3b03d7c0b9002e95

## Responsibility / Boundary
Provide one user-checkable snapshot of the adopted Ticket implementation and repair the confirmed same-Ticket write-queue failure. Preserve the approved design, API/version/permission contracts, original data and environment. Root entry uses the server `/login` redirect; the latest history correction then routes verified authenticated users to `/tickets`, while anonymous users remain at login. No broad optimization, unrelated branch adoption or Epic merge.

## Inherited result
All current adopted work is inherited from Parent. Recovery application: `4e9542be5d61f17b4b426c451b19e6f8b9d8bf4d`; palette adoption: `5af147b515bff8a2c85192e2009333968962d0c1`. Parent `TICKET.md` owns previous adoption/audit evidence. Prior 222 React tests and isolated API/MySQL results remain separate from checks executed here.

## Completion / Verification
- Reproduce the failed first drag dropping a later explicit queued action; repair queue continuation without retrying the first operation or bypassing board_version409.
- Related store tests, frontend checks and actual frontend/API queued-failure boundary.
- Publish this Child, start a clearly identified user-checkable runtime and report exact SHA.
- User acceptance remains pending. After technical checks, prepare `maintenance/ticket-child-cleanup-v1` at this verified snapshot as a reserved cleanup branch. Actual deletions remain gated on user acceptance and exact inventory/dependency checks. No cleanup implementation/worktree starts merely to reserve that ref. Preserve main/Epic, unpublished or unadopted code, dirty/untracked, active worktrees, DB/.env and required comparison refs. Recheck exact deletion SHA and dependencies before authorized deletion.

## Remaining limitations
Development Strict Effect duplicate GETs reproduced; production comparison has one GET per measured list/detail/comment action. Large-data load, company SMTP, original user's authenticated runtime, external OAuth, keyboard DnD and independent review remain unverified. No claim of V1 completion.

## Final local result (2026-10-15)
- Before fix, the new queued-failure regression failed with expected2/actual1 API calls. Queue now runs a later explicit operation on either resolution of its predecessor, while preserving separate rejection results. It never automatically retries the failed operation or changes server version rules.
- Full React 223 tests passed; after adding the further409 case, final store26 tests passed. TypeScript, ESLint, changed-source Prettier, production webpack build and diff check passed. Unchanged Laravel code/tests were not rerun.
- Real production frontend of this Child -> existing identical Laravel API8180 -> isolated MySQL: pointer drag with intentionally stale request board_version returned actual409; a second explicit pointer drag queued before delivery then returned actual200. Exactly2 PATCH requests, persisted IN_REVIEW after reload, no unintended detail dialog, pageerror0. No API response mock. Temporary acceptance Project29/Ticket11 are separate fixtures. Original DB/.env unchanged.
- Initial browser harness matched a drag animation overlay and failed its locator; after waiting for overlay completion, the actual application scenario passed. This was a harness failure, separate from the fixed queue bug.
- Runtime `http://127.0.0.1:3280` now uses this Child production build in `/private/tmp/ticket-acceptance-v1-worktree/react`; API8180 uses `/private/tmp/ticket-recovery-local-worktree/laravel`, whose Laravel tree is unchanged from this Child. Data target is dedicated temporary MySQL `ticket_palette_review` at127.0.0.1:33316. Test login details remain only in local protected fixture file `/private/tmp/ticket-recovery-local-check-20261014/audit-login.json`.
- Evidence: `/private/tmp/ticket-recovery-local-check-20261014/acceptance-queue-result.json` and `acceptance-queue.png`. This WORK's application commit is the validated Child SHA. Original legacy/unadopted branches were not silently merged. Epic remains unchanged; no branch/file/worktree deletion. User acceptance, V1 completion and cleanup execution remain pending.

## Root entry correction (2026-10-15)
- User opening the advertised root URL saw the Next.js starter screen. Root now uses the existing Next server redirect to `/login` (307), regardless of authentication state. Other routes and session policy are unchanged. Existing asset/CSS files were not deleted.
- Changed-page ESLint/Prettier and production build/type check passed. Real Chrome verified anonymous root→login, normal login→Tickets, authenticated root→login with subsequent /me200, starter content absent and pageerror0. No full suite repeat for this isolated route correction.
- Evidence: `/private/tmp/ticket-recovery-local-check-20261014/root-login-result.json` and `root-login.png`. Runtime3280 was rebuilt/restarted from this Child. Cleanup reserved branch remains at its prior checked snapshot; no deletion or Epic merge.

## Authentication history correction (2026-10-15)
- User reported login→Tickets→Back showing the login form, then Forward returning to Tickets. A retained valid session explains forward access; exposing the authenticated login form was the navigation defect.
- LoginForm now waits for initial session resolution and replaces its route with `/tickets` whenever authenticated. Successful login updates the auth store; this single guard owns replacement rather than a separate push. Valid-session visits to `/` or `/login` therefore finish at Tickets; this supersedes the prior authenticated-root-login expectation while preserving anonymous root→login and the existing server307.
- Regression tests cover pending-session form suppression, restored-session redirect without login inputs and successful login replacement; existing validation/failure/resend tests use an initialized anonymous state and replacement navigation. Full React29 files/226 tests, ESLint, changed-source Prettier, production build/type and diff check passed.
- Real production Chrome→Laravel→temporary MySQL: anonymous root→login; successful login replaces history (Back skips login; Forward opens Tickets); direct authenticated `/login` and `/` return to Tickets; reload preserves session; real logout followed by Back/Forward rejects protected history and Ticket API returns401. Exactly1 loginPOST/1 logoutPOST, pageerror0. Evidence: `/private/tmp/ticket-recovery-local-check-20261014/history-auth-result.json` and `history-auth.png`.
- Runtime3280 rebuilt/restarted from this Child. API/data unchanged. Cross-tab logout/server-expiry/BFCache variants beyond these tested navigation paths are not newly verified. No Epic merge, deletion or cleanup execution; user acceptance remains pending.

## Admin Project visibility inspection (2026-10-15)
- Application inspected: `53a96ec29fec64f2658bb7a57b016f26162bbaa3`. User expected an aggregate admin board and interpreted General as an all-project view. No source/API/data change was made in this inspection.
- Actual admin frontend→Laravel→isolated MySQL: active Project API12 IDs and archived API3 IDs exactly match all15 database Projects; Ticket API9 IDs exactly match all9 database Tickets. Selector contains all12 active Projects. Archived scope is separate by existing contract.
- General is a normal Project(id1), not an aggregate sentinel. DB count0/API count0/visible cards0 match. Another populated Project(id2) has DB2/visible2. Board intentionally filters all fetched Tickets by selectedProjectId and defaults to the first returned Project; aggregate view is currently absent.
- The two members rows seen during Project switching represent different URLs: initial `/api/projects/28/members` and selected General `/api/projects/1/members`; one request per selection. A follow-up Project2 selection requested `/api/projects/2/members` once. No duplicate same-scope GET was reproduced in production.
- Evidence: local `admin-project-expected.json`, `admin-project-audit-result.json`, `admin-project-audit.png` under `/private/tmp/ticket-recovery-local-check-20261014`. Real GET/DB reads only; existing data and permissions preserved. Broader API correctness/large-data performance is not implied by this targeted result.
- Next UX decision pending: offer an explicit admin all-project default while retaining General as a normal Project. Proposed aggregate scope is view/detail, with Project selection required for editing/DnD; never use a single Project's permissions or board_version for mixed Projects. No aggregate implementation before user choice. Cleanup/user acceptance remain pending.
