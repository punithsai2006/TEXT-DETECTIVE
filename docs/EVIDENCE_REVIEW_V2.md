# Integrated evidence-grounded pipeline

Current workflow, scoring and setup: [CASE_WORKFLOW.md](CASE_WORKFLOW.md).
Actual latest checks: [WORKFLOW_VERIFICATION.md](WORKFLOW_VERIFICATION.md).
The notes below retain earlier implementation context.

The new evidence features are merged into the existing FastAPI/React application.
Start in **New Investigation** and use the original Documents, Timeline,
Contradictions, Hypotheses, Graph, Agents, Q&A and Report pages. There is no
separate Evidence Review sidebar item; `/review` redirects to Documents for old
bookmarks. Outputs are attributed accounts and reviewable suggestions, never
findings about guilt or actual truth. Existing benchmark claims are not validation
of the new model-assisted workflow.

## Setup and normal execution (PowerShell, repository root)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/new`. Create/select a case, upload `.txt` or digital
`.pdf` files, and run the existing investigation pipeline. The normal endpoint deliberately refuses
mock inference and persists a failed run explaining why. Source viewing works
without a model. Existing `.docx`/log upload support remains; v2 verification
focuses on text/digital PDF.

Use server environment variables or `backend/.env` (never commit secret values):

```text
LLM_PROVIDER=openai | anthropic | ollama | local | mock
LLM_MODEL=<model available to your account or installed locally>
OPENAI_API_KEY=<server-only, for OpenAI>
ANTHROPIC_API_KEY=<server-only, for Anthropic>
DEMO_MODE=false
STORAGE_DIR=storage
```

`ollama` uses the existing loopback Ollama adapter; `local` requires the existing
optional Transformers dependencies and a cached instruction model. This change
does not download a generative model. `MODEL_ASSISTED_ANALYSIS` controls the
legacy pipeline; the explicit v2 run uses its configured provider directly.
Optional Sentence Transformers can supply dense retrieval; the existing lexical
fallback is recorded as such. These are retrieval methods, not generative mocks.
`ALLOW_MODEL_DOWNLOADS=false` is the default: install/cache an embedding model
explicitly before using dense retrieval. V2 skips redundant Chroma persistence.

## Reproducible fixture demonstration

```powershell
.\.venv\Scripts\python.exe scripts/demo_evidence_review.py --fixture --port 8005
```

Open `http://127.0.0.1:8005/new`. This **explicitly scripted fixture server**
uses isolated `storage/review-fixture-demo`, two synthetic files and no real LLM.
It injects the test provider only into this server; production endpoints have
no request option to enable fixtures. Never upload private case material to a
fixture demonstration or present its outputs as model performance.

Walkthrough:
1. Select `FIXTURE ONLY — Archive door review`.
2. Run the existing six-stage investigation, including Hypothesis Scoring.
3. In Documents, inspect attributed claims and click **Inspect exact source**.
4. Inspect the exact quote, `[start,end)` offsets and original download.
5. In Contradictions, compare the locked/open accounts and their assumptions.
6. Add a note and choose **Accept as Investigative Lead**, or mark variance.
7. In Ask AI Assistant, ask `What state was the archive door in?` for a cited answer.
8. Ask `Who opened the archive door?` to see explicit abstention.
9. In the existing Agents screen, inspect the action log: the contradiction agent chose context retrieval before
   comparison; the evidence tool searched passages and claim adjacency.
10. Correct a claim in Documents or replace a source: previous runs/reviews become stale;
    rerun analysis. Export Markdown or JSON from the existing Report page.

The fixture classifier and support checker are scripted. The walkthrough proves
wiring and persistence; it says nothing about real-model accuracy.

## Evidence and persistence conventions

- Originals are retained under unique storage names, separate from display
  filenames. SHA-256 detects byte changes, not authenticity.
- `raw_text` preserves extracted page boundaries (`\f`); `cleaned_text` is a
  separate analysis representation. No unreadable-PDF placeholder is indexed.
- Span version depends on parser version, original hash and extracted text.
  IDs include document/version/offsets. Paragraphs are 1-based per page; PDF
  pages are 1-based viewer pages. Offsets are 0-based, end-exclusive Python
  character offsets in **extracted text**, not PDF visual coordinates or lines.
- Empty PDF pages generate warnings, and blank PDFs have zero source spans.
  Legacy PDFs must be re-uploaded because their original page map was discarded.
