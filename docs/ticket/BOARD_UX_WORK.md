# Ticket Board UX

owner_repo: jihoonlabs/jihoon-projects
owner_branch: feature/ticket-board-ux
role: child
base_sha: cd6ada3aafdcdd6d2e561e1180880e44a77be271
implementation_base_sha: b0c2757e52c50de2644b36f30aa810e48be10ad3
dependency_sha: b0c2757e52c50de2644b36f30aa810e48be10ad3
status: ready_for_test_review

## Responsibility

Apply the approved board UX changes: full-card project tint, title-only detail entry, readable comment controls, accessible long-detail scrolling and persistent detail actions, and signed-in user/logout access. Preserve authentication, membership, comments, detail freshness/version conflict and DnD recovery contracts.

## Basis and implementation

- Parent is the adopted Ticket Epic. Implementation starts at the verified Login UI Child, an explicit dependency, to retain its authentication fixes and failed-logout behavior. This is not Epic adoption of that Child. No suitable ongoing UX Child was identified in the Mac handoff; this Child owns the changes below.
- Reuse the existing immutable project-key hue for a pale 94% lightness card background. Border colors keep their existing contract. Card priority/status/assignee cues remain independent. The drag overlay uses the same background; its title action is disabled.
- Remove the duplicate detail button and unused styles. The title remains a native keyboard-accessible button; existing DnD event boundaries and post-drag suppression are retained. Existing behavior tests now use the title action.
- Add a local CSS Module for comments: stacked labeled input, readable multiline content, consistent action sizes and error presentation. Existing author/admin rules and API calls are unchanged.
- Keep the detail heading and bottom close/edit/delete actions outside the scrolling body. The complete long description remains available in a bounded keyboard-focusable region. Editing retains its existing save/cancel and conflict flow.
- Mount the existing shared account Header in the Board header using a compact presentation. Do not create a second logout implementation. Failed logout retains authentication and provides retry; loading and synchronous duplicate-submit guards are preserved. Add responsive wrapping and focus styling.
- No backend/schema/dependency changes, database writes, global seeding or existing asset deletion.

## Verification

- Here, in the assistant's isolated checkout: final full React suite 25 files / 184 tests passed. TypeScript, changed TS/TSX ESLint and production build passed. Changed source files were formatted with the existing Prettier configuration; final diff whitespace check passed.
- Reuse the failed-logout/retry regression against the actual mounted Board Header. Card test verifies the retained cues and removal of the redundant action. Freshness/conflict, comments/permissions, project filtering, DnD rollback and dashboard guard regression suites pass.
- Mac Codex independently reviewed revision 77203006643b8e73d336e1680be54dedaaf2f45f with actual isolated frontend/Laravel/SQLite: project/color separation, title access, mobile detail, comment CRUD/permissions/error input preservation, logout/auth boundaries, freshness/conflict, assignee and pointer DnD recovery passed. Three P2 blockers remained: newer comment draft erased by earlier send completion; delayed initial GET replacing successful comments; Tab escaping the modal.
- Reproduced the draft loss, stale list overwriting a new edited comment, stale list resurrecting a deleted comment and modal Tab escape in four focused author regressions before fixing them. All four pass after correction; focused comment/detail suite: 25 tests passed.
- Sending captures the draft revision and only clears unchanged input. A temporary mutation journal overlays successful create/edit/delete results on the delayed initial list, then clears. Comment state is keyed by Ticket ID. The dialog boundary contains Tab/Shift+Tab during loading, detail and edit, includes focusable description/comments and ignores disabled/hidden controls. Existing return-to-trigger handling is preserved.
- The 184-test run, type/lint/build and regression fixes are author checks. Mac actual-API reproduction and independent re-review of these fixes remain pending. The assistant did not access the Mac database.

## Mac Codex handoff

Verify the exact updated Child commit, ownership and dependency before testing. Prioritize the three independent P2 blockers with real delayed requests; also check edited/deleted comments are not replaced/resurrected by delayed initial GET, successful unchanged input clears, and Tab/Shift+Tab stay inside loading/error/detail/edit dialogs with disabled controls and return focus on close. Do not repeat unrelated passed scenarios without a changed boundary or new uncertainty. Review the authentication/logout attachment and modal keyboard/scroll boundaries independently. Run actual frontend-to-Laravel scenarios with isolated temporary data: title entry; no duplicate detail button; long description/comment readability; visible close/edit/delete at desktop and narrow mobile sizes; comment create/edit/delete/error input preservation and author/admin permissions; logout success/failure/retry, reload and protected-route back navigation; latest detail/edit conflict; assignee and pointer DnD recovery. Preserve ai/, env and the existing database.

For user preview, retain Login UI plus this Child together. Use isolated UX projects with distinct keys to check project switching/data isolation and card colors; do not grant access to unrelated existing projects or rewrite their data. Include at least two project colors in preview evidence. Clearly label the running branch/SHA and API/data target so preview cannot silently revert to Epic.

The implementation dependency is already contained in this Child's history. In a later isolated integration candidate, apply Login UI then only this Child's commits after implementation_base_sha; do not reapply dependency changes. Epic adoption, main merge, publishing and destructive cleanup remain separately scoped.

## Remaining boundaries

Independent re-review and Mac actual-API verification of the three P2 fixes are pending; Epic adoption remains blocked until those pass. Color persistence and exact duplicate-color rejection are a separate unfinished responsibility; the existing hue algorithm can collide and this change does not claim uniqueness. Similar colors remain allowed. Full project-management UI adoption, external Google/LINE completion and MySQL concurrency/row locks are not verified by this Child. Ticket V1 is not declared complete.

## Improvement note

- Problem: user preview ran the Epic frontend after a completed Login UI Child, so the UI appeared to revert.
- Evidence: Mac diagnosis identified the old 3000 frontend; switching it to the Login UI Child restored its changes.
- Suggested fix: include frontend branch/SHA and API/data target in each preview handoff and verify the combined preview before user testing.
