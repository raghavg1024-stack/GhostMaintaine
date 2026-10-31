# Execution and security boundaries

GhostMaintainer executes repository-supplied and model-proposed setup commands. **Use inspected repositories on a development machine without sensitive workloads.** Docker and a denylist are not a complete malicious-code isolation boundary.

## Implemented controls

- Loopback-only web server, strict Host checks, foreign-Origin rejection and per-process POST token.
- Public github.com root URLs only; no interactive credentials; Git global/system configuration disabled during application clones.
- No arbitrary host shell fallback. The host fixture runner is restricted to hash-checked bundled fixtures and specific command forms.
- Non-root Docker user, capability drop, no-new-privileges, read-only input copy, disposable workspace, resource/time limits and network off by default.
- Schema-constrained docs-only repair targets, citation existence/range checks, unique patch matching, and fixed-target fresh verification.
- Scan safety filters and labelled-container cleanup after total deadlines.
- PR Guard token permissions split between read-only analysis and same-repository commenting. No committed PAT or secret.

## Limits and sensitive data

Repository files may already contain secrets. Inspect before cloning/execution; .env is excluded from runtime copies, but this is not comprehensive secret scanning. By default, selected source/configuration and logs go to the **local Ollama endpoint**. An operator may configure an HTTPS Ollama endpoint with `GHOST_OLLAMA_URL`; the app does not contact it for readiness or send repository data until the user checks the explicit remote-inference consent box. Remote calls receive selected onboarding docs, configuration excerpts, and trimmed failure logs, not the full checkout. Common secret-like strings in logs are redacted, but redaction is incomplete and cannot guarantee secrets are removed. Model input is untrusted and may contain prompt injection. Model responses can contain false diagnoses or dangerous instructions despite checks.

With network enabled, container commands may contact external services. No host environment secrets are intentionally passed, but malicious inputs and Docker vulnerabilities remain concerns. Model citations and high confidence are not security evidence. Logs/test markers can be forged by malicious code; a passing test is not a security certification.

The app has no user accounts, tenant isolation, production-grade scheduler, internet-facing authentication, or hardened cloud executor. Optional remote inference uses a configured server and bearer key, not a hosted executor. Repository cloning and Docker execution remain on the local PC. Do not expose port 8765 publicly or place it behind a public tunnel as a production service.

Runtime clones/reports and response caches persist locally. Inspect and remove them when no longer needed, especially before sharing a computer or archiving the source folder. They are Git-ignored and excluded from the initial repository upload.

## Reporting an issue

Report a reproducible issue through the repository's security reporting mechanism if available. If private reporting is unavailable, contact the maintainer through GitHub without posting secret values or working exploits publicly. No dedicated private security mailbox or response SLA is currently established.
