# Ticket deletion evidence — home Codex handoff

A user with `write` access may delete a ticket, but the database now stores the ticket identifier, project key, title, description, status and who deleted it in a separate audit table. The deletion and the evidence record are written in one transaction. A `read` member still cannot delete tickets.

Branch: `feature/ticket-audit-history`. Only ticket **deletion** history is implemented so far; this does not implement a history screen or project deletion. No runtime tests have run, and the Child has not been merged.

For verification and integration caveats, read `TICKET_AUDIT_WORK.md`. In particular, preserve archived-project write guards from the separate lifecycle Child and do not conflate an audit log with backup or tamper-proof archival.
