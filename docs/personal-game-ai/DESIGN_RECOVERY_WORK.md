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
