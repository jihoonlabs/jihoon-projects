# Ticket Project Discovery API Child — WORK

## Responsibility
- Parent: `feature/ticket`; Child: `feature/ticket-project-discovery-api`.
- Provide membership-scoped project search by public three-letter `project_key` prefix or project name substring, and an exact key lookup endpoint.
- Keep numeric `id` based existing route contracts unchanged. UI, leader transfer, archive, delete and project creation are separate Children.

## API
- `GET /api/projects?search=ABC`: optional `search` string (max 255 chars). Project key is searched as uppercase prefix and project name as substring. Empty input lists accessible projects.
- `GET /api/projects/by-key/ABC`: exact, case-insensitive key lookup. Requires existing Sanctum + active.user middleware. Members can view their own projects; admins can view all. Valid but inaccessible key returns 403, invalid/missing key returns 404.
- Responses keep existing `ProjectResource` data including `id`, `name`, `project_key` and `board_version`.

## Implementation
- API controller commit: `c358636acb179ba0c74709f0f085f534bf5aeb43`.
- Route commit: `ebaef9663c92246c488ad732d4cc4bb74b92fc33`.
- Regression test commit: `bb12f9c6e1168bafcf6dd1e218edb87f053e0f3b`.

## Verification gate
- **Not yet executed** in remote GitHub-only environment. Run `php artisan test --filter=ProjectManagementTest`, `vendor/bin/pint --test`, and related Ticket feature tests where dependencies already exist.
- Check member key search/name search, hidden-project non-disclosure in listings, exact-key read authorization, admin access, malformed search validation, existing numeric routes, guest and inactive user middleware.
- Static caveat: database LIKE case-sensitivity can vary by SQL engine/collation, especially name search; check MySQL in integration. Search is not a global directory and should never reveal names outside membership.
- Parent must adopt a tested Child SHA and execute UI/API integration regression before merge.
