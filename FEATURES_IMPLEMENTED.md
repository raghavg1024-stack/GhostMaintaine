# Verify. Heal. Ship. Measure. Guard.

All eight requested features are implemented in this source checkout. The browser app offers seven analysis modes; friction and replay are embedded in drill reports, and PR Guard runs on GitHub. No sample button was reintroduced.

| Feature | How to use | Verification and practical scope |
|---|---|---|
| F1 Runtime matrix | Choose **Compare Python runtimes**, or `python ghostmaintainer.py drill fixtures/haunted_version --matrix "py3.9,py3.11,py3.12" --out runs/features` | Python 3.9 fails; 3.11 and 3.12 pass. CI-sourced version-note patch is separately checked on 3.11. A version note does not make an unsupported runtime work. Pre-pull images. Up to 3 cells run concurrently. |
| F2 Setup artifacts | Choose **Generate and verify setup artifacts**, or `python ghostmaintainer.py ship fixtures/haunted_init --out runs/features` | Both haunted_env and haunted_init setup.sh files passed fresh Docker execution. devcontainer.json and AGENTS_setup.md are generated, not separately run. Copy the entire ship folder to the project root before use. |
| F3 Drift | Choose **Audit environment variables & versions**, or `python ghostmaintainer.py drift examples/drift_case --out runs/features/drift` | Finds the intentionally undocumented variable and version mismatch. Healthy fixture has no findings. Literal Python/Node checks, advisory only; no patches. |
| F4 Friction | Automatically in new drill reports | Per-step durations and bars, totals, failure/slowest highlights, and measured command time until first verified green. Excludes model/image/container startup time and is not human time. Older stored reports lacking durations say not recorded. |
| F5 GhostBench v0 | Choose **Benchmark local models**, or `python ghostmaintainer.py bench-models --models "rules,qwen3:4b-instruct" --out runs/features/bench` | Reproducible pinned upstream selection labels plus fixture end-to-end checks. Nine labelled steps: rules 6/9, Qwen 8/9. Both recover 2/2 failure-inducing fixture mutations; zero patches on 1 healthy fixture. Tiny sample; no general ranking. Cached latency is disclosed. |
| F6 Ecosystem scan | Choose **Scan a repository list**, or `python ghostmaintainer.py scan --list bench/repos.txt --net on --max-repos 2 --timeout 120 --out runs/features/scan` | Local JSONL and anonymous aggregate. Two-repository run: one safety-filter skip, one needs_human. No successful repair or ecosystem prevalence claim. Hand-select and inspect repos first. No external findings are published. |
| F7 PR Guard | `.github/workflows/pr-guard.yml`; CLI `guard` | Live draft PR in the owner's git_test repo produced a successful Actions run, downloadable artifact, and bot patch comment. This workflow targets the isolated fixture; change the target path for a different project. Same-repo comments only; forks get read-only analysis/artifacts. No PAT or committed secret. |
| F8 Replay | Slider and arrow keys in replay.html | Replays recorded events, highlights the selected step, shows output and phase step completion. Runs offline without external requests. Static logs remain usable without JavaScript. |

## Evidence

- Resource modes: low-memory (Qwen3 1.7B, 4K context), balanced (Qwen3 4B, 8K context), and rules-only (no LLM). Selected evidence is capped and listed in the report. Optional remote Ollama requires HTTPS and explicit per-run consent; the full checkout is not sent.
- Current local run: 51 tests discovered, 44 passed, and 7 Docker-only tests skipped. The latest recorded full Docker run before these profile changes had 38 tests pass; Docker integration has not been rerun for this change. Replay JavaScript has a separate test for scrubbing, output, phase completion, and selected-step highlighting.
- Runtime matrix: `runs/features/haunted_version/matrix.html`.
- Ship verification: `runs/features/haunted_env/ship/verification.json` and `runs/features/haunted_init/ship/verification.json`.
- Benchmark: `runs/features/bench/BENCH.md` and `bench_models.json`.
- Drift: `runs/features/drift/drift.json`.
- Scan: `runs/features/scan/scan_results.jsonl`, `scan_summary.json`, and `SCAN.md`.
- Live PR: https://github.com/raghavg1024-stack/git_test/pull/1
- Successful PR Guard run: https://github.com/raghavg1024-stack/git_test/actions/runs/41126763065
- Original successful bot comment: https://github.com/raghavg1024-stack/git_test/pull/1#issuecomment-6533179689

The default branch was not changed. The demonstration is on a draft PR branch for review. The app remains local-only at http://127.0.0.1:8765. A single scan/benchmark can take minutes; runs are serialized in the web app. This is an inspected-repository prototype, not a public multi-tenant sandbox service.

Latest upgrade: see docs/JUDGE_DEMO.md and docs/REAL_REPO_RESULTS.md. The fresh synthetic AI repair passed in 98.46 seconds; two selected real repositories passed with preparation and one blind case was inconclusive. Zero automatic unrelated-real-repository repairs are claimed.
