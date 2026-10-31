# Recorded evidence and honest status

These are development records, not a general benchmark or proof of deployment readiness. Generated reports are snapshots. Regenerating their HTML layout does not rerun the recorded execution.

## Automated checks

Current Windows run: **48 tests discovered, 41 passed, and 7 Docker-only tests skipped**. The most recent full Docker run predates the new resource-profile and optional remote-inference changes: **38 tests passed** at that time. Assistant validation tests mock model output and check citations, edit boundaries, unique/indentation-only context matching, preservation of unrelated docs, and safe rejection. New tests cover profile budgets, endpoint consent, HTTPS requirements, and common log-secret redaction. The current resource-profile changes have not had a full Docker integration run.

## Live AI reasoning

| Case | Actual outcome | Qualification |
|---|---|---|
| haunted_env, final schema-constrained assistant | Original failed; control failed; patched docs passed fixed target. 16.697 seconds, one attempt, three uncached Qwen calls | Synthetic fixture; verifies that target only |
| haunted_init, earlier assistant iteration | Multi-step repair passed; recorded 43.306 seconds | One plan cache hit plus six uncached calls; predates final constrained-output prompt |
| haunted_secret | needs_human with a concrete source/format/configuration question | No fabricated token; larger earlier context, 136.354 seconds |
| Owner's minimal git_test repository through web/API | Readable needs_human report, 11.132 seconds | No applicable verified repair; an empty project is not a healthy application demonstration |

The committed [AI fixture snapshot](evidence/assistant-haunted-env/replay.html) contains the successful schema-constrained report, actual model-call metadata, events and diff. It is a recorded synthetic example, not a live hosted app.

## Legacy verification and expansion features

- Four broken fixtures were repaired; three healthy fixtures were unchanged; missing-token fixture returned needs_human.
- Version-sensitive fixture: Python 3.9 failed; 3.11/3.12 passed. A CI-sourced version-note patch was checked on 3.11. See [matrix](evidence/runtime-matrix/matrix.html).
- Generated setup.sh for haunted_env and haunted_init passed fresh execution; other setup artifacts are generated, not separately run.
- Legacy GhostBench v0: nine labelled steps over three README inputs; rules 6/9, Qwen 8/9. Each recovered two failure-inducing mutations and proposed zero patches on one healthy fixture. Upstream selection labels are pinned; end-to-end mutation results are synthetic only. Existing cache affects latency. See [benchmark table](evidence/bench/BENCH.md).
- Local two-repo scan: one safety-filter skip and one needs_human. No successful repair or population-level conclusion. See [anonymous scan summary](evidence/scan/scan_summary.json).
- PR Guard passed in the owner's isolated test repo and produced a report artifact plus bot patch comment: [draft PR](https://github.com/raghavg1024-stack/git_test/pull/1), [successful workflow](https://github.com/raghavg1024-stack/git_test/actions/runs/41126763065). That result does not prove this new repository's CI has passed; inspect its own Actions runs.

## Real repositories

- **Boltons**, pinned benchmark commit `d31d821d56c8f7756af9c30a864077f2e5855321`: direct setup check inconclusive because uv was absent in the image; scan skipped on safety filter. No patch success.
- **PyPA sampleproject**: legacy scan needed human input. AI attempts produced incorrect package-structure/metadata hypotheses and invalid/unverified patches. Latest recorded assistant outcome needs_human. Original README was not rewritten upstream.
- **Humanize**: cloned and inspected; execution unverified.
- **git_test**: static drift audit completed; the successful PR repair was against a deliberately broken bundled fixture.

No blind successful unfamiliar-repository repair has been established. Model explanations, confidence, and citations are not independent evidence of correctness.

## Presentation and deployment

The local browser form, progress polling, benchmark results and drift results were exercised. The AI web/API path returned a readable report. Replay slider behavior was unit-tested; fully offline browser execution remains unverified. A 28-second backup video is included as a labeled evidence walkthrough, not live inference footage. No public production deployment is verified, and no real-world recovery-rate claim is supported.

## First repository CI run

The first Ubuntu CI run exposed platform-dependent fixture hash ordering that Windows-only checks had missed. Fixture hashing now explicitly sorts relative POSIX filenames; the reviewed integrity records were recalculated without modifying fixture content. A cross-platform ordering regression test was added. Inspect the repository Actions badge for the latest hosted result.

## Upgraded recorded evaluation

See REAL_REPO_RESULTS.md for all three selected cases and exact commits. ItsDangerous and sampleproject passed with explicit declared-dependency preparation; the blind Humanize case was inconclusive. No automatic real-repository repair was achieved. The separate uncached synthetic fixture repair took 98.46 seconds and verified the unchanged goal in a fresh container. The 28-second backup video is a labelled evidence walkthrough, not live inference footage.
