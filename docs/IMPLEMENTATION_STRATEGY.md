# Text Detective: Implementation Strategy and Engineering Roadmap

> **Document Type:** Phased Engineering Roadmap, Task Allocation, and Quality Verification Plan  
> **Target System:** Text Detective — An Agentic Text Analytics Framework for Evidence-Based Investigation  
> **Evaluation Date:** November 2026  
> **Audience:** Project Engineering Team, Capstone Mentors, and Technical Reviewers  
> **Status:** Implementation Verified & Future Roadmap Catalog  

---

## 1. Roadmap Architecture & Execution Principles

This implementation strategy defines the development, hardening, and verification plan for Text Detective. The framework prioritizes:

$$\text{Correctness} \longrightarrow \text{Security} \longrightarrow \text{Evidence Provenance} \longrightarrow \text{Evaluation Integrity} \longrightarrow \text{Usability} \longrightarrow \text{Documentation}$$

The project is structured into **6 Sequential Phases**, designed to be executed efficiently by a 3-person undergraduate engineering team without introducing unmanageable enterprise overhead.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 1: CRITICAL CORRECTNESS & SECURITY                        │
│   Provenance Validator • File Path Traversal Defense • Upload Size Limits • CORS       │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 2: AI/ML & MULTI-MODULE INTEGRATION                       │
│   NLI Integration • Slide 18 Hypothesis Scorer • Controller Feedback Loops 1, 2, 3     │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 3: EVALUATION INTEGRITY & BENCHMARKING                    │
│   Held-Out Datasets (Cases 3 & 4) • Event F1 Metrics • Human Evaluation Protocol       │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 4: APPLICATION RELIABILITY & STORAGE                      │
│   Atomic Write-Replace • Cascading Doc Deletion • Immutable Run Records & Hashes       │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 5: FRONTEND MODERNIZATION & USABILITY                     │
│   Enterprise Slate UI • Collapsible Navigation • In-Page Upload • Dual-Mode Views      │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 6: DOCUMENTATION & ACADEMIC DEFENSE                       │
│   5-Min Viva Script • 12 Challenging Viva Defenses • Architecture Dossiers             │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Phase-by-Phase Task Breakdown

### Phase 1 — Critical Correctness and Security

* **Objective:** Eliminate citation hallucinations, protect against malicious file uploads, prevent unauthorized path traversal, and secure API boundaries.

| Task ID | Task Description | Priority | Owner | Dependencies | Estimated Effort | Deliverable | Verification Method |
|---|---|---|---|---|---|---|---|
| **T1.1** | Implement `ProvenanceValidator` to audit every citation against source character offsets. | **Critical** | Backend Lead | Preprocessor Chunking | 12 Hours | `app/services/provenance/provenance_validator.py` | Unit test `test_provenance_validator_accepts_valid_citations` passing. |
| **T1.2** | Enforce upload restrictions (10MB per file, 50MB batch, 20 files, whitelisted extensions). | **Critical** | Backend Lead | FastAPI Routes | 4 Hours | Route validation in `app/api/routes.py:upload_documents` | Test `test_unsupported_file_format` returns `HTTP 400`. |
| **T1.3** | Implement path traversal defense using regex stripping and `Path.is_relative_to()`. | **Critical** | Security Lead | Storage Layout | 3 Hours | Path sanitization in `case_store.py` | Test with `../../../etc/passwd` filename rejected. |
| **T1.4** | Configure in-memory sliding-window rate limiting (300 requests/min per IP) and CORS. | **High** | Backend Lead | FastAPI App | 4 Hours | Middleware in `app/main.py` | Verify 301st request returns `HTTP 429`. |
| **T1.5** | Implement prompt injection defense by isolating document text within passive tags. | **Critical** | ML Lead | LLM Provider | 6 Hours | Injection guardrail in `controller.py:ask_case_question` | Test `test_prompt_injection_in_document_treated_as_literal_content` passes. |

---

### Phase 2 — AI/ML Correctness & Pipeline Integration

* **Objective:** Integrate all six modules, enforce the exact Slide 18 hypothesis formula, and implement the three controller feedback loops.

