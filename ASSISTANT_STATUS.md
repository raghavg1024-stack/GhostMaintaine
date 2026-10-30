# AI maintainer assistant

The browser now defaults to **AI maintainer assistant**. The legacy deterministic drill and other features remain available separately.

The local model does substantive interpretation and repair work: it reads onboarding prose/inline commands, reasons from logs plus configuration and selected source/tests, writes documentation replacement prose and commands, and asks maintainer questions. JSON-schema constrained repair output restricts targets to actual documentation files. File/line citations and unique patch context are validated. Indentation-only differences are accepted; changed words are not fuzzily matched. No application-code patch is accepted.

Each proposed repair is independently interpreted from patched docs only and checked in fresh Docker against the unchanged verification command. Original instructions are rerun as a negative control. At most three attempts are made. A successful test verifies that target only; model explanations can still contain incorrect claims. Failed proposals are not published as verified patches.

## Recorded evidence

- Final schema-constrained haunted_env run: repaired in 16.697 seconds, one repair attempt, three uncached Qwen calls. Original and negative control failed; independent patched-doc interpretation and fresh fixed-goal verification passed. Report: `runs/assistant-current/haunted_env/replay.html`.

- The reasoning pipeline repaired the two-gap haunted_init fixture and passed fresh verification. One recorded run took 43.306 seconds, with one cached plan call and six uncached reasoning/interpretation calls. This predates the final schema-constrained prompt changes; see current run artifacts separately.
- The missing-token fixture returned needs_human plus a specific question about the token's source/format and secure configuration. It did not invent a token. That recorded run used the larger initial context and took 136.354 seconds.
- PyPA sampleproject was tested repeatedly with its original README and the same unittest goal. The assistant produced incorrect hypotheses about package metadata; proposals did not pass verification. The latest saved result is needs_human. There is still no successful independent real-repository repair.
- 25 Docker/validation regression tests passed: 18 existing tests plus 7 assistant schema/boundary/citation/patch tests. The assistant validation tests use mocked responses; they do not establish model accuracy. The browser/API path also returned a readable needs_human report for the owner's minimal repository in 11.132 seconds.

## Limits

Local Qwen qwen3:4b-instruct is the default. Model context is now 8K with bounded file selection; documents over the assistant's 16K-character limit are rejected. Larger context spilled onto CPU during testing, so it was reduced. Context is incomplete, and the model may misdiagnose src-layout or installation failures. Citations prove a location exists, not that its interpretation is correct. JSON response caching is disclosed per call. This is a task-oriented assistant, not an unrestricted autonomous agent or interactive chat application. Run only inspected repositories.

```sh
python ghostmaintainer.py assist /path/to/repository --labeller qwen3:4b-instruct --net
```

A fixed ghostmaintainer.json goal is required for CLI use; the browser can provide a goal through Check settings. Leave network disabled when dependencies are already available. Never enter real secret values in model prompts or maintainer answers.
