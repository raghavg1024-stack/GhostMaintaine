# Development and verification

Use a source checkout, Python 3.11+, Git and Docker. AI validation additionally requires a local Ollama model. The Python runtime has no third-party application dependencies.

## Tests

Fast mode exercises the restricted bundled-fixture runner and skips Docker-only tests:

```sh
python -m unittest -v
```

Full Linux/macOS Docker suite:

```sh
docker pull python:3.12-slim
GHOST_TEST_BACKEND=docker python -m unittest -v
python ghostmaintainer.py eval --backend docker
```

Windows PowerShell:

```powershell
$env:GHOST_TEST_BACKEND = 'docker'
python -m unittest -v
python ghostmaintainer.py eval --backend docker
```

At the latest recorded full run, **24 tests passed**. Seven assistant validation tests use mocked model responses; they test boundaries, not model intelligence. Live model execution was tested separately on fixtures. See [evidence](EVIDENCE.md).

Fixtures contain deliberately omitted steps. Their exact-byte integrity records are stored in `fixtures/manifest.json`; `.gitattributes` preserves fixture line endings across clones. Do not regenerate the hashes to hide unreviewed fixture changes. Never run tests that edit the original fixtures in place.

## Useful CLI commands

```sh
python ghostmaintainer.py assist fixtures/haunted_env --labeller qwen3:4b-instruct
python ghostmaintainer.py drill fixtures/haunted_init --backend docker
python ghostmaintainer.py baseline fixtures/haunted_order
python ghostmaintainer.py mutate fixtures/healthy --backend docker
python ghostmaintainer.py drift examples/drift_case
python ghostmaintainer.py ship fixtures/haunted_init
python ghostmaintainer.py bench-models --models "rules,qwen3:4b-instruct"
python ghostmaintainer.py scan --list bench/repos.txt --net on --max-repos 2 --timeout 120
```

Matrix preparation and execution:

```sh
docker pull python:3.9-slim
docker pull python:3.11-slim
docker pull python:3.12-slim
python ghostmaintainer.py drill fixtures/haunted_version --matrix "py3.9,py3.11,py3.12"
```

Quote comma-separated arguments in PowerShell. Plain `drill --net` enables network; feature commands such as `scan` and `ship` accept `--net on|off`. Use `--help` on the relevant command. Python 3.9 is included as an intentionally failing compatibility example, not a recommended new deployment runtime.

## Exit behavior

Normal drill/assist returns 0 for healthy/repaired, 2 for unresolved/inconclusive, and 1 for caught operational errors. Evaluation checks expected fixture outcomes; the intentionally missing-secret fixture must remain needs_human. Matrix command completion does not imply every cell passed. Guard emits a Markdown comment alongside evidence.

## CI workflows

- `check.yml`: push/PR checks, Python 3.12, Docker suite, fixture evaluation, uploaded reports. It does not require Ollama or a paid key.
- `pr-guard.yml`: PRs affecting setup/config files run the controlled haunted_env fixture in rules mode, upload evidence, and post a patch comment for same-repository PRs. It currently guards that demonstration fixture, not arbitrary repository-root onboarding. Adapt the target explicitly before adopting it elsewhere.

PR analysis has contents-read access, checkout credential persistence is disabled, and comments are posted in a separate job. Fork PRs do not receive comment-write access. GitHub Actions is CI; there is no deployment/CD workflow.

## Contributing

Open a branch, make a focused change, add meaningful regression coverage, and run the appropriate suite. Model prompt changes require fresh live evaluations because cached answers can hide behavior changes. State whether results are cached or uncached. Keep application repairs docs-only; never weaken the fixed goal to claim success. Describe known failures honestly.

Do not commit downloaded repositories, model weights, runtime caches, secrets, or private run logs. The project uses MIT licensing; model/runtime dependencies retain their own terms.
