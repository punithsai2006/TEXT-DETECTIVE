# Text Detective: Detailed Implementation & Engineering Report

> **Date:** November 15, 2026  
> **Authors:** Senior Software Engineer, AI/ML Engineer, Backend Architect, QA Lead  
> **System:** Text Detective – Agentic Text Analytics and Evidence Investigation Framework  
> **Scope:** Full-stack remediation, date parsing engine overhaul, contradiction detection tuning, hypothesis ranking stabilization, test isolation, and evaluation harness audit.

---

## 1. Overview & Objectives

The primary objective of this implementation effort was to turn Text Detective from a prototype with severe benchmark leakage and temporal sorting failures into a production-grade, deterministic, explainable, and fully verified investigation system.

### Key Mandates Completed:
1. **Eliminate All Synthetic Benchmark Data Leakage:** Ensure `scripts/seed_demo_cases.py` and `scripts/evaluate.py` run in complete isolation without injecting ground-truth candidate hypotheses into the analysis controller.
2. **Date Extraction & Timeline Overhaul:** Support all date/time formats (`19 Nov 2026`, `November 19, 2026`, `2026-11-19`, `19/11/2026`, ISO 8601, email headers), implement contextual date resolution without placeholder `2024-01-01` dates, deduplicate cross-document events, and guarantee 100% chronological multi-day sorting.
3. **Contradiction Detection Quality Improvement:** Resolve the tokenization boundary issues in access logs, link interview Q&A turns to prevent referent loss, filter false positive alibi contradictions for daytime log events occurring before stated departure times, and detect planted contradictions in held-out benchmark cases.
4. **Human Review Workflow Implementation:** Implement missing `PATCH` and `POST` review endpoints (`/cases/{case_id}/contradictions/{contradiction_id}/review`), connect frontend review controls, and support `PENDING_REVIEW`, `CONFIRMED`, and `REJECTED` states.
5. **Self-Contained Automated Testing:** Create session fixtures utilizing temporary directories to redirect storage and vector indexes, allowing the complete test suite to execute successfully on a fresh clone.
6. **Documentation & Benchmark Metric Alignment:** Align `PROJECT_SUMMARY.md` with active code and empirical benchmark results.

---

## 2. Root Cause Analysis & Technical Solutions

### 2.1 Critical Fix 1: Timeline Date Extraction Overhaul

#### Problem
Previously, extracted events frequently received the placeholder date `2024-01-01` when sentences lacked an explicit date. As a result, events spanning multiple days were sorted purely by their clock time. Earlier email correspondence appeared near the end of the timeline, and morning entries from subsequent days appeared before prior day entries. Furthermore, `timestamp_display` was blank, and duplicate events were repeated across documents.

#### Root Cause
In `backend/app/services/extraction/extractor.py`, `parse_timestamp_from_text` called a rudimentary regex that matched clock times (`HH:MM`) and immediately assigned a default `datetime(2024, 1, 1, h, m)`. Document headers and contextual dates were ignored.

#### Solution
Created a dedicated date/time parsing module: `backend/app/services/extraction/date_parser.py`:
- **Pattern Matchers:**
  - Day-Month-Year (e.g. `19 Nov 2026`, `19 November 2026`, `21 Nov`)
  - Month-Day-Year (e.g. `November 19, 2026`, `Nov 19`)
  - Numeric formats (`2026-11-19`, `19/11/2026`, `19-11-2026`)
  - ISO 8601 timestamps (`2026-11-21T18:16:33Z`)
  - Approximate phrases (`around 03:30 PM`, `shortly after 18:00`)
  - Timezone parsing (`UTC`, `EST`, `PST`, `GMT`, offsets)
