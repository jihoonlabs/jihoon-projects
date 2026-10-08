# Project archive and restore — review handoff

The Ticket project lifecycle Child now introduces **archive** (default hide) and **restore**. Archiving requires all tickets to be DONE, keeps the three-letter project key and historical tickets, and moves the project into a separate archived list. It is available to the current project leader or a system administrator. Archived projects remain readable; ticket and comment edits are blocked.

**This does not implement irreversible deletion.** Deletion with completed tickets needs a separate guarded design, including creator ownership, dependent records and key reuse.

Branch: `feature/ticket-project-lifecycle-api`. Changes are remotely committed only, **not merged or runtime-tested**. Home Codex: read `PROJECT_LIFECYCLE_WORK.md`, run focused Laravel tests and migrations, fix discovered issues in this Child and only propose integration when verified.
