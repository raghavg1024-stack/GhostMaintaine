# Contributing

Read [development instructions](docs/DEVELOPMENT.md), [architecture](docs/ARCHITECTURE.md), and [security boundaries](SECURITY.md) first.

1. Create a branch for a concrete improvement.
2. Keep patches small and record any deliberate limitation.
3. Add regression coverage for changed behavior and run the appropriate Docker tests.
4. For model/prompt changes, include live results and disclose cache use, dataset size, and failures.
5. Open a pull request describing the problem, resulting behavior and actual validation.

Never commit secrets, external repository clones, model weights, `.cache/`, or `runs/`. Do not edit fixtures to make a failing algorithm appear successful. Proposed repairs must remain documentation-only and must not weaken the verification target.

The project's MIT license covers contributed application code. Third-party models, dependencies and sample repository inputs retain their own licenses. AI coding assistance should be disclosed in changes and evaluations.
