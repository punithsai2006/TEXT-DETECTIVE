# Text Detective: Comprehensive File-by-File Code Review

> **Review Date:** November 1, 2026  
> **Review Scope:** All backend services, data models, storage layers, REST API routes, frontend pages, components, test suites, and evaluation scripts.  
> **Prioritization Schema:** Critical (Security/Data Integrity) > High (Algorithm/Logic Correctness) > Medium (Usability/Reliability) > Low (Documentation/Style).

---

## 1. Backend Source Code Review

| File Path | Purpose | Status | Findings | Recommendation | Priority |
|---|---|:---:|---|---|:---:|
| `backend/app/main.py` | FastAPI application initialization, lifespan, middleware (rate limiting, CORS, global exception handler). | Complete | CORS origin array currently includes wildcard `"*"` alongside specific localhost origins, which is flagged when `allow_credentials=True`. | Restrict `allow_origins` strictly to local dev ports (`http://localhost:5173`, `http://127.0.0.1:5173`, etc.). | **High** |
| `backend/app/config.py` | Application settings loaded from `.env` via `pydantic-settings`. | Complete | Correctly loads settings with defaults for `mock` provider and local storage paths. | None. Ensure `.env` is omitted from version control. | Low |
| `backend/app/api/routes.py` | Primary REST API router providing 26 endpoints for cases, documents, runs, evidence, graph, and reports. | Complete | Upload endpoint processes files sequentially; if file 3 of 5 fails, files 1 and 2 remain on disk without rollback. | Implement atomic batch upload handling: clean up partially uploaded files if any item in the batch fails validation. | **High** |
| `backend/app/models/schemas.py` | Pydantic v2 schemas defining all data objects (Entities, Events, Timeline, Contradictions, Hypotheses, Provenance, Runs). | Complete | ContradictionItem lacks an explicit `detection_engine` field (`nli`, `rules`, or `llm_verified`) as required by project specifications. | Add `detection_engine: str = "rules"` to `ContradictionItem` model. | **High** |
| `backend/app/storage/case_store.py` | File-system-based persistence for cases, extraction, contradictions, hypotheses, reports, and run records. | Complete | File writes use standard `open(..., 'w')`. Concurrent writes or interruptions could lead to corrupted JSON. | Implement atomic file writing using a temporary file and `os.replace` to safeguard case JSON files. | **Medium** |
| `backend/app/services/ingestion/preprocessor.py` | Document ingestion for TXT, PDF, DOCX, CSV, LOG, and JSON; sentence splitting and chunking. | Complete | Empty files or scanned PDFs without text throw generic errors. | Add explicit detection for zero-byte files and clear warning when a scanned image PDF without OCR text is uploaded. | **Medium** |
| `backend/app/services/extraction/extractor.py` | Extracts entities, actions, temporal strings, builds chronological timeline, and constructs NetworkX case graph. | Complete | Rule-based extraction is robust; handles names, orgs, locations, objects, and ISO/12hr timestamps with uncertainty flags. | Keep high precision rules and ensure all source sentences are preserved in graph edges. | Low |
| `backend/app/services/retrieval/retriever.py` | Case-isolated hybrid evidence retrieval combining dense SentenceTransformers embeddings, TF-IDF, and Reciprocal Rank Fusion. | Complete | ChromaDB persistent collection is initialized alongside an offline fallback vector index. Case isolation is strictly enforced. | Expose active embedding provider name in evidence metadata for transparency. | Low |
| `backend/app/services/contradiction/detector.py` | Cross-document statement comparison for agreements and contradictions. | Partial | `_get_nli_pipeline()` is defined with `roberta-large-mnli`, but `evaluate_pair()` directly relies on regex rules without attempting NLI or recording `detection_engine`. | Wire `_get_nli_pipeline()` to attempt NLI first if available; fall back to conflict rules; invoke LLM judge on borderline cases; record `detection_engine`. | **High** |
| `backend/app/services/hypothesis/scorer.py` | Implementation of the exact Slide 18 hypothesis scoring formula: `Score = Support - Conflict + Corroboration - ConflictPenalty`. | Complete | Formula correctly calculated; claim decomposition implemented; handles ties with uncertainty notices. | Explicitly enforce heuristic ranking disclosure in all generated explanations. | Low |
| `backend/app/services/orchestration/controller.py` | Central Controller Agent managing module execution and 3 feedback loops (Evidence, Clarification, Additional Analysis). | Complete | Maximum iteration count (2) is enforced; logs all feedback loop triggers to `audit_log.json`; SHA-256 document hashing recorded. | Add structured audit log inspection to API and UI. | **Medium** |
| `backend/app/services/provenance/provenance_validator.py` | Audits timeline events, contradictions, hypothesis claims, and report source citations against document texts. | Complete | Validates document existence, sentence indices, and character spans. Rejects orphan/dangling citations. | Preserve as core verification gate. | Low |
| `backend/app/services/reporting/reporter.py` | Assembles 18-section investigation report in Markdown, JSON, and HTML with verifiable citations. | Complete | Source citations are formatted with document ID, filename, speaker, and timestamp. | Ensure citation numbers in text map 1-to-1 with key evidence list. | Low |
| `backend/app/services/llm_provider.py` | Multi-provider abstraction for Anthropic Claude, OpenAI GPT, and offline MockLLM. | Complete | Includes refusal mechanisms for prompt injection and secret revelation attempts. | Clearly mark mock provider outputs in responses. | Low |

---

## 2. Frontend Source Code Review

