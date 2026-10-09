# Design failure records and model limits

The tool can now preserve why design generation stopped without copying diagnostic Python into the terminal. No game or product specification was changed.

Set limits for one execution, for example:

```bash
GAME_AI_NUM_CTX=16384 GAME_AI_NUM_PREDICT=6144 python design_plan.py --revise outputs/design_EXAMPLE/design.json --feedback feedback.txt
```

Replace the example paths with the actual source design and feedback file. Larger limits can increase memory and response time; this example has not been tested on the user's Mac. These environment settings also apply to other callers of `ask_model` in that process. Defaults are unchanged. They are not token counting or guaranteed protection against input truncation.

Inspect the reported `outputs/design_*` folder:

- `context.txt`: generation context.
- `prompt_N.txt`: exact submitted prompt, including validation feedback.
- `answer_N.txt`: completed model response before structural validation.
- `attempt_N.json`: status, reason and no automatic approval.
- `response_N.json`: incomplete Ollama response when output hits its limit.

The incomplete response never becomes `design.json`. Review settings and explicitly retry using the existing workflow `--retry` when the workflow is in an eligible interrupted generation stage. A direct `design_plan` rerun creates a new candidate folder. Neither route approves results automatically. An identical invalid response stops on repetition rather than spending the remaining call budget; different invalid responses retain the maximum of three attempts.

Validation: 88 automated tests passed with fake responses. Live model behavior, all workflow integrations and hardware remain unverified. Natural-language contract correctness still requires review and fixed tests; a structure pass is not a game completion claim.

## Workflow error diagnostics (new, not yet execution-verified)

When design generation fails, the JSON result can include `design_diagnostics`, listing newly observed `design_*` folders and their `attempt_N.json` status/error records. This does not approve, resume, or alter incomplete responses. Older folders are omitted. Use the recorded paths to inspect prompts and model-limit responses. Two regression tests were added but have not yet been run; live Ollama and device behavior remain unverified.