- Run snapshots persist model/provider, prompt/parser versions, source hashes,
  extraction versions, actual retrieval method, limits, actions, usage and
  failures in `cases/<case>/evidence_review/run_*.json`.
- Claims preserve negation, attribution, reported/record times, intervals,
  timezone, approximation, units, clock uncertainty and source span IDs.
- Graph entity mentions are document-scoped. Exact name links retrieve related
  claims but do not prove identity or independent corroboration.
- Review/correction events use new files under `evidence_review/events`; earlier
  events are not overwritten. Reviewer labels are self-reported, not authenticated.
  Corrections apply to matching claims on subsequent runs and invalidate old
  approvals. Sources changing marks all dependent runs stale conservatively.
- Answers and verification actions persist under `evidence_review/answers`.
  Locator existence, exact quotation and semantic support are separate checks.
  Semantic support is another model judgment, not a proof or calibrated score.

## Bounded roles

Evidence agent: schema-validated extraction plus case-filtered passage search
and exact-subject claim-graph expansion. Contradiction agent: model selects
`retrieve_context` or `compare`, with at most one context tool invocation per
candidate, then returns a structured contextual assessment. Verification/reporting
agent: generates attributed answer assertions and separately checks support
against their cited sources; unsupported assertions are withheld.

No arbitrary shell/network tool is available to the model. Evidence content is
JSON data beneath a fixed system instruction. This boundary and least privilege
reduce consequences of injection; they do not establish real-model resistance.

Limits: 120 source paragraphs / 120,000 extracted characters; 40 candidate pairs;
24 model calls including retries per analysis; at most two attempts per structured
request. Answers have 10 calls. Analysis/answer deadlines are 180/120 seconds,
checked before calls and on return. Provider HTTP timeouts also apply (existing
remote adapters: 45 seconds; Ollama: 120 seconds). Local in-process Transformers
generation cannot be forcibly cancelled; hard worker-process termination is a
remaining production requirement. A deadline/budget failure is explicit and
never labelled completed. Remaining unprocessed candidates yield a partial run.

## Checks and evaluation

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/evaluate_evidence_review.py
.\.venv\Scripts\python.exe scripts/evaluate_evidence_review.py --real
npm.cmd --prefix frontend run build
```

`--real` uses the configured provider and may incur usage charges. Without a
non-mock available provider it writes `model_metrics: null` and a blocked status.
Gold labels live only in the evaluation script, outside ingestion. Default
evaluation measures deterministic safeguards and intentional deferral, not LLM
accuracy. The 12 pairs are a manually authored pilot, not a genuinely unseen
held-out corpus. Matching policy, counts, per-case outcomes and unmeasured
metrics are included in the JSON result. Extraction/entity F1, retrieval Recall@k,
human semantic-support labels, comparable timeline-pair accuracy and controlled
LLM-only/RAG/graph/verification ablations remain unmeasured.

Actual execution results are in `NEXT_VERSION_STATUS.md`.

## Remaining limits

Real inference was not verified: installed configuration is mock and no cloud
provider keys are present. HTTP adapter tests use intercepted requests, not real
provider responses. Entity resolution/coreference remains conservative; exact
subject/predicate or event-scope candidate blocking can miss paraphrases and
aliases. No calibrated confidence scores are shown. Model extraction and support
checks can both be wrong. Original downloads verify current file hashes; stale
sources are not silently resolved against replacement files.

The graph is persisted as nodes/edges and displayed in the existing interactive
canvas; claim-node details open exact source passages. This is a single-process,
local-user prototype: no authenticated case authorization, encrypted storage,
tamper-proof audit log, cross-process transaction isolation, parser sandbox or
production backup/retention policy. Do not expose it publicly or use confidential
case data without those controls. Optional OCR, image analysis, ASR and diarization
are deliberately deferred until real-model core evaluation is available.

## Existing feature integration

The existing `/cases/<id>/analyze` endpoint now orchestrates the evidence service
and publishes the same run into the existing extraction, contradiction, timeline,
graph, hypothesis, report and run-record contracts. Existing Q&A/review/export
endpoints use the current source-backed run. Hypothesis Scoring retains its
existing formula and lexical heuristic, with explicit uncertainty; a top-ranked
account is not designated as an established explanation. Pre-upgrade cases remain
readable, but require rerunning to receive the new analysis. Older benchmark
results and old automatically generated narratives are not upgraded by relabeling.
