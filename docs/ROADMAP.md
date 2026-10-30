# Proposed additions — not implemented

Priority is based on failures observed during development. These are suggestions, not delivered features.

## Next: improve usefulness and evidence

1. **Ask-and-answer maintainer conversation:** accept answers to specific questions, retain them as declared assumptions, and rerun without collecting secret values.
2. **Environment profiles:** explicitly choose Python/uv/Poetry/Node images and prerequisites before testing. Record the profile so missing tools do not become false documentation blame.
3. **Reliable repository evaluations:** curate licensed, commit-pinned held-out repos; measure healthy false positives, failure classification, repair correctness and patch quality. Current synthetic evidence is insufficient.
4. **Better context and config parsing:** bounded source-tree inventory, relevant file retrieval, structured YAML/multiline commands, CONTRIBUTING links, monorepos, and src-layout handling.
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
