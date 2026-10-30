# GhostMaintainer

**A local AI maintainer assistant for understanding and checking repository onboarding.**

[![CI](https://github.com/raghavg1024-stack/GhostMaintaine/actions/workflows/check.yml/badge.svg)](https://github.com/raghavg1024-stack/GhostMaintaine/actions/workflows/check.yml)
[MIT license](LICENSE) · [User guide](docs/USER_GUIDE.md) · [Architecture](docs/ARCHITECTURE.md) · [API](docs/API.md) · [Evidence](docs/EVIDENCE.md) · [Roadmap](docs/ROADMAP.md)

Paste a public GitHub repository URL into the local website. GhostMaintainer uses an installed Ollama model to interpret onboarding documents, explain setup failures, propose evidence-backed documentation edits, and ask specific maintainer questions. Docker checks proposed repairs against a fixed test target in a fresh environment.

**Status: hackathon prototype.** A live AI fixture repair has passed; reliable repair on unfamiliar real repositories remains unverified. Model explanations can be wrong. This is a local application, not a deployed public service or a universal setup-success guarantee.

<img src="docs/images/assistant.png" alt="GhostMaintainer local website with AI maintainer assistant selected" width="420">

## Start the website

Install **Python 3.11+**, **Git**, **Docker** with Linux containers, and **Ollama** for AI mode. Start Docker and Ollama first. No paid API key is required.

```sh
git clone https://github.com/raghavg1024-stack/GhostMaintaine.git
cd GhostMaintaine
docker pull python:3.12-slim
ollama list
python app.py
```

Open **http://127.0.0.1:8765**. On Windows, `./start.ps1` is an alternative launcher. Use the source checkout; the full web/fixture assets are not packaged as a standalone pip application.

Assistant mode defaults to the tested installed tag `qwen3:4b-instruct`. Install an instruction model through Ollama if needed and select its exact installed name in **Check settings**. Model weights are not included; availability and license depend on the model you install.

1. Choose **AI maintainer assistant**.
2. Paste an inspected public GitHub root URL.
3. In **Check settings**, choose the intended test command and optionally enable dependency-download networking.
4. Click **Ask GhostMaintainer** and read the explanation, evidence, questions and result.
5. Review any verified diff before applying it yourself. The web app never opens PRs or writes upstream.

The default goal is `python -m unittest discover -v` unless the repository supplies `ghostmaintainer.json`. Change it for projects using another runner. Zero tests is not a pass. Supported execution is currently Python/Linux with a root README.md; missing tools, complex setup and unsupported repositories may remain blocked.

## What the AI does

| Step | AI responsibility | Deterministic control |
|---|---|---|
| Understand | Interpret README/CONTRIBUTING prose, inline code and a contributor path | Validate selected commands and citations |
| Diagnose | Explain logs using configuration and selected source/tests | Preserve actual logs and the unchanged test target |
| Propose | Write documentation prose/commands and maintainer questions | Constrain edit paths; validate unique context and source locations |
| Verify | Independently interpret patched documents without the repair context | Run in fresh Docker; require successful non-empty verification |

Up to three repair attempts are allowed. Original instructions are repeated as a negative control. A model's confidence and file citations do not prove its explanation is correct. Proposed changes are offered as verified only when the execution check passes.

## Website modes and features

| Capability | Available behavior |
|---|---|
| AI assistant | Interpretation, failure explanation, documentation proposals and maintainer questions |
| Rules-based drill | Legacy bounded search over config commands, without Ollama |
| Setup artifacts | Generates setup.sh, devcontainer.json and agent instructions; setup.sh alone is separately verified |
| Drift audit | Advisory literal Python/Node environment-variable and version checks |
| Python matrix | Runs multiple Python images; grid and CI-sourced version note |
| Friction/replay | Recorded command timings, failure details and interactive saved-event scrubber |
| GhostBench v0 | Small hand-labelled model-selection comparison and fixture recovery checks |
| Repository scan | Safety/license prefilters and anonymous local aggregate results |
| PR Guard | Rules-only controlled-fixture GitHub Action, artifacts and same-repo patch comments |

There is no sample button in the website. Bundled fixtures are retained for transparent tests and demonstrations. See the [user guide](docs/USER_GUIDE.md) for every mode, settings, artifacts, limits and troubleshooting.

## Reproduce a controlled check

```sh
# No model required; actual Docker verification.
python ghostmaintainer.py drill fixtures/haunted_init --backend docker

# AI reasoning and generated documentation repair.
python ghostmaintainer.py assist fixtures/haunted_env --labeller qwen3:4b-instruct

# Restricted fixture-only checks; not a host runner for arbitrary repos.
python ghostmaintainer.py eval --backend fixture
```

For another repository, fix the test target before repair:

```json
{"cmd": "python -m unittest discover -v"}
```

Save that as `ghostmaintainer.json` at its root, or provide the command through the website. CLI `--net` explicitly permits container networking. See [development](docs/DEVELOPMENT.md) for matrix, ship, benchmark, scan and test commands.

## Verified evidence and limits

- **25 regression tests passed** with Docker locally. Seven assistant tests validate boundaries with mocked responses; they are not model-accuracy tests.
- A schema-constrained AI `haunted_env` repair passed in **16.697 seconds** with **three uncached Qwen calls** and fresh original/control/verification runs.
- A multi-gap fixture repair and a missing-token question were also recorded. Their runtimes/context settings differ.
- Python matrix: 3.9 fails the version-sensitive fixture; 3.11 and 3.12 pass.
- Both example setup scripts passed separate fresh-container verification.
- Legacy GhostBench v0: rules 6/9, Qwen 8/9 labelled selections; both recovered 2/2 failure-inducing fixture mutations. Cache-sensitive latency is disclosed. This does not measure the new reasoning assistant.
- Real-repository attempts exposed missing tools, src-layout misdiagnoses and invalid AI patches. No successful independent real-repository repair is claimed.

Selected recorded artifacts are committed under [docs/evidence](docs/evidence/). Full local runs, caches and external repository clones are excluded. Read [evidence details](docs/EVIDENCE.md) before interpreting the numbers.

## Security and hosting

The server binds to loopback, validates Host/Origin and requires a session token for POST requests. Docker runs non-root with resource limits, dropped capabilities, disposable workspaces and network off by default. These controls are not complete protection against malicious repositories.

**Run inspected inputs only. Do not expose this prototype as a public multi-tenant service.** Models can hallucinate; repositories can contain secrets; tests/markers can be forged. See [SECURITY.md](SECURITY.md).

## Project map

```text
app.py                  Local HTTP API and job execution
assistant.py            Model-led interpretation and repair
ghostmaintainer.py       Runner, verification, legacy CLI and reports
features.py             Audits, matrix, ship, bench, scan and guard
web/index.html          Browser interface
fixtures/               Deliberately controlled evaluation inputs
bench/                  Hand labels, pinned sources and selection list
examples/               Drift audit example
test_*.py               Regression tests
.github/workflows/      CI and controlled PR Guard
docs/                   User guide, API, architecture, evidence and roadmap
```

## What to add next

Priorities are **maintainer answer-and-rerun conversations**, **explicit environment profiles**, **held-out real-repository repair evaluation**, and **better context/config parsing**. Then add history/cancellation, target discovery, improved patch review and packaging. These are proposals, not shipped features; see the [prioritized roadmap](docs/ROADMAP.md).

## Contribute and credits

See [CONTRIBUTING.md](CONTRIBUTING.md). Application code is MIT licensed. Python, Git, Docker, Ollama, models and sample inputs retain their own terms. AI coding assistance: OpenAI Codex; runtime AI is the selected local model. Prior art includes [Repo2Run](https://github.com/bytedance/Repo2Run) and [Rundoc](https://github.com/eclecticiq/rundoc); no first-of-its-kind claim is made. Upstream benchmark input: [Boltons](https://github.com/mahmoud/boltons), BSD licensed. Other evaluated input: [PyPA sampleproject](https://github.com/pypa/sampleproject), MIT licensed.
