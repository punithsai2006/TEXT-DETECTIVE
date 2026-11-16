# Source-linked review implementation status

Superseded by [current workflow](CASE_WORKFLOW.md) and
[actual verification results](WORKFLOW_VERIFICATION.md). Earlier delivery notes
below are historical; the current path uses competing-hypothesis scoring.

## Current integration update

The separate Evidence Review page/sidebar item has been removed. The original
New Investigation action now invokes source-backed extraction, contextual
comparison, the retained Hypothesis Scoring stage and the existing dossier.
The same run populates the original Timeline, Contradictions, Graph, Evidence,
Q&A, Agents and Report pages. Documents contains attributed claims/corrections;
source inspection is a shared popup in the existing cards. Old `/review` bookmarks
redirect to Documents. Processing status uses actual backend values rather than
simulated completion. Earlier delivery notes below describe the initial separate
workspace and are superseded by this integration update.

Integration validation: final full suite **95 passed, 1 warning in 24.57s**; targeted
evidence tests **29 passed**. The expanded API integration test executes the
existing `/analyze`, hypothesis, graph, contradiction-review, Q&A and report-export
contracts, verifies shared decisions, and rejects stale approvals. Frontend
TypeScript/Vite build passed in 12.79s (existing bundle-size warning). Browser
checks confirmed the original six-stage Run Full Investigation flow, the
existing Report source popup, and the existing interactive Graph canvas with
four nodes/two sourced edges. No separate Evidence Review navigation item is
present. These checks used the explicitly labelled synthetic fixture server. Real inference
remains unverified because provider credentials are not configured.

## Baseline (2026-11-16)

Inspected FastAPI routes, React routing/context, JSON case storage, ingestion,
hybrid retrieval, schema models, provider adapters, tests and saved benchmarks.
No AGENTS.md was found in the repository. Working tree was initially clean.

Existing: upload and case CRUD, rule/model-assisted extraction, timelines, graph,
hybrid retrieval with optional dense models, JSON reports, review fields,
mock/OpenAI/Anthropic/Ollama/local-transformers adapters.

Gaps: page-preserving evidence spans, versioned claims, conservative comparison,
append-only review/correction records, bounded auditable tool decisions, and
separate locator/quote/support validation. Legacy pages retain legacy behavior
until explicitly migrated; the new Evidence Review page is the v2 workflow.

Architecture: retain FastAPI/React, existing case/document persistence and
retriever/provider adapters. Add versioned source spans to documents and an
evidence-review service with immutable per-run snapshots and append-only events.
No additional agent framework or database. The prototype is single-process and
local-user only; case scoping is not a substitute for authentication.

Baseline commands/results:
- `python -m pytest -q`: blocked, system Python 3.14 has no pytest.
- Installed root `requirements.txt` into `.venv` after approved network access.
- Untouched `HEAD` snapshot in `.baseline-check`: `..\.venv\Scripts\python.exe
  -m pytest -q` passed **66 tests in 54.30 seconds**.
- Baseline `npm.cmd run build` in `frontend`: passed; existing large-chunk warning.

## Delivered

- Versioned exact source spans for text/digital PDFs; original hashes and unique
  original storage names; page preservation; empty/missing-page warnings.
- `/review` React workspace and case-scoped FastAPI endpoints for run/source/
  original/report/review/question access. Original downloads verify hashes.
- Structured attributed claims/entities, reported event timeline, and persisted
  document-scoped mention/claim graph with evidence references.
- Context-aware candidate comparisons within/across documents. No automatic
  confirmed-conflict label or fabricated confidence percentage on the v2 path.
- Bounded provider-backed extraction/comparison/verification. A model-selected
  context retrieval tool call precedes comparison when requested. Actions, run
  versions, usage, errors and limits persist; no arbitrary external tool access.
- Case-filtered original-span RAG with claim adjacency expansion. Locator,
  quotation and semantic support checks are separate; unsupported answers abstain.
- Append-only review/correction records; corrections or source replacement,
  deletion, and external original-byte changes invalidate old approvals/runs.
- Existing architecture/provider adapters retained; explicit fixture-only server,
  evaluation command and operating guide added. Automatic embedding downloads
  default off; v2 does not create a redundant Chroma index.
- Related security fixes: preserve originals during failed replacement batches,
  prevent case-deletion traversal, and prevent the SPA file route serving above
  its frontend distribution directory.

## Actual final checks (2026-11-16)

- `.\.venv\Scripts\python.exe -m pytest -q`: **95 passed, 1 warning in 53.14s**.
  The warning is Starlette's deprecation of httpx-backed TestClient in the newly
  installed dependency versions. No test was skipped to obtain this result.
- FastAPI TestClient initially stalled inside Python's Windows loopback socketpair
  before reaching app code under the restricted sandbox. Re-running with approved
  local socket access completed the full suite. Stalled test processes were stopped.
- New coverage: text/PDF exact offsets and pages, blank scans, repeated spans,
  within/across-document conflicts, compatible accounts, time/context/identity/
  hearsay/unit safeguards, retrieval isolation, citation tampering, original-byte
  changes, append-only history, corrections, stale reviews, abstention, retries,
  provider HTTP contracts, upload rollback, traversal, and full fixture API flow.
- `scripts/evaluate_evidence_review.py --real`: **12/12 deterministic safeguard
  checks passed**, including **5 deliberate deferrals**. Real-model evaluation
  blocked by mock configuration; `model_metrics` is **null**. This is not a
  contradiction-accuracy or real-model benchmark.
- Browser interactions against the explicit synthetic fixture server verified
  the rendered review page, exact-source viewer, saved `accept_lead` decision,
  cited answer and unanswerable-question abstention. The browser session dropped
  once and was recovered. This was accessibility-state interaction verification,
  not a screenshot-based responsive-layout audit or real inference.
- `git diff --check`: passed before final documentation updates.
- Final `npm.cmd run build` in `frontend`: passed (existing >500 kB bundle
  warning); TypeScript and Vite compilation completed. The new source viewer
  uses Unicode code-point slicing to match Python's extracted-text offsets.

## Blocked/deferred

Configured provider is `mock`; OpenAI/Anthropic key-presence checks were both false.
No secret values were inspected or printed. Real provider request shapes were
tested with intercepted HTTP responses, not actual cloud calls. See
`EVIDENCE_REVIEW_V2.md` for configuration and the explicit `--real` command.

Real extraction/retrieval/semantic-support/timeline benchmark metrics and
controlled ablations remain outstanding. OCR/audio/image interpretation are
deferred. Legacy analytics/report pages have not been migrated; their safety and
benchmark claims do not apply to v2. Local single-process storage is not a
production authorization or tamper-proof audit system.

Automatic approval review rejected recursive cleanup of the generated
`.baseline-check` snapshot because it contains a full project tree. It remains
intact and is ignored by Git; no alternate deletion method was attempted.