| Task ID | Task Description | Priority | Owner | Dependencies | Estimated Effort | Deliverable | Verification Method |
|---|---|---|---|---|---|---|---|
| **T2.1** | Implement deterministic sentence boundary detection with abbreviation preservation. | **Critical** | NLP Lead | Ingestion Engine | 6 Hours | `preprocessor.py:split_into_sentences` | Test `test_sentence_splitting_with_abbreviations` passing. |
| **T2.2** | Integrate ChromaDB dense embedding search with fallback TF-IDF and Reciprocal Rank Fusion. | **Critical** | ML Lead | SentenceTransformers | 10 Hours | `retriever.py:search` | Test `test_retriever_case_isolation` passing; MRR > 0.90. |
| **T2.3** | Implement cross-document pairwise contradiction detection using `roberta-large-mnli`. | **Critical** | NLP Lead | PyTorch / Transformers | 14 Hours | `detector.py:find_cross_document_contradictions` | Test `test_direct_negation_contradiction_detection` passing. |
| **T2.4** | Implement exact Slide 18 hypothesis scoring formula ($Score(H) = Support - Conflict + Corrob - Penalty$). | **Critical** | ML Lead | Contradiction Engine | 8 Hours | `scorer.py:compute_exact_hypothesis_score` | Test `test_exact_hypothesis_scoring_formula` passing. |
| **T2.5** | Implement Central Controller Agent with Loops 1, 2, and 3 capped at 2 iterations. | **Critical** | Backend Lead | Modules 1–6 | 16 Hours | `controller.py:InvestigationController` | Verify loop iteration audit log in `case_store.json`. |

---

### Phase 3 — Evaluation Integrity & Benchmarking

* **Objective:** Establish honest, reproducible evaluation metrics across training and strictly held-out evaluation datasets.

| Task ID | Task Description | Priority | Owner | Dependencies | Estimated Effort | Deliverable | Verification Method |
|---|---|---|---|---|---|---|---|
| **T3.1** | Create automated evaluation harness calculating Entity F1, Event F1, Timeline Acc, and MRR. | **Critical** | Research Lead | Controller Pipeline | 12 Hours | `scripts/evaluate.py` | Execution outputs `docs/evaluation/benchmark_results.json`. |
| **T3.2** | Author hand-crafted ground truth for Training Cases (`case_01_meridian`, `case_02_blackwood`). | **High** | Research Lead | Evaluation Script | 10 Hours | `data/ground_truth/case_01_*.json` | Full schema validation against ground-truth schema. |
| **T3.3** | Construct held-out evaluation case `case_03_helios` (Clinical Trial Fraud; 8 docs). | **Critical** | Research Lead | Ingestion Pipeline | 8 Hours | `storage/cases/case_03_helios/` | Evaluated blindly without tuning extraction parameters. |
| **T3.4** | Construct second held-out case `case_04_apex_robotics` (Tactical Drone Sabotage; 8 docs). | **Critical** | Research Lead | Ingestion Pipeline | 10 Hours | `storage/cases/case_04_apex_robotics/` | Top-1 accuracy verified on fresh unseen scenario. |
| **T3.5** | Standardize Human Evaluation Protocol (1–5 scale) for qualitative dossier review. | **Medium** | Research Lead | Report Engine | 4 Hours | `docs/evaluation/HUMAN_EVALUATION_TEMPLATE.csv` | Peer evaluator grading conducted on 4 sample dossiers. |

---

### Phase 4 — Application Reliability & Storage Hardening

* **Objective:** Ensure data consistency, eliminate file write corruption, and maintain immutable audit run records.

| Task ID | Task Description | Priority | Owner | Dependencies | Estimated Effort | Deliverable | Verification Method |
|---|---|---|---|---|---|---|---|
| **T4.1** | Implement atomic write-and-replace (`atomic_write_json`) using temporary files. | **Critical** | Backend Lead | File Storage | 4 Hours | `case_store.py:atomic_write_json` | Test `test_atomic_write_json_integrity` passing. |
| **T4.2** | Implement cascading document deletion workflow with vector purging and `OUTDATED` status. | **Critical** | Backend Lead | ChromaDB + Storage | 8 Hours | `DELETE /api/cases/{id}/documents/{doc_id}` | Test `test_document_deletion_workflow_and_outdated_status` passes. |
| **T4.3** | Implement immutable `AnalysisRunRecord` with parser version, model ID, and SHA-256 hashes. | **High** | Backend Lead | Controller | 6 Hours | `app/models/schemas.py:AnalysisRunRecord` | Test `test_reproducible_analysis_run_records` passing. |
| **T4.4** | Build interactive Human Review Workflow for contradictions (`Confirm`, `Dismiss`, `Investigate`). | **High** | Full-Stack Lead | Contradiction Engine | 8 Hours | `PATCH /api/cases/{id}/contradictions/{c_id}` | Test `test_contradiction_human_review_workflow` passing. |

---

### Phase 5 — Frontend Modernization & Usability

* **Objective:** Transform the interface into a sleek, real-world enterprise cockpit that is intuitive, responsive, and easy to navigate.