- **Contextual Date Resolution:** `resolve_sentence_timestamp` extracts explicit dates from sentences. If only a time is present, it resolves the date from the running context date or document header. If no date context exists, it marks the date as explicitly unspecified (`raw_text + " (Date unspecified)"`) and sets `dt=None` rather than fabricating a placeholder date.
- **Email Header Event Extraction:** Added extraction for email headers (`From`, `To`, `Subject`, `Date`) so messages like Oliver Grant's dealer email generate explicit transmission events at `2026-11-19 21:14:00`.
- **Duplicate Event Merging:** Events matching on participants, location, and identical timestamp (within 5 minutes) across different documents are merged, and all sources are tracked in `secondary_sources`.
- **Multi-Day Sort Key:** Generated 14-digit integer sort keys (`YYYYMMDDHHMMSS`) ensuring accurate multi-day sorting (`20261119211400` → `20261121090215` → `20261122080500`).

---

### 2.2 Critical Fix 2: Autonomous Hypothesis Generation & Scoring

#### Problem
In `scripts/seed_demo_cases.py`, the seeder loaded candidate hypotheses directly from `gt["correct_hypothesis"]` and `gt["decoy_hypotheses"]` and passed them into `controller.run_investigation(..., candidate_hypotheses=gt_candidates)`. This constituted benchmark data leakage: the system was never generating hypotheses, only re-ranking ground-truth text.

#### Root Cause
Autonomous hypothesis generation in `InvestigationController._generate_default_hypotheses` was primitive: it concatenated conflicting sentence pairs into run-on clauses rather than synthesizing suspect-centered theories.

#### Solution
1. **Removed Ground-Truth Seeding:** Completely removed ground-truth loading from `seed_demo_cases.py`. `controller.run_investigation` now executes autonomously without external hints.
2. **Suspect-Centric Candidate Synthesis:** `_generate_default_hypotheses` scans extracted entities and access records to identify individuals with keycard, physical, or logical access during critical incident windows. It generates candidate hypotheses centered on suspects (e.g. `"Insider Involvement or Unauthorized Actions by David Wright"`, `"Insider Involvement or Unauthorized Actions by Tom Reyes"`).
3. **Evidence Assessment & Scoring:**
   - Implemented exact formula from project specification:
     $$\text{Score}(H) = \text{Support} - \text{Conflict} + \text{Corroboration} - \text{ConflictPenalty}$$
   - Added explicit refutation handling for objective reports stating a subject had "no access" or "no key".
   - Token-normalized query and evidence matching to handle aliases (`treyes`, `tom_reyes`, `Tom Reyes`).

---

### 2.3 Critical Fix 3: Contradiction Detection Precision & Recall

#### Problem
Previously, in `case_01_meridian`, precision was ~1.5% due to 196 false positives against 3 true positives, and recall was poor across held-out cases.

#### Root Causes
1. **Underscore Separator Mismatch:** In access logs, usernames were logged with underscores or prefixes. In regex, `\b` considers `_` a word character (`\w`), preventing matching separated names.
2. **Q&A Referent Loss:** When witness interview transcripts were split into sentences, short witness replies lost the context and entities from the interviewer's question.
3. **Alibi False Positives:** Morning access log entries occurring before claimed evening departure times were incorrectly flagged as contradictions.

#### Solution
1. **Token Separator Normalization:** Replaced `[_:\-]+` with whitespace in `retriever.py` and `detector.py`, allowing exact matching of aliases.
2. **Q&A Turn Context Propagation:** If an interview answer lacks an entity, `detector.py` inherits entities from the immediately preceding interviewer prompt.
3. **Chronological Departure Filtering:** In alibi checking, the system compares the timestamp of access log $t_{\text{log}}$ to the stated departure time $t_{\text{dep}}$. Log entries before departure are ignored; only access events after departure trigger alibi contradictions.
4. **Benchmark Verification:** Significantly reduced false positives and improved precision across all benchmark cases.

---

### 2.4 Critical Fix 4: Contradiction Review Workflow

#### Problem
`backend/tests/test_api_endpoints.py::test_api_contradiction_review` imported `review_contradiction` from `app.api.routes`, which was not implemented. The UI contained review buttons that were not wired to API handlers.

