# Ticket Recovery Integration Candidate

owner_repo: jihoonlabs/jihoon-projects
owner_branch: integration/ticket-recovery-local-20261014
role: integration
status: local-verification-passed-target-acceptance-pending
parent_branch: feature/ticket
base_sha: 5af147b515bff8a2c85192e2009333968962d0c1
dependency_candidate_sha: 317115de91ed61781d467cd66da6b6f1a6e450a1

## Responsibility / Boundary
Combine verified recovery fixes and the requested login presentation correction. Jira is a workflow reference, not a visual template. Preserve the approved board design, authentication policy, APIs, database and user environment.

## Validation / Handoff
- Applied applications in order: project order `f8ad6e4513c272503b30c741382cd2032fe8f7d1`; delayed drag `ff1fb5da5aa9e3c06f1b0d17ef2237d4893cdb05`; account entry `8ad9e165adf04fa4958773dbe79726a7c6b35fe7`; save input `b8cfd8635df0975ffd1bfd2409286c4398a98b58`; login presentation `3b1343fb7ed7aac4ede45cfda099af37cf0c3a79`.
- Last two boundary checks: 17 Ticket detail tests, then 12 LoginForm tests. Login presentation merged without conflicts and existing resend-response guards remain present.
- Final combined frontend: 29 files / 218 tests passed; TypeScript via production build, ESLint, changed TSX/CSS Prettier, production build and git diff check passed.
- Changes: isolate Project optimistic order; retain newer list failures after delayed drag success; isolate stale verification resend responses; lock draft fields during Ticket submission while preserving failed drafts; align login controls with the approved board tone.
- Login Child production /login HTTP 200 and new heading/control groups were verified. Browser download failed; actual responsive visual acceptance remains unverified. Real Laravel/MySQL/SMTP connections were not executed for this candidate.
- Local review reported invalid Ticket version, missing Tickets and old design. The actual local API response, running backend source and migration state are unknown. Do not claim this update fixes that runtime mismatch or disable version validation.
- Remote candidate originally lacked local palette adoption `5af147b`; the local continuation now includes it.
- Original review snapshot `c511635` remains available by SHA. Epic/main adoption and source/branch cleanup have not been performed.
- Next: obtain the actual local source when accessible, compare/apply these applications in an isolated candidate based on it, verify frontend/backend/DB alignment and real internal workflow before Epic adoption.
- Finish cross-environment handoff with published branch HEAD and file/tree verification; a local commit alone is insufficient.

## Minimum internal-use readiness
Required flow: account access/recovery, Project/membership setup, Ticket creation/assignment/priority/status/search, comments, completion and Project restore. Existing code is not actual internal-use acceptance. Company mail delivery, new-account-to-first-Ticket, separate-user permissions and persistence/reconnection remain target-environment checks. No OAuth, audit UI, keyboard DnD or additional DB configuration was automatically added.

## Local continuation
- Local Parent includes the approved persistent palette; remote recovery candidate merged without conflict. No palette duplication or approved board CSS change.
- This WORK owns the local combined candidate. Remote checks above remain author/remote results, separate from new Mac results.
- Current: Mac React218/type/lint/build passed; new Login desktop/mobile/toggle, actual registration/403, real DTO version/palette checks passed against isolated MySQL. Save failure/retry, delayed drag/newer GET failure, signed verification/first Project/first Ticket also passed. Strict delivery checks subsequently reproduced two authentication failures: delayed initial GET401 and delayed verification POST200 replaced the new login cookie (next /me401). Earlier resend check removed interception before delivery and was insufficient. Both failures now pass after canceling obsolete initial authentication/resend requests before newer credentials are submitted. Reused only authentication restoration guards/tests from login Child `b0c2757`; no login style transplant. CSRF acquisition shares the resend cancellation signal. Real response delivery was held after Laravel completed it; browser cancellation and subsequent authenticated /me200/reload were verified. Original user DB authenticated runtime check still needs a fresh user login. Company SMTP delivery is not verified.
- Existing database/env and the other project worktree remain protected. No Epic adoption/push during validation. V1 remains user-acceptance pending.

## Local verification boundary (2026-10-14)
- Merge base: `5af147b515bff8a2c85192e2009333968962d0c1`; remote dependency: `317115de91ed61781d467cd66da6b6f1a6e450a1`; combined pre-fix commit: `7a027775cdb625a3a6a4e3f73e79c9447571098f`. This entry's commit is the final local verification reference.
- Final frontend: React 29 files / 222 tests, TypeScript, ESLint, changed-source Prettier, production webpack build and diff check passed. An initial parallel standalone type check raced build-generated .next types (TS6053); sequential check after build passed. No application type failure remained.
- Actual frontend -> Laravel -> isolated MySQL 8.4.11: registration/unverified-login rejection; signed verification/first Project/first Ticket; save409 input preservation/explicit retry201; delayed move200 preserving newer project-list500; initial auth401 and resend200 cancellation/session preservation; valid Ticket versions and persistent Project colors passed. Responsive login 1440/393/320px, password toggle and board screenshots captured. Links were not clicked in the layout check.
- Runtime: frontend `http://127.0.0.1:3280` from this candidate's production build; API `http://127.0.0.1:8180` from its Laravel; temporary `ticket_palette_review` database on dedicated local MySQL container. Original localhost3000/8000 and original SQLite/.env were preserved.
- Evidence (local only): `/private/tmp/ticket-recovery-local-check-20261014`, including flows-result.json, restore-race-result.json, cookie-resend-result.json and screenshots. Scripts may contain temporary test credentials and must not be published.
- Remaining: company SMTP delivery, original user's authenticated runtime after fresh login, full internal-use/visual acceptance, external OAuth and keyboard DnD. No new concurrent MySQL row-lock test was run for this recovery change; prior palette MySQL evidence remains separate. Independent review was not performed in this continuation. No Epic adoption/push; V1 is not complete.
