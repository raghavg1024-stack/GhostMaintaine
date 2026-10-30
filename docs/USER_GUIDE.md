# Website user guide

## Requirements and startup

Use a **source checkout** with Python 3.11+, Git, and a running Docker engine capable of Linux containers. AI assistant mode also requires Ollama and the selected model installed locally. No paid API or OpenAI API key is required. Python's standard library supplies the application runtime; Docker, Git, Ollama, and model weights are separate installations.

```sh
git clone https://github.com/raghavg1024-stack/GhostMaintaine.git
cd GhostMaintaine
docker pull python:3.12-slim
ollama pull qwen3:4b-instruct
python app.py
```

If that exact model tag is unavailable from your registry, install an available Ollama instruction model and enter its exact installed name under Check settings. The tested local tag is `qwen3:4b-instruct`; weights are not bundled. Run `ollama list` to inspect installed names and check your model's license separately.

On Windows, `./start.ps1` is a convenience launcher that locates Python and Docker. Open **http://127.0.0.1:8765**. Stop the server with Ctrl+C. For another port, set `GHOST_PORT` before starting; the default browser link remains 8765 in the launcher text.

## Check a repository

1. Choose **AI maintainer assistant**, the default mode.
2. Paste a public root GitHub repository URL, for example `https://github.com/owner/repository`.
3. Expand **Check settings**. Select your installed model, supply the intended test command if necessary, and enable network only when container dependency downloads are needed.
4. Click **Ask GhostMaintainer**. Wait for cloning, reasoning, and Docker execution to complete.
5. Read the AI explanation and its evidence, the before/after results, and maintainer questions. Download and review the diff before applying it yourself.

Only public github.com root URLs are accepted. Private repositories, branch/tree URLs, arbitrary Git hosts, local folder uploads, and interactive login/setup are not supported by the web form. A root `README.md` is required. Repositories containing symlinks are rejected. The runtime image targets Linux/Python; this is not general Node/Java/Rust support. The drift audit can inspect some Node configuration statically.

## Define success explicitly

If no test command is entered, the application uses a repository-root `ghostmaintainer.json` when present. Otherwise it defaults to `python -m unittest discover -v`. This default is often unsuitable; choose the project's actual test command.

```json
{"cmd": "python -m unittest discover -v"}
```

For a repository-configured smoke test, an explicit output marker is also supported:

```json
{"cmd": "python smoke_test.py", "marker": "APPLICATION_SMOKE_OK"}
```

The browser's custom test-command field supplies a command only, not a custom marker. Without a marker, a positive unittest or pytest test count is required. Zero tests is not accepted. Exit code zero alone does not establish a pass. The target stays fixed across repair attempts. A pass verifies this target in this environment, not every feature or the completeness of the documentation.

## Analysis menu

| Mode | What it does | Dependencies |
|---|---|---|
| AI maintainer assistant | Interprets onboarding prose/inline commands, reasons about failures, proposes docs edits, and independently interprets patched docs before Docker verification | Ollama/model, Git, Docker |
| Verify & heal the README | Legacy bounded config-command search; rules mode by default | Git, Docker |
| Generate and verify setup artifacts | Produces setup.sh, devcontainer.json, and agent instructions after a passing run; separately executes setup.sh | Git, Docker |
| Audit environment variables & versions | Advisory static Python/Node checks; no project commands execute | Git; UI readiness still expects Docker installed |
| Compare Python runtimes | Runs the same instructions on selected Python images, at most three concurrently | Git, Docker and selected images |
| Benchmark local models | Compares models on the fixed v0 dataset, not the repository URL field | Git, Docker, selected Ollama models |
| Scan a repository list | Up to 20 public URLs; license/setup prefilters, total deadlines, anonymous local aggregates | Git, Docker; optional network |

The model field is optional outside assistant mode. Blank assistant mode uses `qwen3:4b-instruct`; blank legacy mode uses rules. The benchmark has its own comma-separated model list. Matrix values look like `py3.9,py3.11,py3.12`; pre-pull the corresponding `python:VERSION-slim` images.

## Read the result

- **healthy**: the original documented path and declared verification target passed.
- **repaired**: original/control failed, a proposed docs change was independently interpreted, and the fixed target passed in a fresh container.
- **needs_human**: no verified repair is available. AI questions may identify missing information; invalid AI proposals can also result in this state.
- **inconclusive**: an environment limitation, unstable failure, code concern, or uncertainty prevents a documentation conclusion.
- **error**: application, clone, model, or validation failure interrupted the job. No successful repair should be inferred.
- **feature_complete**: an audit/matrix/benchmark/scan completed; this does not mean repository setup passed.

AI confidence and explanations are hypotheses. Citations validate file/line existence, not the truth of the interpretation. Invalid proposals are rejected. Some model-plan failures still appear as job errors. The assistant can make incorrect claims even when a location exists.

Reports contain the summary, explanation, proposed/verified diff, source receipts, fixed test target, collapsed logs, measured sandbox timing, and a recorded-event replay. Replay runs saved data; it is not another live execution. Full static logs remain accessible without JavaScript. Old reports can lack timings.

## Artifacts and persistence

Local jobs are stored under `runs/web/JOB_ID/`: cloned input in `checkout/`, generated evidence in `result/`. The application does not commit, push, open PRs, or modify upstream repositories. Patch application is manual. The original checkout is not overwritten by model repair proposals; temporary copies are used for verification.

Only one web job runs at a time. Job status is in memory; restarting loses the polling index, while disk artifacts remain. There is currently no history UI or cancellation button. Raw model responses are cached under `.cache/`; per-call cache use is reported. Delete the relevant cache entries if you need an uncached demonstration. No backup video or hosted deployment is included.

`ship/setup.sh` is separately verified. `devcontainer.json` and `AGENTS_setup.md` are generated from passing commands, not separately run. Copy the entire `ship/` directory to your project root before using them.

## Troubleshooting

| Symptom | Next step |
|---|---|
| Docker missing/unreachable | Install/start Docker Desktop or Docker Engine; ensure Linux containers and correct PATH |
| Model missing/unreachable | Start Ollama, run `ollama list`, select the exact installed model name |
| Missing uv/git/system library | The base image may be unsuitable; CLI `--image` supports a prepared image. Do not automatically blame docs |
| Network install failure | Inspect logs; explicitly enable network only for an inspected repository |
| Zero tests | Correct the verification command; do not substitute a trivial success marker |
| AI citation/patch rejected | Read the validation explanation; no verified fix is available. Try rules mode or review the documents manually |
| Slow AI | Context/model size affects GPU/CPU placement. Current assistant uses an 8K context and bounded input; latency is machine-dependent |

Run only inspected repositories. This local prototype is not safe public multi-tenant hosting; see [security boundaries](../SECURITY.md).
