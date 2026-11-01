# Text Detective: Project Architecture & Engineering Audit

> **System Audit Date:** November 1, 2026  
> **Authors:** Makka Lokesh (AM.SC.U4CSE24233), Punith Sai Nallapaneni (AM.SC.U4CSE24337), Vamsika Kilari (AM.SC.U4CSE24227)  
> **Repository:** [https://github.com/punithsai2006/TEXT-DETECTIVE](https://github.com/punithsai2006/TEXT-DETECTIVE)  
> **Audit Status:** Verified against active source code, automated test suite (42 tests), and 4 evaluation benchmark cases.

---

## 1. Verified Architecture & Technology Stack

Text Detective is implemented as a multi-tier, modular investigation architecture adhering strictly to the specifications from the project research presentation.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER (UI/UX)                          │
│     React 18 + TypeScript + Vite + Tailwind CSS + Lucide Icons (12 Pages)      │
└───────────────────────────────────────┬────────────────────────────────────────┘
                                        │ HTTP REST / JSON
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│                         API & APPLICATION SERVER (FASTAPI)                     │
│  - App Lifespan & Config Management (Pydantic Settings)                        │
│  - In-Memory Rate Limiting (300 req/min per IP sliding window)                 │
│  - Localhost CORS & Global Exception Masking Middleware                        │
│  - Endpoints: Cases, Uploads, Analysis, Graph, Evidence, Contradictions, Q&A   │
└───────────────────────────────────────┬────────────────────────────────────────┘
                                        │
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│                            CENTRAL CONTROLLER AGENT                            │
│  Orchestrator (`backend/app/services/orchestration/controller.py`)             │
│  Manages execution across the 6 modules and enforces 3 closed feedback loops:  │
│    • Loop 1: NEED_MORE_EVIDENCE (Sufficiency threshold re-querying)            │
│    • Loop 2: NEED_CLARIFICATION (Context-enriched contradiction re-evaluation) │
│    • Loop 3: NEED_ADDITIONAL_ANALYSIS (Hypothesis tie-breaking evidence hunt)  │
└───────┬───────────────────────┬───────────────────────┬───────────────┬────────┘
        │                       │                       │               │
        ▼                       ▼                       ▼               ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐ ┌──────────────┐
│   MODULE 1    │       │   MODULE 2    │       │   MODULE 3    │ │   MODULE 4   │
│ Ingestion &   │──────►│ Entity, Event │──────►│ Chronological │ │ Semantic     │
│ Preprocessing │       │ & Case Graph  │       │   Timeline    │ │ Vector Store │
└───────────────┘       └───────────────┘       └───────────────┘ └──────┬───────┘
                                                                         │
                                                                         ▼
                                                                ┌────────────────┐
                                                                │   MODULE 5     │
                                                                │ Contradiction  │
                                                                │  & Agreement   │
                                                                └────────┬───────┘
                                                                         │
                                                                         ▼
                                                                ┌────────────────┐
                                                                │   MODULE 6     │
                                                                │ Hypothesis     │
                                                                │ Scoring Engine │
                                                                └────────┬───────┘
                                                                         │
                                                                         ▼
                                                                ┌────────────────┐
                                                                │ PROVENANCE &   │
                                                                │ FINAL DOSSIER  │
                                                                └────────────────┘
```

### Verified Technology Stack

| Layer | Component | Verified Technology | Purpose in System |
|---|---|---|---|
| **Backend Framework** | Web API | FastAPI 0.115+, Uvicorn | High-performance asynchronous REST API server |
| **Data Validation** | Schema Models | Pydantic v2.10+, Pydantic Settings | Strict request/response validation and environment typing |
| **Vector Storage** | Embedding Index | ChromaDB 0.6+ & JSON fallback index | Dense vector indexing per case with Cosine & RRF search |
| **Embeddings** | Dense Representation | SentenceTransformers (`all-MiniLM-L6-v2`) / TF-IDF | Semantic search over document chunks and query terms |
| **Graph Modeling** | Network Topology | NetworkX 3.4+ | Case Graph node-link generation and graph metric analysis |
| **Contradiction NLI**| Semantic Conflict | Transformers (`roberta-large-mnli`) / Lexical regex pairs | Identifying opposing witness statements and alibi discrepancies |
| **Frontend** | Single Page App | React 18.3, TypeScript 5.6, Vite 6.0 | Investigative analyst console with client-side state |
| **Styling & Icons** | Design System | Tailwind CSS 3.4, Lucide React | Forensic color palette (`#131A2E`, `#C9962F`, `#F4F0E6`) |
| **Testing Harness** | Automated Tests | Pytest 9.2, Pytest-Asyncio, HTTPX | 42 unit, integration, provenance, and adversarial tests |

---

## 2. Inventory of Project Artifacts

### A. Source Code Files
* **Backend Core (`backend/app/`):**
  * `main.py`: FastAPI server setup, rate-limiting middleware, CORS, and static file serving.
  * `config.py`: Environment configuration via Pydantic Settings (`storage`, `data`, `demo_mode`).
  * `api/routes.py`: 26 REST endpoints for cases, documents, runs, evidence, graph, and reports.
  * `models/schemas.py`: Comprehensive Pydantic models for all entities, events, claims, and runs.
  * `storage/case_store.py`: File-based atomic JSON persistence and case-level data isolation.
  * `services/ingestion/preprocessor.py`: Multi-format parsing, sentence segmentation, and chunking.
  * `services/extraction/extractor.py`: Named entity recognition, temporal normalization, and graph builder.
  * `services/retrieval/retriever.py`: Case-isolated vector store, dense embeddings, TF-IDF, and RRF.
  * `services/contradiction/detector.py`: Cross-document statement comparison, NLI, and conflict word pairs.
  * `services/hypothesis/scorer.py`: Exact Slide 18 hypothesis scoring formula implementation.
  * `services/orchestration/controller.py`: Central controller with 3 autonomous feedback loops.
  * `services/provenance/provenance_validator.py`: Provenance validation and citation integrity auditor.
  * `services/reporting/reporter.py`: Markdown and JSON dossier generation with source references.
  * `services/llm_provider.py`: Abstraction layer for Anthropic, OpenAI, and offline MockLLM.

* **Frontend Console (`frontend/src/`):**
  * 12 Functional Pages: `DashboardPage`, `CasesPage`, `NewInvestigationPage`, `DocumentsPage`, `TimelinePage`, `EvidencePage`, `ContradictionsPage`, `HypothesesPage`, `CaseGraphPage`, `ReportPage`, `AskQuestionPage`, `SettingsPage`.
  * 6 Reusable Components: `Navbar`, `Sidebar`, `CaseGraphViewer`, `ContradictionCard`, `EvidenceCard`, `HypothesisCard`.
  * Context & Services: `CaseContext.tsx`, `api.ts`, and `types/index.ts`.

### B. Sample Cases & Ground Truth (`data/`):
* `case_01_meridian`: The Meridian Tech Data Leak (9 documents, insider data theft scenario).
* `case_02_blackwood`: The Blackwood Manor Art Heist (8 documents, physical museum theft scenario).
* `case_03_helios`: The Helios Pharma Trial Discrepancy (8 documents, held-out clinical data fabrication).
* `case_04_apex_robotics`: The Apex Robotics Drone Sabotage (8 documents, held-out industrial firmware sabotage).
* Answer Keys: Hand-verified JSON answer keys for all 4 cases in `data/ground_truth/`.

### C. Test Files (`backend/tests/`):
* `test_all_modules.py`: 13 tests covering preprocessing, extraction, retrieval, scoring, and ties.
* `test_api_endpoints.py`: 15 tests verifying all REST endpoints, downloads, and search.
* `test_provenance_and_security.py`: 7 tests validating provenance audit, deletions, and run records.
* `test_adversarial_and_injection.py`: 7 tests validating prompt injection defense, secret disclosure refusal, and date ambiguities.
* Total: **42 passing automated tests**.

---

## 3. Module Responsibilities & Feature Flow

```
1. Document Upload
   ├── Files: .txt, .pdf, .docx, .log, .csv, .json
   ├── Validation: File size (<10MB), Batch (<50MB), Extension Whitelist, Path Traversal Defense
   └── Processing: Sentence boundary detection, metadata extraction, deterministic chunking

2. Extraction & Case Graph
   ├── Entity Extraction: Person, Organization, Location, Object (with mention counts and source sentences)
   ├── Temporal Normalization: ISO-8601 formatting, relative time parsing, uncertainty flagging
   └── Graph Topology: Nodes (Entities, Events, Documents) & Directed Edges (Relations, Timeline links)

3. Vector Evidence Retrieval
   ├── ChromaDB persistent collection per case (`case_{case_id}`)
   ├── Hybrid Retrieval: Dense Cosine Similarity + BM25 Token Frequency
   └── Reciprocal Rank Fusion: Combined RRF score = 1/(60+sem_rank) + 1/(60+kw_rank)

4. Contradiction Detection
   ├── Pairwise Cross-Document Statement Analysis
   ├── Conflict Detection: Semantic Antonyms, Negation Disparities, Location/Time Clashes
   └── Human Review Support: Pending, Confirmed, Rejected, Needs Further Investigation

5. Hypothesis Scoring
   ├── Exact Presentation Formula: Score(H) = Support - Conflict + Corroboration - ConflictPenalty
   ├── Claim Decomposition: 2-4 atomic verifiable claims per hypothesis
   ├── Corroboration: +1 if claim supported by >=2 different documents AND >=2 different speakers
   └── Ranking: Highest score designated 'Proposed Explanation', with tie/ambiguity detection

6. Report & Provenance Validation
   ├── Structured 18-Section Investigation Dossier (Markdown, JSON, HTML)
   ├── Traceable Evidence Citations: Document ID, Chunk ID, Sentence Index, Text Excerpt
   └── ProvenanceValidator: Zero-hallucination verification rejecting orphan citations
```

---

## 4. Current Implementation Status & Verification

* **Backend Execution:** Verified functional on Windows with Python 3.12 (`fastapi`, `uvicorn`, `chromadb`).
* **Frontend Execution:** Verified production build with Vite 6 (`npm run build` succeeds in 12.5s with zero TypeScript errors).
* **Automated Tests:** 42/42 tests passing (`pytest backend/tests/ -v`).
* **Evaluation Harness:** Automated benchmarking executed via `python scripts/evaluate.py`:
  * Hypothesis Top-1 Accuracy: **100.0%** (4/4 cases)
  * Timeline Chronological Accuracy: **100.0%**
  * Evidence Retrieval MRR: **0.97** (Recall@5: **100.0%**)
