# Ticket Project Order Isolation Child

owner_repo: jihoonlabs/jihoon-projects
owner_branch: feature/ticket-project-order-isolation
role: child
status: validated-adoption-pending
parent_branch: feature/ticket
base_sha: 9269be437b16cfe9e2a9db55e1f7deec558d3faa

## Responsibility / Boundary
Project間でTicketのDnD楽観更新の順序を分離する。別Projectの同じ状態のTicketを並べ替えない。既存API・DB・権限・承認済みデザイン・Project色は変更しない。

## Validation / Handoff
- Application commit: `f8ad6e4513c272503b30c741382cd2032fe8f7d1`.
- Reproduced both regressions before the fix: a successful drag with failed refresh changed another Project's position, and a rejected drag left another Project's position changed.
- Restrict the optimistic target column to the moving Ticket's Project. Keep unrelated objects untouched, including during rollback and failed revalidation.
- React: 29 files / 210 tests passed, including 24 store tests. TypeScript, ESLint, changed TypeScript Prettier, production build and git diff check passed.
- Real browser / Laravel / MySQL integration was not executed for this Child. Store tests simulate deferred API responses and failures; they are not database verification.
- Application changes are limited to `react/src/features/tickets/store/useTicketStore.ts` and its existing test. No database, environment or backend files were changed.
- The reported local Epic `5af147b` is not available remotely or in this environment. The remote Epic starting point is the SHA above; this Child has not been adopted into either Epic.
- When the local adoption is available, compare the two application files and apply this application commit in an isolated integration candidate. Preserve the palette migration, seeded examples and local adoption records. Run relevant tests before Epic adoption.
- V1 remains pending actual user workflow confirmation. Keyboard DnD, OAuth and additional database configurations are outside this Child.
