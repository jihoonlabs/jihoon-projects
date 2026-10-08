# Project Leadership Child — WORK

## Responsibility
- Branch: `feature/ticket-project-leadership`, parent: `feature/ticket`.
- One leader per project, explicit transfer of leadership, independent ticket read/write permissions.
- Outside scope: project creation, archive/delete, project key search, React UI, and merge.

## Contract
- `POST /api/projects/{project}/members/{user}/transfer-leader` switches leadership to an existing member.
- Project leader or system administrator can transfer; non-leader cannot.
- Transfer uses a DB transaction and a project row lock. Prior leader becomes member; new leader becomes leader. The ticket read/write permission of each member is preserved.
- Regular member-add only accepts role `member`; member-update may edit permission but cannot change role; current leader cannot be removed before transfer.
- Missing target => 404. No or multiple leaders => 409. Membership mutations outside the transfer API do not share a project-level lock; verify concurrent behavior and adjust if needed.

## State and validation
- Remote code and tests committed; **execution tests not run**.
- Test `php artisan test --filter=ProjectManagementTest` and `vendor/bin/pint --test` on an existing Laravel environment; then related feature regression.
- Check initial creator leader from `feature/ticket-project-creation`, exactly one leader, old leader loses authority after handover, concurrent handover, admin behavior, direct promotion/demotion blocked, read/write preserved.
- Existing seeded/legacy projects without any leader may require a migration/reconciliation policy. Do not silently choose one.
- No merge into Epic without user approval.

## Handoff
- Inspect GitHub diff for this branch against `feature/ticket`; verify test results and document failures before proposing integration.