| File Path | Purpose | Status | Findings | Recommendation | Priority |
|---|---|:---:|---|---|:---:|
| `frontend/src/App.tsx` | Main application shell, router configuration, layout with Navbar and Sidebar. | Complete | All 12 routes cleanly wired under `CaseProvider`. | Ensure responsive mobile drawer toggle for sidebar on small screens. | **Medium** |
| `frontend/src/context/CaseContext.tsx` | Global case state provider: active case selection, loading state, refresh triggers. | Complete | Handles case switching and caches current case status. | Keep clean state synchronization. | Low |
| `frontend/src/services/api.ts` | Axios API client encapsulating all backend endpoints. | Complete | Includes endpoints for cases, documents, runs, contradictions review, and provenance. | Add response error interceptor for consistent notification handling. | Low |
| `frontend/src/pages/DashboardPage.tsx` | Main case overview: metrics summary, quick actions, analysis trigger, module status. | Complete | Real-time status polling during analysis; renders metric cards and case info. | Display controller feedback loop activity indicator. | Low |
| `frontend/src/pages/DocumentsPage.tsx` | Document management: multi-file upload, document list, text preview, search, delete. | Complete | Category filter, text search, and secure deletion working. | Add drag-and-drop file upload zone and file size warnings. | **Medium** |
| `frontend/src/pages/TimelinePage.tsx` | Interactive chronological timeline with participant filters and event inspection. | Complete | Displays ISO time, participant badges, location, and source document links. | Provide text/table toggle view for accessibility. | **Medium** |
| `frontend/src/pages/CaseGraphPage.tsx` | Visual node-link case graph using SVG canvas / force layout. | Complete | Interactive node dragging, color-coded node types (Person, Org, Loc, Object), and edge labels. | Add text table fallback listing all nodes and connections for accessibility. | **Medium** |
| `frontend/src/pages/ContradictionsPage.tsx` | Cross-document contradictions matrix: agreement vs conflict filtering and human review. | Complete | Interactive review status buttons (`Confirmed`, `Rejected`, `Investigate`). | Display detection engine badge (`NLI`, `Rules`, `LLM Verified`). | **High** |
| `frontend/src/pages/HypothesesPage.tsx` | Competing hypothesis ranking console with score breakdown and proposed explanation banner. | Complete | Displays Support, Conflict, Corroboration, Conflict Penalty, and Total Score. | Ensure heuristic disclosure note is prominently displayed. | Low |
| `frontend/src/pages/EvidencePage.tsx` | Semantic evidence search console and key retrieved evidence browser. | Complete | Search bar, threshold slider, document filter, and score badges working. | Display retrieval method and ranking metrics. | Low |
| `frontend/src/pages/ReportPage.tsx` | Complete 18-section investigation dossier viewer with Markdown/JSON export. | Complete | Provenance audit banner displayed; exports working. | Enable clicking a citation to scroll directly to the matching key evidence excerpt. | **High** |
| `frontend/src/pages/AskQuestionPage.tsx` | Natural language forensic Q&A console grounded in retrieved evidence. | Complete | Evidence excerpts and source citations rendered with answer. | Handle empty query validation gracefully. | Low |
| `frontend/src/pages/SettingsPage.tsx` | System configuration, provider status, storage path disclosure. | Complete | Shows active LLM provider, model name, and demo mode flag. | Disable sensitive input fields when running in demo/offline mode. | Low |
| `frontend/src/components/ContradictionCard.tsx` | Reusable card for viewing and reviewing contradiction items. | Complete | Displays statements A and B, speakers, documents, timestamps, and review status. | Add pill tag for `detection_engine`. | **High** |

---

## 3. Evaluation Scripts & Dataset Review

| File Path | Purpose | Status | Findings | Recommendation | Priority |
|---|---|:---:|---|---|:---:|
| `scripts/evaluate.py` | Benchmark evaluation harness for computing P/R/F1, MRR, and hypothesis ranking accuracy. | Partial | `evaluate_event_extraction` had `recall = 1.0` hardcoded instead of evaluating against ground truth `true_timeline`. | Compute genuine event recall and F1 by matching extracted events with `true_timeline` entries. | **Critical** |
| `scripts/seed_demo_cases.py` | Seeds cases 1 to 4 and pre-computes analyses for instant offline demonstration. | Complete | Works cleanly, populating `storage/cases/` and `storage/uploads/`. | Ensure idempotent execution without duplicating records. | Low |
| `scripts/generate_cases.py` | Generates synthetic sample cases and answer keys. | Complete | All 4 cases generated with realistic cross-document contradictions and ground truth. | Preserve strictly separated held-out cases (`case_03`, `case_04`). | Low |
| `data/ground_truth/*.json` | Ground-truth answer keys for Cases 01 to 04. | Complete | Hand-verified entities, timelines, planted contradictions, and culprit hypotheses. | Do not modify ground truth to artificially inflate scores. | Critical |

---

## 4. Repository & Configuration Hygiene

| File Path | Purpose | Status | Findings | Recommendation | Priority |
|---|---|:---:|---|---|:---:|
| `.gitignore` | Git exclusion rules. | Incomplete | Does not exclude `.env` or `*.env`. `storage/chroma/chroma_db/chroma.sqlite3` is tracked in git index. | Add `.env` to `.gitignore`; untrack `backend/.env` and `chroma.sqlite3` from git index. | **Critical** |
| `backend/.env` | Local environment configuration. | High Risk | Currently tracked by git (even though only containing placeholders). | Untrack with `git rm --cached backend/.env`. | **Critical** |
| `backend/.env.example` | Environment configuration template. | Complete | Contains safe dummy defaults and documentation comments. | Keep tracked as official template. | Low |
