# Ticket Recovery Integration Candidate

owner_repo: jihoonlabs/jihoon-projects
owner_branch: integration/ticket-recovery-20261014
role: integration
status: validated-local-adoption-comparison-pending
parent_branch: feature/ticket
base_sha: 9269be437b16cfe9e2a9db55e1f7deec558d3faa

## Responsibility / Boundary
Combine verified Ticket and account-entry recovery fixes. No new features, API, DB, palette, mail configuration or design changes. Preserve the approved original design; Jira is a workflow reference, not a visual template.

## Validation / Handoff
- Applications, in order: project order `f8ad6e4513c272503b30c741382cd2032fe8f7d1`, delayed drag `ff1fb5da5aa9e3c06f1b0d17ef2237d4893cdb05`, account entry `8ad9e165adf04fa4958773dbe79726a7c6b35fe7`.
- Boundaries passed after application: 24 store tests, 38 View tests, then 12 LoginForm tests.
- Final combined frontend: 29 files / 216 tests passed; TypeScript, ESLint, changed TypeScript Prettier, production build and git diff check passed.
- Fixes: project-scoped optimistic order, preservation of newer list errors on delayed drag success, and isolation of stale email resend responses from new email/login input.
- Real browser/Laravel/MySQL/SMTP connections were not executed for this candidate. Simulated HTTP/React tests are not actual database or mail delivery verification.
- The local Epic `5af147b` is not available remotely or here. This candidate excludes the local palette adoption/migration and does not replace the local Epic.
- Next: compare with that actual local adoption, integrate application commits in a candidate based on it, preserve palette/seed/data/permission contracts, then run regression and real connection checks before Epic adoption.
- Source Child branches and this candidate are retained. Epic/main adoption and cleanup were not performed.

## Minimum internal-use readiness
- Required workflow: account access/recovery, Project/membership setup, Ticket creation/assignment/priority/status/search, comments, completion and Project restore. Code exposure is not actual internal-use acceptance.
- Verification resend and password recovery exist. Checked-in mail default/example use `log`; actual mail delivery and new-account-to-first-Ticket flow remain unverified. Do not change user settings or weaken verification to bypass this check.
- Confirm separate-user permissions, persistence/reconnection and failure recovery in the target environment before V1 completion.
- Audit UI, keyboard DnD, external OAuth and additional database configurations are not automatically required or added.
