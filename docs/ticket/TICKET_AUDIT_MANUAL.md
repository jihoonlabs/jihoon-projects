# Ticket work history — home Codex handoff

**New capability in this Child:** Ticket creation, edits, Kanban moves and deletion each produce an audit event with project key, ticket key, actor, timestamp and the ticket state. Deleting a ticket retains the final title and details after the live record is gone. Audit writes and the corresponding ticket mutations share database transactions.

**Existing access model remains:** project `write` members may mutate tickets, `read` members cannot. The audit history is not publicly exposed by API or UI yet, avoiding unintended disclosure of historic descriptions.

Branch: `feature/ticket-audit-history`. Commits pushed remotely; **runtime tests NOT RUN, no merge**.

Codex: read `TICKET_AUDIT_WORK.md`, run the focused tests and relevant ticket regressions, and reconcile `TicketController` with archived-project guards from `feature/ticket-project-lifecycle-api` before proposing an Epic merge. The audit table is not a backup or tamper-proof journal.

Still outstanding: comment and project lifecycle audit events, secure audit reader, project creator, deleted-project tombstones and irreversible delete policy.