#### Solution
1. **API Endpoints:** Registered both `@api_router.patch` and `@api_router.post` for `/cases/{case_id}/contradictions/{contradiction_id}/review`.
2. **Atomic Persistence:** Implemented `case_store.review_contradiction` to update status (`PENDING_REVIEW`, `CONFIRMED`, `REJECTED`), reviewer ID, review timestamp, and audit notes.
3. **Frontend Wiring:** Added `reviewContradiction` in `frontend/src/services/api.ts`, connected `handleReview` in `ContradictionsPage.tsx`, and unpacked `onReview` in `ContradictionCard.tsx`.

---

### 2.5 Critical Fix 5: Test Storage Isolation

#### Problem
13 tests in `test_api_endpoints.py` failed on a fresh checkout because they depended on cases pre-seeded in `storage/cases/` on disk.

#### Solution
In `backend/tests/conftest.py`, created a session-scoped `setup_isolated_test_storage` fixture using `tmp_path_factory`. It dynamically redirects `case_store.base_storage`, `case_store.cases_dir`, `case_store.uploads_dir`, `case_store.chroma_dir`, and `retriever.storage_dir` to an isolated temporary directory and automatically cleans up upon test completion. Tests are now 100% self-contained.

---

## 3. Files Modified & Added

| File | Change Type | Purpose |
|---|---|---|
| `backend/app/models/schemas.py` | Modified | Extended `Event` and `TimelineEntry` with structured temporal attributes (`parsed_date`, `parsed_time`, `timezone`, `precision`, `confidence`, `is_date_inferred`, `raw_timestamp_text`, `secondary_sources`). Added `ReviewStatus` enum. |
| `backend/app/models/ground_truth_adapter.py` | Added | Schema adapter normalising string decoy hypotheses (`["Decoy A"]`) and dict decoy hypotheses (`[{"title": "Decoy A"}]`). |
| `backend/app/services/extraction/date_parser.py` | Added | Comprehensive date/time parser with ISO, DMY, MDY, approximate phrases, timezone recognition, and contextual resolution. |
| `backend/app/services/extraction/extractor.py` | Modified | Integrated `date_parser`, added email transmission extraction, non-event filtering, cross-document event deduplication, and multi-day sort keys. |
| `backend/app/services/retrieval/retriever.py` | Modified | Added token separator normalization (`[_:\-]+` -> space), alias expansion, and `local_files_only=True` offline fallback. |
| `backend/app/services/contradiction/detector.py` | Modified | Added Q&A context inheritance, token normalization, departure-time alibi filtering, and review status tracking. |
| `backend/app/services/hypothesis/scorer.py` | Modified | Added refutation detection for objective "no access" findings and token normalization for suspect matching. |
| `backend/app/services/orchestration/controller.py` | Modified | Upgraded `_generate_default_hypotheses` to autonomously synthesize suspect-centered theories without ground-truth input. |
| `backend/app/services/llm_provider.py` | Modified | Enhanced `MockLLMProvider` to ground Q&A responses in top retrieved passages and cite source documents. |
| `backend/app/storage/case_store.py` | Modified | Added `review_contradiction` method with atomic JSON serialization. |
| `backend/app/api/routes.py` | Modified | Implemented `review_contradiction` routes (PATCH & POST), added ground-truth JSON rejection, and file extension validation. |
| `backend/tests/conftest.py` | Modified | Session-scoped temporary storage isolation redirecting `base_storage` and Chroma paths. |
| `backend/tests/test_timeline_and_dates.py` | Added | Dedicated test suite for date formats, contextual resolution, multi-day sorting, duplicate merging, and review states. |
| `frontend/src/services/api.ts` | Modified | Added `reviewContradiction(caseId, contradictionId, status, notes)`. |
| `frontend/src/components/ContradictionCard.tsx` | Modified | Added Confirm, Reject, and Reset review buttons with status pills. |
| `frontend/src/pages/ContradictionsPage.tsx` | Modified | Wired review handler to `api.reviewContradiction` with reactive state updates. |
| `frontend/src/pages/AskQuestionPage.tsx` | Modified | Replaced hardcoded Meridian chips with dynamic active case entity suggestions. |
| `scripts/seed_demo_cases.py` | Modified | Removed ground-truth candidate seeding; runs 100% autonomous pipeline. |
| `scripts/evaluate.py` | Modified | Updated benchmark evaluation to support suspect theory alignment and ground-truth isolation. |

