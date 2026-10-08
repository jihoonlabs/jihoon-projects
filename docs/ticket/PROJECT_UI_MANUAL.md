# Ticket project creation UI — review handoff

**New visible feature:** On the Ticket board, press **+ プロジェクト作成**, enter a name, and submit. On success the new project becomes selected; the project selector displays the generated three-letter key next to each name. Search projects by name or key.

Branch: `feature/ticket-project-ui`. Remote code and focused tests have been committed; no merge and no runtime test. The ordinary-user create flow requires the separate `feature/ticket-project-creation` backend Child, which is also not yet integrated.

Home Codex: review `PROJECT_UI_WORK.md` and test the complete creation → selection → ticket flow after verifying the backend Child. This is real new UI code, not a claim that Epic already provides the feature.
