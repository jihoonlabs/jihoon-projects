# Design generation recovery

Branch: `backup/ollama-design-recovery-20261009`
Base: `b79093884983f99facd2c586c54f4618c0e13a62` from `feature/personal-game-ai-thumby-rpg-api`.

## Scope and contract

First bounded improvement after the local RPG design session repeatedly hit response limits and ignored revision feedback. Keep existing approval digests, target configuration, generated game files and AGENTS unchanged. This branch does not integrate into the RPG branch or main.

`ask_ai.model_options()` accepts per-process `GAME_AI_NUM_CTX` and `GAME_AI_NUM_PREDICT`; defaults remain 8192/1024. Validate ranges and output < context before HTTP. Never mutate shared payload options. `ModelLengthError` preserves the raw Ollama result and still rejects incomplete responses.

`design_plan` saves context, exact prompt and attempt status. Output-limit failures additionally save the incomplete response JSON, stop without automatic retry and provide the record folder. Invalid structural responses still receive validation feedback within the three-attempt bound; byte-identical invalid answers stop on repetition. Network/model errors stop and record their reason. Successful structural generation records `review_required`, never approval.

## Validation

88 tests passed: `python -m unittest test_ask_ai test_design_plan test_design_revision test_generation_profile test_thumby_capabilities`.
Tests use fake model/HTTP responses and temporary directories, covering output-limit diagnostics, per-call settings, early rejection, repeated failures, three distinct failures, revision/source protection, approval digests and existing Thumby constraints. Actual Ollama, Docker and hardware not run.

## Remaining work

This is not semantic proof of arbitrary natural-language requirements. It does not automatically repair RPG contracts, approve designs or recover partial JSON. Existing workflow request/state/retry gates remain unchanged. Next: inspect real local request/state lineage before connecting a reviewed design, then define explicit machine-readable acceptance contracts instead of keyword heuristics. Test workflow integration before adoption.

Local user-reported candidate: `outputs/design_20261009_005502_261874/design.json`, SHA-256 `12006806acb9de41b6239e6cb87193c2d6d66fa9edcb153dc7ad555601bdca31`. It combines Ollama contracts with ChatGPT-authored checks, is structurally valid and unapproved. File availability on GitHub is unverified; do not invent or replace it. Mac checkout and current branch were not accessible.

## 2026-10-09 remote workflow audit

Read-only inspection of `workflow.py`, `design_plan.py`, and `test_workflow.py` confirmed existing persistent stage transitions, request/context identity, protected SHA-256 artifacts, explicit retry, approval gates, and review-design direct-parent validation. No candidate design was imported or approved.

Integration gap: a failed `generate_design` leaves workflow at `generating_design` with a separate `design_*` diagnostic folder; workflow result reports only its workflow log and folder. Preserve both records and expose a diagnostic pointer before adding any automated recovery. Existing `--retry` explicitly regenerates rather than resuming a partial model response. `generating_tests` and `installing` remain distinct interruption states; do not treat installation as retryable without verifying side effects.

Next bounded implementation: attach a validated, read-only design-attempt diagnostic reference to workflow error output; test model-limit, model-error, and interrupted-retry paths with temporary folders. Then propose requirement-ID-to-observable-test traceability with explicit reviewer disposition (verified / failed / unverified); keyword coverage and model self-judgment are not evidence of compliance. Keep generated model output, reviewer edits, and execution evidence separately attributable. No live Ollama or hardware validation was performed in this audit.

## Diagnostic integration implementation

Commits `d27f27e` and `d1c993f` add a read-only `design_diagnostics` field to workflow error results for newly created design attempt records, and two mock-based regression cases. Existing folders and symlinked diagnostic folders are excluded. This is observability, not automatic recovery or semantic validation. Tests have been authored but **not executed** in this remote connector session; treat pass status as unknown. The folder scan is invocation-scoped and cannot attribute concurrent uncoordinated external writers; workflow's own lock does not lock standalone design_plan invocations. Follow up with isolated test execution and tighten provenance if concurrent writers are supported.
