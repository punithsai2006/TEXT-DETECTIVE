# Text Detective: integrated case workflow

All features use the existing FastAPI/React app and its existing navigation.
Evidence Search and Ask AI Assistant remain separate. No additional workspace,
agent framework, or database was introduced.

## Setup (PowerShell, repository root)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Create an investigation in Cases Directory, enter its name/description, upload
files in New Investigation, and run the pipeline. The same case ID scopes all
files, retrieval, graphs, hypotheses, answers, reviews and reports.

Server configuration: `LLM_PROVIDER`, `LLM_MODEL`, and `OPENAI_API_KEY` or
`ANTHROPIC_API_KEY` for the corresponding cloud adapter. `ollama` and `local`
adapters remain available when installed/configured. Keys stay backend-only.
`STORAGE_DIR` selects persistent storage. Set `DEMO_MODE=false` for normal use.
The normal analysis endpoint refuses a mock provider; it does not substitute
fixtures when a real provider fails. No generative model was downloaded.

PDF export adds the `reportlab` dependency. Cached local sentence embeddings
enable semantic retrieval; otherwise results explicitly identify lexical
TF-IDF/BM25 retrieval. `ALLOW_MODEL_DOWNLOADS=false` prevents automatic downloads.

## Implemented pipeline and persistence

Ingestion -> source spans -> schema-validated extraction -> conservative entity
resolution -> timeline -> source graph -> contextual comparison -> competing
hypotheses and deterministic scoring -> evidence verification -> model-written
report synthesis and verification.

The ten processing stages appear in the existing New Investigation panel.
Completed extraction batches, comparison pairs, hypothesis proposals,
assessments and verification results have case/source/model/configuration-bound
checkpoints. Retrying a failed stage reuses successful checkpoints. A completed
unchanged analysis reuses its run ID and does not call the model again. Source,
claim-correction, model or scoring changes require an appropriate new run.

Records live under `storage/cases/<case_id>` and originals under
`storage/uploads/<case_id>`. Raw extraction/comparison runs and reasoning
artifacts retain versions and action summaries. Analysis-run metadata is not
rewritten by review or repeat report generation. Review events are append-only
application history, not tamper-proof forensic records. Answers retain their
run ID, source fingerprint, provider/model, validation and usage records.

Supported inputs remain text, digital PDFs and the existing parsers. Blank or
partly unreadable PDFs show OCR warnings; OCR is not silently simulated. SHA-256
detects byte changes; it does not authenticate a source. PDF offsets are in
extracted text, not invented visual line numbers. Span IDs, exact quotes,
1-based PDF pages/paragraphs and extraction versions are retained. Answer-key
markers are checked after extraction as well as during upload; evaluator labels
are never indexed as evidence.

## Timeline, graph, search and questions

- Timeline descriptions open exact source passages. Event time/interval,
  document time, basis (reported/observed/logged/inferred), precision, timezone
  and uncertainty stay separate. Comparable timezone-aware times are ordered in
  UTC; uncertain events retain stable input order and an unordered label.
- Graphs contain document, claim, event and document-scoped entity nodes.
  Explicit person/organization/location/object mentions retain types; ambiguous
  names are not merged through similarity. Edges retain claim IDs, source IDs
  and potential-conflict links. Inspect nodes/edges, filter types, or focus on a
  hypothesis's connected claims. Red indicates a candidate conflict, not falsity.
- Evidence Search supports natural-language and exact-phrase retrieval, document,
  entity, event-date and evidence-type filters. Results expose original passages,
  filenames/locations, context and links to timeline/graph/comparisons. It needs
  no synthesis model. Unknown event dates are excluded by date filters; record
  dates are never substituted.
- Ask AI Assistant retrieves passages and graph-adjacent claims. Generic
  hypothesis questions also load persisted hypotheses' linked evidence, even
  without lexical matches. A bounded hypothesis agent can request more context.
  Answers do not regenerate the report. Substantive assertions require source
  IDs; existence, exact quotation and semantic support are checked separately.
  Unsupported assertions are withheld and missing evidence is stated.

## Hypotheses and scoring

The model proposes at most four competing explanations with necessary claims,
source references, assumptions and missing evidence. Each is investigated with
case-filtered retrieval, timeline/graph context and structured assessments.
Descriptions, support/opposition and constraints receive separate model support
verification. Unsupported assessments do not contribute to the score.

An unscored **insufficient evidence / other explanation** alternative is always
retained. A leading hypothesis is nullable. Ties, support/coverage below 0.6,
contrary evidence, negative constraints or unresolved assumptions prevent a
leader. Unknown feasibility contributes zero and remains visible; ranking is
not proof that an explanation occurred.

`SCORE_METHOD_VERSION=evidence-support-v3.0`. Default `SCORE_WEIGHTS`:

