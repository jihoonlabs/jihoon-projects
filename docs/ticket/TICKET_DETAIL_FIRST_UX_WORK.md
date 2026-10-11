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

## Current state
- Session checkpoint: worktree `/private/tmp/ticket-detail-first-ux-worktree`, branch `feature/ticket-detail-first-ux`, implementation commit `884fccd3fb9c54b50cb17438dee5c5f6367956dc`. At checkpoint the worktree was clean and HEAD matched this commit. No code changes are pending; this document is being updated to record session handoff state.
- Implemented card-title/detail-button entry, detail-local edit and confirmed delete, editable detail fields, save/delete error handling, focus entry and return, and card/modal visual hierarchy using the existing project border color. The title-region project background remains unapplied.
- Reapplied the `ed3cfa4` drag-failure rollback protection against concurrent successful same-project edits, creations, and deletions; failed deletion is rethrown after rollback so the detail dialog can report the failure. Manual status failures are caught and surfaced for retry.
- Directly executed in this Child: React `pnpm test:run` (23 files, 141 tests passed), `pnpm exec tsc --noEmit` (passed), `pnpm lint` (passed), Prettier check for changed source/tests (passed), `git diff --check` (passed), and `pnpm build` (passed after sandbox network denial was resolved by approved network execution). No Laravel files changed, so Laravel tests/Pint were not run.
- Independent review was completed. It confirmed the detail controls stop pointer/key event propagation and keyboard detail entry is covered. It also found the current drag regression test invokes a mocked `onDragEnd` rather than performing a real pointer drag/release. Therefore actual pointer drag-release behavior remains unverified. Existing board configuration uses only `PointerSensor`; keyboard detail entry is verified, while keyboard drag-and-drop was not part of the prior setup and was not added here.
- Actual application browser verification was not run: the Child has no Playwright executable and Laravel dependencies (`laravel/vendor`) are absent, so an isolated full-stack browser session could not be started without expanding the environment setup. The installed Chrome binary alone was insufficient. MySQL concurrency/row-lock validation remains out of scope and unrun.
- Ticket V1 is not complete. Remaining follow-up includes real browser verification of pointer drag followed by release, and separately the existing Epic limitations around refreshing detail data and detecting edit conflicts.
- Process check: targeted process listing found no running Next.js, Laravel, or Playwright process for this Child; only the inspection command itself matched. The earlier `pgrep` attempt failed because the macOS `sysmond` service was unavailable.
- Next task: in this Child, add/execute a real pointer drag-and-release regression check (and full-stack browser validation if an isolated Laravel/Playwright environment is available), then update this WORK with direct results. Do not start color persistence, detail refresh/conflict detection, or Epic integration in this step.
