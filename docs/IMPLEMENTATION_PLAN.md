# Text Detective: Implementation Plan & Architectural Specification
## An Agentic Text Analytics Framework for Evidence-Based Investigation

---

### 1. Executive Summary & Project Purpose

**Text Detective** is an investigation-oriented text analytics framework designed to analyze multi-source, heterogeneous, and potentially conflicting documents (such as witness interview transcripts, emails, forensic reports, incident logs, and audio/text memos). The application automatically extracts structured knowledge, constructs a chronological timeline and case graph, conducts semantic and keyword evidence retrieval, detects cross-document contradictions and agreements, formulates and scores competing hypotheses using an exact evidence-grounded scoring algorithm, and produces an auditable, source-referenced final investigation report.

Every factual conclusion in the application is strictly grounded in uploaded source documents with exact sentence, chunk, and document attributions.

---

### 2. Requirements & Specification (from Primary Source of Truth: Slides 1–20)

| Slide | Section | Key Architectural & Functional Requirements |
|---|---|---|
| **2–3** | Background & Motivation | Human investigators face high cognitive load reconciling conflicting multi-source texts. Text Detective synthesizes three core paradigms: Large Language Models (unstructured text understanding), Retrieval-Augmented Generation (grounding facts in real text), and Agentic AI (modular division of cognitive labor with feedback loops). |
| **4** | Problem Statement | Provide a single unified workflow that automates six essential capabilities: (1) Entity/Event/Time extraction, (2) Chronological timeline construction, (3) Meaning-based evidence search, (4) Cross-document contradiction detection, (5) Hypothesis comparison and ranking, (6) Fully source-linked reporting. |
| **5–6** | Literature Review | Bridges existing gaps across RAG (Lewis 2020, Gao 2023), DPR (Karpukhin 2020), Agent frameworks (Wang 2023), Contradiction detection (ContraDoc 2024, SNLI 2015, ContraGen 2025), and Fact-checking/Temporal reasoning (Guo 2022, SBERT 2019, TempEval 2007). |
| **7** | Research Gap | Solves lack of task integration, moves beyond isolated sentence-pair checking to multi-document contexts with speakers and timelines, supports full hypothesis comparison, provides end-to-end citation traceability, and offers an evaluation benchmark with ground truth. |
| **8** | Research Objectives | Implement Modules 1 through 6, Controller agent with feedback loops, evaluation framework across extraction, timeline, retrieval, contradiction detection, hypothesis ranking, and report quality. |
| **9–10** | Dataset & Tech Setup | 4 document types: Interviews, Emails, Reports, Logs. Tools: Python 3.11+, spaCy, SBERT + ChromaDB, RoBERTa-MNLI + LLM, FastAPI backend, React/Vite/Tailwind frontend. |
| **11** | Evaluation Metrics | Extraction (P/R/F1), Timeline (% event pairs in correct order), Retrieval (Recall@k, MRR), Contradictions (P/R/F1 on planted contradictions), Hypotheses (% correct hypothesis ranked #1), Report (Human rating 1–5 for clarity & traceability). |
| **12** | System Architecture | 6 Core Modules + Vector Database + Controller Agent orchestrating the pipeline with feedback loops. |
| **13** | Detailed Workflow & Feedback Loops | Controller manages forward flow and 3 feedback loops: Loop 1 (Need more evidence), Loop 2 (Need clarification), Loop 3 (Need additional analysis). Maximum 2 iterations per loop to guarantee termination. |
| **14–15** | Six Core Modules | Mod 1: Ingestion & Preprocessing; Mod 2: Entity, Event & Time Extraction; Mod 3: RAG-based Evidence Retrieval; Mod 4: Contradiction & Cross-Document Linking Agent; Mod 5: Hypothesis Generation & Scoring Module; Mod 6: Report Generation Module. |
| **16** | Case Graph Design | Node types: Entity (Person, Organization, Location, Object), Event (Action), Document (Source: Interview, Email, Report, Log, Other), Time (Temporal). Relations: `stated_in`, `works_for`, `involved_in`, `before/after/overlap`, `occurs_at_time`, `located_at`, `uses`, `provides_evidence`. |
| **17** | Sequence Diagram | 24 discrete operational steps from user upload to final report display with conditional feedback loop triggers. |
| **18** | Hypothesis Scoring Algorithm | `score(hypothesis) = Support - Conflict + Corroboration - Conflict Penalty`. Pure, unweighted, deterministic baseline. Exact test case: Support=3, Conflict=1, Corroboration=1, Penalty=0 -> Score=3. Top score is designated "System's Proposed Explanation". |
| **19–20** | References & Attribution | Formal research citation base; team attribution (Makka Lokesh, Punith Sai Nallapaneni, Vamsika Kilari). |

---

### 3. System Architecture & Component Design

```
+-----------------------------------------------------------------------------------+
|                                 FRONTEND (React + TS)                              |
| Dashboard | Cases | Upload | Analysis Status | Timeline | Evidence | Contradictions   |
| Hypotheses | Case Graph (React Flow) | Report (MD/JSON/PDF) | Ask a Question       |
+-----------------------------------------------------------------------------------+
                                        |  REST API (HTTP / JSON)
+-----------------------------------------------------------------------------------+
|                                 BACKEND (FastAPI)                                 |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                             CONTROLLER AGENT                                 |  |
|  |   - Pipeline Orchestrator                                                    |  |
|  |   - Feedback Loop 1: Need More Evidence (Refine query & re-retrieve)        |  |
|  |   - Feedback Loop 2: Need Clarification (Ambiguity & contradiction checks)   |  |
|  |   - Feedback Loop 3: Need Additional Analysis (Claim re-evaluation)          |  |
|  |   - Max 2 iterations per loop; comprehensive event audit logger              |  |
|  +-----------------------------------------------------------------------------+  |
|         |               |              |               |             |            |
|         v               v              v               v             v            |
|    +---------+     +---------+    +---------+     +---------+   +---------+       |
|    | Module 1|     | Module 2|    | Module 3|     | Module 4|   | Module 5|       |
|    |Ingestion|     |Extract'n|    |Retrieval|     |Contra-  |   |Hypothesis       |
|    |& Clean  |     |& Graph  |    |Hybrid   |     |dictions |   |& Scoring|       |
|    +---------+     +---------+    +---------+     +---------+   +---------+       |
|         |               |              |               |             |            |
|         +---------------+--------------+---------------+-------------+            |
|                                        |                                          |
|                                        v                                          |
|                                  +-----------+                                    |
|                                  | Module 6  |                                    |
|                                  | Reporting |                                    |
|                                  +-----------+                                    |
|                                                                                   |
|  +-------------------------+  +------------------------+  +--------------------+  |
|  | Storage: Case/Doc JSON  |  | Vector DB: ChromaDB    |  | LLM Providers:     |  |
|  | File system raw uploads |  | Sentence-Transformers  |  | Mock / Claude / GPT|  |
|  +-------------------------+  +------------------------+  +--------------------+  |
+-----------------------------------------------------------------------------------+
```

---

### 4. Technical Stack & Justification

- **Backend Language:** Python 3.12 (standard scientific & NLP runtime, highly reliable wheels for PyTorch, spaCy, ChromaDB).
- **Web Framework:** FastAPI (asynchronous, type-safe via Pydantic v2, automatic OpenAPI / Swagger documentation).
- **NLP & Parsing:**
  - `spaCy` (`en_core_web_sm` / rule-based matcher fallback) for NER, sentence tokenization, and linguistic structures.
  - Custom rule-based & regex temporal parser for ISO dates, clock times, relative times, and TempEval relations (`before`, `after`, `overlap`, `same_time`).
- **Vector Database & Embeddings:**
  - `sentence-transformers` (`all-MiniLM-L6-v2`) with a fast, lightweight fallback TF-IDF/BM25 + cosine embedder if heavy models are unavailable or offline.
  - `ChromaDB` for persistent local vector indexing segregated by `case_id`.
  - Hybrid retrieval: BM25/keyword scoring + vector cosine similarity fused with Reciprocal Rank Fusion (RRF), followed by Cross-Encoder / cosine reranking.
- **Natural Language Inference (NLI):**
  - Hugging Face `roberta-large-mnli` / `roberta-base` NLI pipeline or an efficient local zero-shot NLI classifier for entailment, contradiction, and neutral assessment.
  - LLM judge verification interface for borderline confidence pairs.
- **LLM Provider System:**
  - Configurable multi-provider architecture: `MockLLM` (fully deterministic, offline, zero API-key requirement), `AnthropicProvider` (Claude 3.5 Sonnet), and `OpenAIProvider` (GPT-4o).
  - Explicit provider selection via `.env` (`LLM_PROVIDER=mock`).
- **Frontend:**
  - React 18+ with TypeScript, Vite build tool, Tailwind CSS.
  - `@xyflow/react` (React Flow) for interactive case graph visualization.
  - `lucide-react` for case-file investigation iconography.
  - Responsive design, investigation case-file color palette (Dark navy `#131A2E`, Muted gold `#C9962F`, Cream `#F4F0E6`).

---

### 5. Detailed Module Specifications

#### Module 1: Ingestion & Preprocessing
- **Inputs:** Files (`.txt`, `.pdf`, `.csv`, `.json`, logs, `.docx`), document metadata (type, author, speaker, timestamp).
- **Operations:** Text extraction, encoding normalization (UTF-8), whitespace normalization, noise sanitization, sentence splitting.
- **Chunking:** Semantic sentence-level chunking preserving exact boundaries.
- **Outputs:** Processed document record with chunk list; each chunk carries `chunk_id`, `case_id`, `document_id`, `filename`, `document_type`, `speaker`, `timestamp`, `text`, `sentence_indices`, `char_span`.

#### Module 2: Entity, Event & Time Extraction
- **Entities:** Person, Organization, Location, Object.
- **Events:** Event description, participants (`involved_in`), location (`located_at`), time (`occurs_at_time`), object (`uses`), source citation (`provides_evidence`).
- **Temporal Relations:** `before`, `after`, `overlap`, `same_time`.
- **Case Graph (Slide 16):** NetworkX graph serialized to JSON:
  - Nodes: `Entity` (types: Person, Organization, Location, Object), `Event`, `Document` (types: Interview, Email, Report, Log, Other), `Time`.
  - Edges: `stated_in`, `involved_in`, `works_for`, `before`, `after`, `overlap`, `same_time`, `occurs_at_time`, `located_at`, `uses`, `provides_evidence`.
- **Timeline:** Ordered sequence of events with resolved or estimated timestamps and uncertainty flags.

#### Module 3: RAG-Based Evidence Retrieval
- **Indexing:** Persistent ChromaDB collection scoped per `case_id`.
- **Search Modes:** Semantic vector search, lexical keyword search (BM25), Hybrid RRF fusion (`score = 1/(60 + rank_sem) + 1/(60 + rank_kw)`).
- **Reranker:** Cross-score sorting returning top-k evidence items with source attributions.
- **Outputs:** Standard `EvidenceItem` with chunk text, document name, speaker, timestamp, sentence indices, relevance score.

#### Module 4: Contradiction & Cross-Document Linking Agent
- **Statement Pairing:** Cross-document statement clustering targeting identical entities, events, or timeframes.
- **NLI Classifier:** Evaluates premise-hypothesis pairs for `contradiction`, `entailment`, `neutral`.
- **Distinction:** Confirmed contradiction, possible contradiction, agreement, neutral.
- **Metadata Captured:** Statement A, Statement B, Document A, Document B, Speaker A, Speaker B, Entity/Event link, NLI label, confidence, explanation, resolution status.

#### Module 5: Hypothesis Generation & Scoring Module
- **Modes:** User-supplied hypotheses OR auto-generated candidate hypotheses via LLM / deterministic generator.
- **Claim Decomposition:** Decomposes each hypothesis into testable sub-claims.
- **Exact Scoring Formula (Slide 18):**
  $$\text{Score}(H) = \text{Support} - \text{Conflict} + \text{Corroboration} - \text{ConflictPenalty}$$
  - **Support:** Count of evidence chunks entailing hypothesis claims.
  - **Conflict:** Count of evidence chunks contradicting hypothesis claims.
  - **Corroboration:** +1 bonus per claim supported by evidence from at least 2 distinct documents AND 2 distinct speakers/authors.
  - **ConflictPenalty:** -1 penalty per unresolved contradiction touching the hypothesis claims.
- **Verification Rule:** Must pass unit test `Support=3, Conflict=1, Corroboration=1, Penalty=0 => Score=3`.
- **Ranking:** Sort descending by score. Highest designated "System's Proposed Explanation".

#### Module 6: Report Generation Module
- **Contents:** Case overview, documents ingested, executive summary, extracted entities, chronological timeline, key evidence, agreements, contradictions, candidate hypotheses, score breakdown, proposed explanation with full citation trail, unresolved questions, limitations and uncertainty statement.
- **Export Formats:** Interactive UI, Markdown (`.md`), Structured JSON (`.json`), Printable HTML/PDF.

#### Controller Agent & Feedback Loops (Slide 13, 17)
- Coordinates all 6 modules sequentially.
- **Feedback Loop 1 (Need More Evidence):** If retrieved evidence count or relevance for a core claim is below threshold, reformulates query and re-retrieves (capped at 2 iterations).
- **Feedback Loop 2 (Need Clarification):** If contradiction confidence is ambiguous, triggers targeted contextual retrieval and re-evaluates (capped at 2 iterations).
- **Feedback Loop 3 (Need Additional Analysis):** If hypothesis claims lack conclusive evidence or tie scores, requests targeted claim-evidence check (capped at 2 iterations).
- Logs every iteration and state transition for UI inspection.

---

### 6. Storage & Database Design

Storage hierarchy organized under `storage/`:
```
storage/
├── cases/
│   └── {case_id}/
│       ├── case.json                # Case metadata, status, description
│       ├── documents.json           # Ingested documents metadata & parsed chunks
│       ├── extraction.json          # Entities, events, timeline, case graph
│       ├── contradictions.json      # Cross-document agreements & contradictions
│       ├── hypotheses.json          # Evaluated & ranked hypotheses
│       ├── report.json              # Final investigation report
│       └── audit_log.json           # Controller event log and loop traces
├── uploads/
│   └── {case_id}/
│       └── {filename}               # Raw uploaded source files
└── chroma/                          # Persistent ChromaDB vector collections
```

---

### 7. API Design (FastAPI)

- `GET /api/health` - System health, active LLM provider, model status.
- `GET /api/cases` - List all cases (with document counts and status).
- `POST /api/cases` - Create a new case.
- `GET /api/cases/{case_id}` - Get case details.
- `PATCH /api/cases/{case_id}` - Rename or update case description.
- `DELETE /api/cases/{case_id}` - Delete case and all associated storage.
- `POST /api/cases/{case_id}/documents` - Upload one or more documents.
- `GET /api/cases/{case_id}/documents` - List documents for a case.
- `GET /api/documents/{document_id}` - Get full document chunks and text.
- `DELETE /api/documents/{document_id}` - Remove a document from a case.
- `POST /api/cases/{case_id}/analyze` - Run or re-run the full investigation pipeline.
- `GET /api/cases/{case_id}/analysis-status` - Current status, module progress, controller logs.
- `GET /api/cases/{case_id}/analysis-results` - Aggregated results across all modules.
- `GET /api/cases/{case_id}/entities` - Extracted entities.
- `GET /api/cases/{case_id}/events` - Extracted events.
- `GET /api/cases/{case_id}/timeline` - Chronological timeline.
- `GET /api/cases/{case_id}/case-graph` - Case graph (nodes, edges, styles).
- `POST /api/cases/{case_id}/evidence/search` - Semantic and hybrid evidence retrieval.
- `GET /api/cases/{case_id}/contradictions` - Detected contradictions and agreements.
- `POST /api/cases/{case_id}/hypotheses` - Add custom hypotheses.
- `GET /api/cases/{case_id}/hypotheses` - Get ranked hypotheses.
- `POST /api/cases/{case_id}/hypotheses/score` - Recalculate hypothesis scoring.
- `POST /api/cases/{case_id}/ask` - Ask a question about the case with grounded citations.
- `GET /api/cases/{case_id}/report` - Final investigation report.
- `GET /api/cases/{case_id}/report/download?format={md|json|html}` - Download report.
- `POST /api/evaluate` - Run benchmark evaluation against ground truth.
- `GET /api/evaluate/results` - Get latest evaluation report.

---

### 8. Frontend Navigation & Screen Structure

1. **Dashboard:** Case statistics, total documents, contradictions, active investigations, quick actions.
2. **Cases:** Case directory, create case, delete case, demo cases badge.
3. **New Investigation:** Step-by-step case creation and document upload wizard.
4. **Documents:** Document viewer, chunk explorer, speaker/timestamp tagger.
5. **Analysis Progress:** Live module-by-module execution tracker showing controller feedback loops.
6. **Timeline:** Interactive vertical chronological timeline with speaker and document links.
7. **Evidence Search:** Interactive query bar, relevance threshold slider, hybrid source citations.
8. **Contradictions:** Conflict and agreement cards with Statement A vs. B comparison and resolution status.
9. **Hypotheses:** Score cards, formula breakdown (Support - Conflict + Corroboration - Penalty), proposed explanation banner.
10. **Case Graph:** Interactive React Flow node-link diagram with filters for entities, events, documents, and times.
11. **Investigation Report:** Formatted executive dossier with tabs for Markdown, JSON, and download triggers.
12. **Ask a Question:** Natural-language interactive investigation Q&A grounded in evidence.
13. **Settings & Benchmark:** LLM provider configuration, evaluation runner, ground truth benchmark viewer.

---

### 9. Dataset & Ground Truth Plan

- **Sample Case 1 (Flagship Hand-crafted):** *"The Meridian Tech Data Leak"*
  - 9 documents: 3 interviews (Alice Vance, Bob Chen, David Wright), 2 emails (security alert, project update), 2 system logs (server access log, badge swipe log), 2 incident reports (CISO report, forensic report).
  - 18 named entities, 12 chronological events.
  - 6 planted contradictions (timestamps of presence, authorization claims, badge swipe discrepancies).
  - 1 correct hypothesis (credential misuse by subcontractor) and 3 believable decoy hypotheses (external ransomware attack, accidental misconfiguration, rogue DBA).
  - Stored in `data/sample_cases/case_01_meridian/` and answer key in `data/ground_truth/case_01_ground_truth.json`.
- **Sample Case 2:** *"The Blackwood Manor Art Heist"* (8 documents, 5 contradictions, 3 hypotheses).
- **Sample Case 3 (Held-Out Evaluation):** *"The Helios Pharma Clinical Trial Discrepancy"* (8 documents, 6 contradictions, 3 hypotheses).
- **Generator Script:** `scripts/generate_cases.py` to synthesize additional randomized or structured test cases.

---

### 10. Implementation Milestones

- **M1 (Scaffold):** Project structure, `.env.example`, Python venv, FastAPI skeleton, Pydantic schemas, MockLLM provider.
- **M2 (Module 1):** Ingestion, chunking, sanitization, metadata normalization, unit tests.
- **M3 (Module 2):** NER, temporal extraction, event builder, NetworkX case graph serializer, timeline builder, unit tests.
- **M4 (Module 3):** ChromaDB vector store, SBERT/TF-IDF hybrid retrieval, RRF fusion, reranker, unit tests.
- **M5 (Module 4):** Statement pair candidate generator, NLI classifier, contradiction graph, unit tests.
- **M6 (Module 5):** Hypothesis claim decomposer, exact scoring engine, ranking algorithm, unit tests.
- **M7 (Module 6):** Report builder, source reference linker, export generators (Markdown, JSON, HTML).
- **M8 (Controller Agent):** Full pipeline orchestration, 3 feedback loops with max 2 iterations, event logger, unit tests.
- **M9 (Frontend & APIs):** Vite + React + Tailwind UI, all 12 views, React Flow graph, live investigation runner.
- **M10 (Dataset & Evaluation):** 3 complete cases with ground truth, evaluation harness (`scripts/evaluate.py`), metrics calculation.
- **M11 (Verification & Production Build):** Pytest suite, frontend TypeScript build, end-to-end integration test, documentation.
