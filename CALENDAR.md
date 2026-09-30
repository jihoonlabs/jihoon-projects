# Calendar / Schedule MVP

## Goal

Add a personal calendar and schedule feature for authenticated users.

This Epic is independent from Ticket and Attendance. Existing authentication and CSRF handling must be reused.

## MVP scope

- Show a monthly calendar.
- Show the signed-in user's schedules on the calendar.
- Select a date and create a schedule.
- Edit an existing schedule.
- Delete an existing schedule.
- A schedule contains:
  - title
  - start date/time
  - end date/time
  - optional memo
- Users can access only their own schedules.

## Rules

- Store schedule timestamps in UTC.
- Display schedule timestamps in Asia/Tokyo.
- End time must be later than start time.
- Authorization and ownership checks are enforced on the server.
- Frontend restrictions are for UX only and do not replace server-side authorization.
- Reuse Laravel Sanctum SPA authentication and the existing frontend CSRF request flow.
- Keep Calendar/Schedule independent from Attendance in the MVP.

## Out of scope

- Shared calendars
- Invitations or attendees
- Recurring schedules
- Notifications
- Drag-and-drop rescheduling
- Attendance integration
- Admin schedule management

## Planned implementation order

1. Define the Calendar/Schedule MVP and domain rules.
2. Add the schedule database model and migration.
3. Add authenticated schedule APIs and ownership tests.
4. Add the monthly calendar UI.
5. Add create/edit/delete UI and tests.
6. Verify the complete flow in a real browser.

## Branch

`feature/calendar`


## Verification handoff

The Calendar branch is being implemented through GitHub remote changes. Checks that require a local runtime must be completed later on the development Mac.

### Completed remotely

- Calendar/Schedule MVP scope documented.
- Schedule model and database migration added.
- User-to-schedules Eloquent relation added.
- Authenticated schedule CRUD routes and controller added.
- Ownership and validation feature tests added.
- `/api/schedules` route registration added.

### Pending local verification

Run these checks before treating the API step as complete:

1. Run the Laravel Schedule feature tests.
2. Run the full Laravel test suite.
3. Run Laravel Pint / formatting checks.
4. Run migrations from a clean test database and confirm the `schedules` table is created correctly.
5. Verify authenticated API requests with the existing Sanctum session/CSRF flow.
6. Confirm create, monthly-range list, update, delete, validation failure, and cross-user access behavior in the real application.

If any check fails, fix it on `feature/calendar` before continuing browser-level verification.

### Company-side review

When only code review is possible, inspect these files first:

- `laravel/app/Http/Controllers/ScheduleController.php`
- `laravel/routes/api/schedules.php`
- `laravel/tests/Feature/ScheduleTest.php`
- `laravel/database/migrations/2026_09_30_000000_create_schedules_table.php`

Review points:

- Schedule ownership is always derived from the authenticated user.
- Another user's schedule returns 404 for update/delete.
- `ends_at` must be later than `starts_at`.
- Monthly-range queries include schedules overlapping the requested range.
- UTC storage and Asia/Tokyo display responsibilities remain separated.
