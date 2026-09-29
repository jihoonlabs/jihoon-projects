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
