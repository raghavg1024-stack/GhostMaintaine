# Local HTTP API

These endpoints belong to the local application, not a public hosted API. Requests must use the local Host value for the configured `GHOST_PORT` (default 8765). POST requests require the current per-process token. Foreign Origin values are rejected. No CORS API is advertised.

## Routes

| Method / route | Purpose |
|---|---|
| `GET /` | HTML application |
| `GET /api/session` | Session token and Docker/Git executable availability (not engine/model health) |
| `POST /api/jobs` | Start one asynchronous analysis; 202 returns its ID |
| `GET /api/jobs/{id}` | Read running/done/error status |
| `GET /reports/{id}/{artifact}` | Allowlisted generated report/artifact under that job's result directory |

Example request, with a placeholder token obtained from the current `/api/session` response:

```http
POST /api/jobs
Content-Type: application/json
X-Ghost-Token: <session-token>

{"mode":"assist","url":"https://github.com/owner/repository","target":"python -m unittest discover -v","model":"qwen3:4b-instruct","network":false}
```

```json
{"id":"<16-hex-character-job-id>"}
```

## Inputs

| Field | Meaning |
|---|---|
| `mode` | `assist`, `check`, `ship`, `drift`, `matrix`, `bench-models`, or `scan`; API default is legacy `check`, browser default is `assist` |
| `url` | Public github.com root URL, required except benchmark/scan |
| `target` | Optional replacement fixed test command; no custom marker field |
| `model` | Optional installed Ollama name; assistant defaults to Qwen, legacy defaults to rules |
| `network` | Boolean container network opt-in |
| `matrix` | Comma-separated `py3.MINOR` environments |
| `models` | Comma-separated benchmark model names |
| `urls` | Scan list of 1–20 public GitHub URLs |

Benchmark mode uses `bench/labels.json`, not the URL field. Scan mode uses its URL list and the default scan success-target policy. Request size is limited to 8192 bytes. Only one web job is admitted at a time; a second receives 409.

## Job responses

```json
{"state":"running","message":"AI is reading onboarding docs...","mode":"assist"}
```

```json
{"state":"done","status":"needs_human","message":"Check complete.","report":"/reports/<id>/replay.html","duration":16.7}
```

Fields vary by mode. Git-backed jobs include a checked commit revision. `done` means analysis finished, not that setup succeeded. Setup statuses are `healthy`, `repaired`, `needs_human`, and `inconclusive`; static/aggregate modes can return `feature_complete`. An interrupted operation returns `state:error` and a message. Some invalid repair proposals become readable needs_human reports; invalid initial plans can still terminate with error.

Artifacts include replay.html, report.json, events.jsonl, verified README.patch/README.patched.md, matrix.html/matrix.json/version-note.patch, ship files, benchmark files, and scan files. Report routes resolve within the result directory and enforce a basename allowlist. Checkout files and arbitrary local paths are not served. Guessing an unknown job returns 404; invalid local request authorization returns 403.

No cancellation, history-list endpoint, streaming model tokens, persistent job index, remote authentication, or upload endpoint exists. Restarting clears the job index but not disk artifacts.