| Task ID | Task Description | Priority | Owner | Dependencies | Estimated Effort | Deliverable | Verification Method |
|---|---|---|---|---|---|---|---|
| **T5.1** | Replace vintage yellow parchment aesthetic with modern Slate/Zinc palette and Tailwind design tokens. | **High** | UI/UX Lead | Tailwind Config | 8 Hours | `frontend/src/index.css`, `tailwind.config.js` | Visual verification: clean white cards, crisp slate background. |
| **T5.2** | Implement Collapsible Sidebar with icon rail mode (`w-16` / `w-64`) and remove academic footer text. | **Critical** | Frontend Lead | Sidebar Component | 6 Hours | `frontend/src/components/Sidebar.tsx` | Toggle button verified; student names cleanly removed. |
| **T5.3** | Add in-page direct document upload modal and dropzone directly on `DocumentsPage.tsx`. | **High** | Frontend Lead | API Client | 6 Hours | `frontend/src/pages/DocumentsPage.tsx` | User can upload files without leaving the Documents view. |
| **T5.4** | Implement dual-mode view toggles (Visual Timeline vs. Data Table; Graph Canvas vs. Topology Table). | **Medium** | Frontend Lead | ReactFlow | 6 Hours | `TimelinePage.tsx`, `CaseGraphPage.tsx` | View toggles switch smoothly with instant state preservation. |
| **T5.5** | Build interactive Slide 18 Formula Scorecard on Hypotheses page with claim expansion accordions. | **High** | Frontend Lead | Hypotheses Component | 8 Hours | `frontend/src/components/HypothesisCard.tsx` | 5 formula metric tiles render with clear color coding. |

---

### Phase 6 — Documentation, Demonstration & Academic Defense

* **Objective:** Package the project for flawless academic viva demonstration and rigorous examiner evaluation.

| Task ID | Task Description | Priority | Owner | Dependencies | Estimated Effort | Deliverable | Verification Method |
|---|---|---|---|---|---|---|---|
| **T6.1** | Author comprehensive 5-minute timed viva demonstration script with exact examiner talking points. | **Critical** | All Members | All Modules | 6 Hours | `docs/DEMO_SCRIPT.md` | Rehearsed offline walkthrough under 5 minutes. |
| **T6.2** | Compile complete answers to the 12 challenging external evaluator viva questions. | **Critical** | All Members | Evaluation Data | 10 Hours | `docs/ACADEMIC_EVALUATION_READINESS.md` | Team mock-viva practice with peer grilling. |
| **T6.3** | Compile master project architecture analysis and risk governance registers. | **High** | All Members | Benchmark Harness | 8 Hours | `COMPREHENSIVE_PROJECT_ANALYSIS.md`, `PROJECT_RISK_REGISTER.md` | Complete file inventory verified in workspace. |
| **T6.4** | Final regression verification: 45 automated unit tests passing, production frontend build successful. | **Critical** | QA Lead | Entire Codebase | 4 Hours | Clean Git commit on `main` branch | `pytest backend/tests/ -v` (45 passed), `npm run build` (0 errors). |

---

## 3. Team Resource Allocation Matrix

| Team Member | Primary Roles | Allocated Technical Responsibilities | Viva Defense Focus Areas |
|---|---|---|---|
| **Makka Lokesh** | Backend & Systems Architect | API Routing (`routes.py`), Atomic Storage (`case_store.py`), Rate Limiting, Cascading Deletion, Path Traversal Security | Backend architecture, REST endpoint design, file persistence safety, concurrency, and security hardening. |
| **Punith Sai Nallapaneni** | ML / NLP & Evaluation Lead | Ingestion Chunking (`preprocessor.py`), Vector Retrieval (`retriever.py`), Contradiction Detection (`detector.py`), Benchmark Harness (`evaluate.py`) | ChromaDB hybrid retrieval, RRF math, NLI classification, Slide 18 formula derivation, and evaluation metrics. |
| **Vamsika Kilari** | Full-Stack & UI/UX Lead | React 18 Frontend Architecture, Knowledge Graph Canvas (`@xyflow/react`), Collapsible Navigation, Citation Inspection Drawer | User experience, knowledge graph visualization, human review workflow, provenance tracking, and report dossier layout. |

---

## 4. Milestone Verification Schedule

```
MILESTONE 1: Core Engine Integration (Modules 1–6 Functional) ........... [COMPLETED]
MILESTONE 2: Provenance Validator & Adversarial Defense ................. [COMPLETED]
MILESTONE 3: Held-Out Benchmarking (4 Cases, 33 Documents) ............... [COMPLETED]
MILESTONE 4: Modern Enterprise UI & Collapsible Navigation .............. [COMPLETED]
MILESTONE 5: 45-Test Automated Regression Suite (100% Passing) .......... [COMPLETED]
MILESTONE 6: Academic Viva Preparation & Documentation Package .......... [COMPLETED]
```