| Component | Normalized input | Weight |
|---|---|---:|
| Support | Necessary claims with verified support / distinct necessary claims | 4 |
| Conflict | Necessary claims with verified opposition / distinct necessary claims | -4 |
| Temporal | supported=1, conflicting=-1, unknown=0 | 1 |
| Relationships/access | supported=1, conflicting=-1, unknown=0 | 1 |
| Coverage | Necessary claims with any verified evidence / distinct necessary claims | 2 |
| Assumptions | min(distinct unresolved assumptions, 5) / 5 | -1 |

The final score is the deterministic sum of input x weight. The model cannot
supply the final number. Set the six weights as a JSON dictionary in
`SCORE_WEIGHTS`; method version and weights are persisted and changes invalidate
old current runs. No probability normalization occurs.

Canonical normalized exact quotation text defines a lineage. Copies in different
files and graph projections cannot increase support; duplicate necessary-claim
text is counted once. Text lineages are not asserted to be independently authored.
A log receives no automatic credibility bonus. Missing records do not prove
absence without established completeness. Every score is labelled:
**Evidence-support score — not a probability of guilt.**

## Summary and reports

`GET /api/cases/<id>/summary` returns the nested validated `CaseSummary` contract:
run/version details, cited summary, nullable leader, typed alternatives and score
components, comparisons/review states, timeline, unanswered questions and
limitations. Evaluation answer fields are not runtime output fields.

The existing Report page provides Generate Report, Preview Report, Markdown,
PDF and JSON. Report synthesis receives persisted findings/fixed scores; its
assertions are then checked against cited passages. Downloads render those
persisted assertions; they cannot silently change hypotheses or scores.
Mutable review decisions are rendered separately and remain consistent with the
comparison screen. Stale downloads are rejected until analysis is rerun.

Reports include details/version, executive summary and citations, all candidate
explanations/components, support/opposition/assumptions, review decisions,
detailed timeline, sourced relationships, a bounded PDF graph snapshot, exact
quotation appendix and unknowns. HTML/model/source strings are escaped; PDF
filenames use safe ASCII case IDs even for Unicode investigation names.

## Bounds and limitations

Raw analysis: 120 paragraphs / 120,000 characters; 40 candidate pairs per run;
24 model calls including retries; 180-second cooperative deadline. Reasoning:
at most 4 hypotheses, 6 necessary claims each, 30 model calls, 240 seconds.
Questions: 14 calls / 180 seconds. Structured requests get at most two attempts.
Initial hypothesis context is bounded to 80 claims/40 comparisons, with targeted
retrieval for additional context. Candidate blocking and bounded contexts can
miss conflicts or alternatives. Large cases may require explicit retries to
finish comparison checkpoints; a partial run is never labelled completed.

Provider HTTP timeouts apply; a deadline is checked before and after calls.
In-process local Transformers generation still lacks hard process cancellation.
Semantic verification is a model judgment and can be wrong. Fixture injection
tests do not establish prompt-injection resilience of a real model.

This remains a local, single-process prototype without authenticated multi-user
authorization, encryption at rest, parser isolation or production retention.
Do not expose it publicly or upload confidential evidence to an unapproved cloud
provider. OCR/audio, identity disambiguation beyond conservative mentions, and
restoring historical replaced-source viewers remain limitations. Stale citations
are not silently redirected to replacement files.

## Reproducible checks and demonstration

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe scripts/evaluate_case_workflow.py
.\.venv\Scripts\python.exe scripts/evaluate_evidence_review.py --real
.\.venv\Scripts\python.exe scripts/demo_evidence_review.py --fixture --port 8005
```

The fixture server is explicitly scripted, isolated in
`storage/review-fixture-demo`, and labelled in UI/exports. For a full manual test,
create a named synthetic investigation, upload `tmp/ui-workflow/witness.txt` and
`record.txt`, run analysis, inspect Timeline and Graph, inspect all three hypothesis
outcomes, search `archive door was locked` in exact mode, ask which hypothesis is
best supported, accept a finding as a lead with notes, then preview/download the
report. Restart and reopen the case to check persistence.

To reproduce without temporary files, create `witness.txt` containing
`At 2026-11-01 20:00 UTC, the archive door was locked.` and `record.txt`
containing `At 2026-11-01 20:00 UTC, the archive door was open.` These exact
synthetic passages are recognized by the explicit test-fixture provider.

The exported fixture PDF is a rendering/demo artifact, never a real-model result:

```powershell
.\.venv\Scripts\python.exe scripts/demo_evidence_review.py --fixture --no-serve --export output/pdf/text-detective-fixture-report.pdf
pdftoppm -r 90 -png output/pdf/text-detective-fixture-report.pdf tmp/pdfs/fixture-report
```

Actual test/evaluation/browser results are recorded in `WORKFLOW_VERIFICATION.md`.