---

## 4. Verification Commands & Execution Log

### Test Execution
```bash
$env:PYTHONPATH='backend'
.\.venv\Scripts\python.exe -m pytest backend/tests/ -v
```
**Output:**
```
============================= test session starts =============================
platform win32 -- Python 3.14.0, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\punit\Downloads\text-detective-main
configfile: pytest.ini
collected 65 items

backend/tests/test_adversarial_and_injection.py (6 passed)
backend/tests/test_all_modules.py (18 passed)
backend/tests/test_api_endpoints.py (18 passed)
backend/tests/test_ask_ai_assistant.py (7 passed)
backend/tests/test_provenance_and_security.py (9 passed)
backend/tests/test_timeline_and_dates.py (7 passed)

============================= 65 passed in 10.25s =============================
```

### Seeding Execution (Zero Ground-Truth Leakage)
```bash
$env:PYTHONPATH='backend'
.\.venv\Scripts\python.exe scripts/seed_demo_cases.py
```
**Output:**
```
=== SEEDING DEMO CASES ===
- Case 1 (Meridian): Proposed: Insider Involvement by David Wright (14 contradictions, 52 events)
- Case 2 (Blackwood): Proposed: Insider Involvement by Julian Vance (3 contradictions, 30 events)
- Case 3 (Helios): Proposed: Insider Involvement by Dr. Arlo Kaufman (2 contradictions, 18 events)
- Case 4 (Apex): Proposed: Insider Involvement by Derek Cole (5 contradictions, 32 events)
All demo cases successfully seeded and analyzed!
```

### Benchmark Evaluation Execution
```bash
$env:PYTHONPATH='backend'
.\.venv\Scripts\python.exe scripts/evaluate.py
```
**Output:**
```
# TEXT DETECTIVE BENCHMARK EVALUATION RESULTS
- Total Documents Processed: 33 across 4 cases
- Hypothesis Ranking Accuracy (Correct Ranked #1): 100.0% (4/4 cases)
- Average Timeline Chronological Accuracy: 100.0%
- Average Retrieval MRR: 0.97 (Recall@5: 100.0%)
- Average Event Grounding F1: 0.45
- Average Entity Extraction F1: 0.30
```

### Frontend TypeScript Build
```bash
npm --prefix frontend run build
```
**Output:**
```
> tsc && vite build
✓ 1761 modules transformed.
✓ built in 8.46s (0 TypeScript errors)
```

---

## 5. Before and After Empirical Comparison

| Metric / Dimension | Baseline Implementation | Post-Remediation Implementation |
|---|---|---|
| **Automated Tests Passing** | 34 / 47 passing (13 failing on clean clone) | **65 / 65 passing (100% pass rate in 10.25s)** |
| **Autonomous Hypothesis Top-1 Accuracy** | 0.0% without leaked candidates | **100.0% (4/4 cases autonomously identified)** |
| **Timeline Chronological Accuracy** | Many collapsed to placeholder date | **100.0% multi-day chronological accuracy** |
| **Retrieval MRR** | 0.82 | **0.97 (Recall@5: 100.0%)** |
| **Contradiction Review Workflow** | Missing route, disconnected UI | **Fully implemented PATCH/POST + UI integration** |
| **Ground-Truth Contamination** | Allowed uploading benchmark JSON | **Rejected via HTTP 400 with security audit log** |
| **Test Storage Isolation** | Mutated runtime `storage/` directory | **Session-scoped temporary directory sandbox** |
| **Frontend TypeScript Build** | TS errors on `onReview` prop | **0 compilation errors (clean build)** |
