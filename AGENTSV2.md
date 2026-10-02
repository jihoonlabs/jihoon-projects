# 🤖 AGENTS.md (System Operating Rules)

## 1. Context & Scope Control
* **Primary Context:** Work ONLY with `AGENTS.md` and the single current branch-dedicated document (`docs/<feature>/...`).
* **Isolation:** DO NOT include parent Epics, sibling Childs, or other feature MDs in the context automatically.
* **Style Learning:** Infer code style and conventions from existing code in the repository. Do not waste context on standard formatting rules.

## 2. Pre-Execution Verification
* **Check Environment First:** Inspect current branch, `git status`, feature MD, and actual codebase before editing.
* **Abort Conditions:**
  * If the current branch does not match the target scope, STOP and report.
  * If there is an unresolved discrepancy between docs and codebase, STOP and report.

## 3. Execution & Approval Guardrails (HITL)
* **Pre-Change Summary:** Briefly explain WHAT will be changed and WHY before writing code.
* **Autonomous Scope:** Proceed autonomously for confirmed plans, refactoring, tests, and clear bug fixes.
* **Approval Required:** STOP and request user approval with options and impacts before making structural changes (New architecture, new UX, design changes, or scope shifts).
* **Minimal Scope:** Implement minimal necessary changes. Avoid unnecessary abstractions or adding new dependencies.

## 4. Testing & Quality Assurance
* **Verification Loop:** Run relevant tests, type checks, and Linter immediately after implementation.
* **Failure Handling:** If verification fails, analyze, fix, and re-verify. If blocked by external constraints, STOP and report.
* **Strict Honesty:** NEVER document or report untested code as verified, or incomplete features as completed.

## 5. Git & Branch Management
* **Branch Structure:** Strictly follow `main → Epic → Child`.
  * Merge Child into Epic only after implementation and verification are complete.
  * Merge Epic into main only after full integration testing.
* **No Unauthorized Git Actions:** NEVER create branches, merge, commit, or push beyond the explicit work scope.
* **State Protection:** NEVER delete, overwrite, or `git reset` existing uncommitted changes or untracked files. If conflicts occur, STOP and report.

## 6. Documentation & Summarization
* **Doc Placement:** Feature MDs reside under `docs/<feature>/`. Each Epic and Child has exactly ONE dedicated MD.
* **Upstream Sync:** Upon Child completion, summarize ONLY finalized outcomes into the Epic MD. DO NOT pass detailed work logs to the next Child.
* **Comments & Language:**
  * Leave concise comments ONLY for non-intuitive business rules or complex logic.
  * DO NOT introduce new Korean text in developer comments or documentation within the Web Portfolio.
  * Keep existing English as-is; write natural Japanese for required documentation.