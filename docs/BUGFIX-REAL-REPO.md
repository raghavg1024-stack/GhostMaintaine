# Real repository demo fixes

The Click demo exposed two GhostMaintainer bugs, not a demonstrated defect in Click.

* A plan with an unavailable source citation escaped as a job error. Plans now get one correction attempt, followed by an inconclusive report if still invalid. Rejected commands are never executed. The independent post-repair plan receives the same validation and cannot publish an unverified patch.
* A goal command using `python -m pytest` could fail because the selected image did not include pytest, but was reported as an ordinary failure. Its specific missing-runner log now produces `environment_blocked`, and the overall result is inconclusive. No dependency is installed implicitly, networking is not enabled, and no upstream documentation defect is inferred.
* Lowercase `docs/contributing.md` is included among supported contributor documents.

Additional checks reject installation commands absent from their cited documentation and classify dependency connection failures with container networking off as environment blocks.

Verification: all 32 tests passed with Docker in 53.567 seconds. The repeated Click verifier run completed in 12.9 seconds, returned inconclusive (missing pytest runner), and served its report with HTTP 200. The AI rerun also returned a report instead of crashing, but its invalid repair was rejected. No successful Click repair is claimed.
