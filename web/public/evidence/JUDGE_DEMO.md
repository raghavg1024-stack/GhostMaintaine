# Three-minute judge demonstration

## What to say

GhostMaintainer is a local AI assistant for Python contributor onboarding. Ollama reads documentation and proposes a sourced documentation repair. A fresh Docker container checks the same fixed command. Source citations are checked for file/line existence; they do not prove the reasoning is correct.

## Before presenting

1. Double-click start.cmd, or run ./start.ps1. It checks Git, the actual Docker engine, Ollama, and the selected installed model. Set GHOST_MODEL before launching if using another installed model. No model is downloaded automatically.
2. Verify the Docker image exists: docker image inspect python:3.12-slim. If missing, pull it before going on stage.
3. Show ollama list, then ollama ps during the live analysis. The latter shows loaded models; it does not by itself prove inference is occurring, so also show uncached call records.
4. Open http://127.0.0.1:8765. Vercel is the hosted interface, not the Docker/Ollama backend.

## Reliable local-model demonstration

From the project directory:

```powershell
./run.ps1 assist fixtures/haunted_env --labeller qwen3:4b-instruct --no-cache --out runs/judge-rehearsal
```

Label this as a **synthetic fixture with a deliberately missing instruction**. Do not describe it as a blind real-repository success. Show the original missing-config failure, the AI diagnosis, the documentation diff adding python app.py init, and the fresh passing fixed goal. The recorded uncached run took 98.46 seconds; all three recorded model calls were uncached. A new run may take longer or fail.

## Live web demonstration on a real repository

Select AI maintainer assistant, paste an inspected Python repository, and leave the target blank to use its ghostmaintainer.json or detect pytest/unittest. Select the local model. Enable Live AI demo to bypass model response caching. To prepare declared dependencies, explicitly enable BOTH dependency preparation and container network access. Preparation is recorded separately and repeated in each fresh sandbox. A healthy result with preparation is environment-assisted; it does not prove the original README alone was sufficient.

Show the stage log, diagnosis, maintainer questions, exact diff, unchanged verification target, execution events, and downloadable evidence. Never promise a repair before verification finishes.

## Backup and honest limits

The checked-in docs/evidence/judge-live snapshot is precomputed evidence, not a live run. The backup video is docs/evidence/GhostMaintainer-Judge-Backup.mp4 (about 28 seconds). It is an evidence walkthrough, not a recording of live model inference. Use these only if Docker/Ollama fails, and say so explicitly. Read the complete real-repository results alongside this demonstration. No verified automatic repair on an unrelated real repository has been established by this fixture run.

## Likely judge questions

- Why an LLM? It interprets prose and synthesizes a context-based documentation explanation and edit. Its output is not trusted until the exact plan and patch pass validation and execution.
- Why local? Inference requests go to Ollama on 127.0.0.1:11434; no cloud LLM key is required. Git cloning and dependency installation still use the network.
- What can change? Only the supplied onboarding documentation. Application code, tests, dependency declarations, and the fixed test goal are not repaired by this assistant.
- Is Docker a complete security boundary? No. This prototype is for repositories the operator trusts and has inspected; it is not a public arbitrary-code execution service.

## Current selected real-repository results

With opt-in declared-dependency preparation: ItsDangerous and sampleproject passed their fixed checks; the blind Humanize case was inconclusive. These are three selected cases, not an ecosystem-wide success rate. See REAL_REPO_RESULTS.md for commits and all outcomes.
