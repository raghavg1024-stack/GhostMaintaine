# Roadmap

## Implemented in the current branch

- Low-memory and balanced model context profiles, plus a deterministic rules-only path.
- Selected-file evidence packs instead of sending the whole repository to the model.
- Optional remote Ollama inference with HTTPS validation and a per-run user consent gate.
- Setup-first product flow: replay documented onboarding, keep the test target fixed, and offer a documentation repair only after fresh verification.

These features still need broader real-PC and held-out repository evaluation. Profiles do not promise smooth inference on every computer, and the supported execution environment remains Python/Linux.

## Next: improve usefulness and evidence

## Next: improve usefulness and evidence

1. **Ask-and-answer maintainer conversation:** accept answers to specific questions, retain them as declared assumptions, and rerun without collecting secret values.
2. **Runtime profiles:** explicitly choose supported Python, uv, Poetry, and later Node images/prerequisites before testing. Record the profile so missing tools do not become false documentation blame.
3. **Reliable repository evaluations:** curate licensed, commit-pinned held-out repos; measure healthy false positives, failure classification, repair correctness and patch quality. Current evidence is not enough for broad success claims.
4. **Better context and config parsing:** select relevant sections within the current low/balanced budgets; add structured YAML/multiline commands, more CONTRIBUTING links, monorepos, and src-layout handling.
5. **Patch review quality:** explain each change, avoid duplicate commands/prose, flag unsupported claims, preserve formatting and let users approve a diff before applying locally.

## Then: improve the local experience

6. **Run history and cancellation:** persistent local job index, cancel button, detailed phase progress, cleanup/retention controls, and resumable review.
7. **Success-target discovery with approval:** suggest project-specific test/smoke commands from configuration, explain the choice, and fix the approved target before repair.
8. **Model evaluation:** compare reasoning/repair models rather than only command selection; include failed/refused outputs, uncached latency and hardware details.
9. **One-click packaging:** ship a reproducible local installer/container with all web assets and a clear Docker/Ollama health check.
10. **Maintainer-controlled PR integration:** optional branch/PR creation for owned repositories after diff review. Current web checks never write upstream.

## Later, after the boundaries are stronger

- Public hosting backed by a hardened disposable execution service, authentication, rate limits and abuse controls.
- GitLab/private-repository support with explicit credential boundaries.
- A setup badge based on a declared target/environment and dated evidence; never a universal 100/100 guarantee.
- Real longitudinal setup regression metrics and appropriately scoped CI gates.

Avoid adding more visual panels before real-repository repair reliability improves. A backup demonstration recording is also still needed for presentation resilience.
