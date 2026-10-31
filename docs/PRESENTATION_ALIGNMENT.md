# Presentation promise audit

Reviewed October 31, 2026 against the 10 slides, speaker notes, and embedded architecture image in the supplied GhostMaintainer.pptx. This is a comparison with source code and recorded evidence, not a new live-model benchmark. The original deck was not edited.

| Slide | Promise | Implementation and evidence | Assessment |
|---|---|---|---|
| 1 | Local AI suggestions checked by execution | `assistant.py` proposes docs edits; `ghostmaintainer.run` executes fixed checks. Saved synthetic repair: `evidence/judge-live/report.json`. | Implemented; automatic real-repository repair remains unverified. |
| 2 | Fresh contributor environment | `ghostmaintainer.run` creates a separate working copy and fresh Docker container per run. | Implemented for supported Python/Linux projects; not identical to every contributor's PC. |
| 3 | Link, instructions, optional preparation, Docker execution, diagnosis, docs repair, fresh verification, evidence | `app.run_job`, `assistant.run`, `runner_setup.dependency_plan`, report generation. | Implemented. Report visibility gaps repaired in this update. |
| 4 | React/Tailwind, local Python, separate Git copy, Docker, Ollama/Qwen, fixed verifier; Vercel hosts interface/evidence only | `web/src/App.jsx`, `app.py`, `assistant.ask`, `ghostmaintainer.run`, `web/vercel.json`. | Implemented. Optional remote inference is explicitly consent-gated; local is the default. Docker is not an absolute security guarantee. |
| 5 | Windows launcher, readiness checks/instructions, no model auto-download, public clone with commit, fixed user/config/detected goal | `start.cmd`, `start.ps1`, `doctor.py`, `runner_setup.health/default_goal`, `app.run_job`. | Implemented. Ollama is optional for rules-only mode. AI mode checks the selected installed model. Launcher itself has not been rerun in this audit. |
| 6 | Explicit preparation + network permissions, declared sources, fresh installs, fenced/prose/inline reading, numbered citations, corrective retry | `app.validate_request_flags`, `dependency_plan`, `ghostmaintainer.run/extract`, `assistant.plan/validate_plan/citations`. | Implemented with supported declarations. Bounded excerpts can omit relevant instructions; citations do not prove reasoning. |
| 7 | Logs, exit codes, timing; distinguish docs/environment/credentials/code/uncertainty; init/test example | Runner events; `assistant.propose` categories; `fixtures/haunted_env`; archived Qwen repair. | Implemented; model classification can be wrong. Deterministic environment blockers may stop before model diagnosis. |
| 8 | Docs-only patch, repeated failure, independent patched interpretation, fresh fixed check, zero-test rejection | `assistant.apply_edits/run`, `ghostmaintainer.run`; synthetic repair records. | Implemented. Full current Docker integration and live-model rerun are unverified in this audit. |
| 9 | Four status labels, journey, stages/readiness, uncached option, citations/questions/diffs/downloads/cache disclosure, no auto PR | API/UI pipeline; report renderer now shows original/control/verification, diagnosis, sources/questions, exact diff, call/cache metadata. | Implemented. Missing stages explicitly display “Not run”; inconclusive stays inconclusive. |
| 10 | Synthetic repair; ItsDangerous/sampleproject pass with preparation; Humanize inconclusive; 38 tests | Pinned saved records in `docs/REAL_REPO_RESULTS.md`, `docs/evidence/judge-live`, `docs/evidence/real-evaluation`. | Historical results, not rerun here. Current local suite: 53 discovered, 46 passed, 7 Docker checks skipped. Keep the slide's 38-test figure labeled as an earlier Docker run. |

## Changes from this audit

- Restored visible diagnosis categories, maintainer questions, source receipts, exact documentation diffs, fresh/control execution logs and model cache records in HTML reports. Markdown summaries include diagnosis, questions, stages and the diff too.
- Removed report language that incorrectly assumed every inconclusive run stopped before testing, or that every AI report failed to reach a passing check.
- Removed a repository-specific EduMind explanation from the generic report guidance.
- Refreshed the published report layouts from their existing JSON. Their underlying execution/model-call data and timestamps were not rerun or replaced. The backup video retains its original recorded layout.

## Presentation boundaries to keep

- “Faster fixes” and “healthier projects” are intended benefits; no measured human time savings or project-health improvement is established.
- Supported prototype: Python/Linux with a root README. Arbitrary languages, large-repository completeness, universal model accuracy, and automatic repairs on unfamiliar real repositories are not established.
- Vercel publishes the interface and selected saved reports. Start the local Python backend, Docker and the selected Ollama model to run new AI analyses. No local backend update is delivered merely by refreshing Vercel.
- No automatic upstream commit/PR is part of a normal website check. Maintainers review and apply changes themselves.
- Regression checks use mocks/fixtures where appropriate. They do not establish local model accuracy. The fresh Docker/model loop must be rehearsed on the presentation PC before calling it a live demonstration.
