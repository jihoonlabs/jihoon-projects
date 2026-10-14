# Ticket Delayed Drag Recovery Child

owner_repo: jihoonlabs/jihoon-projects
owner_branch: feature/ticket-delayed-drag-recovery
role: child
status: validated-adoption-pending
parent_branch: feature/ticket
base_sha: 9269be437b16cfe9e2a9db55e1f7deec558d3faa

## Responsibility / Boundary
Prevent delayed successful drag responses from clearing a newer Project list failure. Existing operations, API, permissions, palette and approved design remain unchanged.

## Validation / Handoff
- Application commit: `ff1fb5da5aa9e3c06f1b0d17ef2237d4893cdb05`.
- Reproduced two failing View regressions before the correction: a newer Project list error disappeared on delayed drag success, both with and without Project switching.
- Capture Project list request sequence and revision at drag start. Clear the drag error on success only when no newer list request or Project lifecycle change has occurred.
- Verified failure notice preservation and successful explicit list retry. Existing failed-drag notice and successful drag retry tests remain passing.
- React: 29 files / 210 tests passed; focused View: 38 tests passed. TypeScript, ESLint, changed TypeScript Prettier, production build and git diff check passed.
- Real browser/Laravel/MySQL integration is unverified for this Child. These are rendered React tests with simulated delayed API responses.
- Application boundary: `react/src/features/tickets/components/Board/View/index.tsx` and its existing View test.
- Separate sibling `feature/ticket-project-order-isolation` contains application commit `f8ad6e4513c272503b30c741382cd2032fe8f7d1`; it is not included here. The two fixes affect different application files.
- The reported local Epic `5af147b` is unavailable here. No Epic/main adoption, palette reconstruction or user DB/environment modification was performed.
- Next: compare with the actual local adoption and apply the application commits in an isolated integration candidate, then run related regression and connection checks before Epic adoption. Keep the local palette and its adoption record.
- V1 remains pending actual user workflow confirmation. No new features were added.
