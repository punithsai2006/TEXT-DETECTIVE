# Text Detective: An Agentic Text Analytics Framework for Evidence-Based Investigation

> **Research & Implementation Project**  
> Based on the official research presentation by:
> - **Makka Lokesh** (AM.SC.U4CSE24233)
> - **Punith Sai Nallapaneni** (AM.SC.U4CSE24337)
> - **Vamsika Kilari** (AM.SC.U4CSE24227)

---

## 1. Project Overview & Research Purpose

**Text Detective** is an investigation-oriented text analytics framework designed for forensic analysts, intelligence investigators, and corporate compliance officers. When presented with complex, multi-document case files containing fragmented accounts, overlapping timelines, and conflicting witness statements, traditional keyword search or simple RAG chatbots fail by hallucinating unverified claims or overlooking subtle discrepancies.

Text Detective solves this through an autonomous agentic framework combining:
1. **Document Ingestion & Preprocessing** (Module 1)
2. **Entity, Event, and Time Extraction with Structured Case Graph** (Module 2)
3. **RAG-Based Evidence Retrieval** via Hybrid Dense/TF-IDF Search and RRF (Module 3)
4. **Cross-Document Contradiction & Linking Agent** using NLI and Discrepancy Rules (Module 4)
5. **Hypothesis Generation & Scoring** via the exact mathematical formula from Slide 18 (Module 5)
6. **Traceable 18-Section Investigation Report** (Module 6)
7. **Central Controller Agent** managing 3 autonomous feedback loops (Need more evidence, Need clarification, Need additional analysis).
8. **Evidence Provenance Validator** auditing 100% of citations and preventing dangling references.
9. **Human Review Workflow** for analyst review of detected contradictions (`pending_review`, `confirmed`, `rejected`, `needs_further_investigation`).
10. **Reproducible Analysis Run Records** capturing immutable audit logs, models, and SHA-256 document hashes.

---

## 2. System Architecture

```
                       ┌─────────────────────────┐
                       │  Uploaded Case Dossier  │
                       │ (PDF, DOCX, TXT, Logs)  │
                       └────────────┬────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Module 1: Ingestion & Preprocessing                  │
│   - Multi-format text extraction (pypdf, python-docx, text, logs)      │
│   - Abbreviation-safe sentence boundary detection                      │
│   - Metadata tagging (doc_id, doc_type, author, timestamp, sha256)    │
│   - Sentence-index tracked chunking (400 chars, 80 char overlap)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             Module 2: Entity, Event & Case Graph Construction          │
│   - NER: Person, Organization, Location, Object                        │
│   - Event & Temporal parsing (participants, locations, ISO dates)      │
│   - Chronological Timeline & NetworkX Directed Multi-Graph (Slide 16)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               Module 3: RAG Evidence Retrieval Engine                  │
│   - ChromaDB persistent vector storage & fallback TF-IDF vectorizer    │
│   - Hybrid Dense/Semantic + BM25 Lexical search                        │
│   - Reciprocal Rank Fusion (RRF) reranker                              │
│   - Direct source attribution down to chunk & sentence index           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│          Module 4: Cross-Document Contradiction & Linking Agent        │
│   - Cross-document pairwise sentence alignment                         │
│   - NLI classification (Entailment, Contradiction, Neutral)            │
│   - Temporal, numerical, locational, and direct negation conflict rules│
│   - Contradiction pairing with confidence & human review status        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               Module 5: Hypothesis Generation & Scoring                │
│   - Claim decomposition and semantic evidence mapping                  │
│   - Multi-Source Corroboration Rule: 2+ distinct docs & authors (+1)   │
│   - Conflict Penalty Rule: Active unresolved contradiction (-1)        │
│   - Exact Slide 18 Formula: Score(H) = Support - Conflict + Corrob - Pen│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│              Module 6: Traceable Investigation Report Dossier          │
│   - Full 18-Section Structured Dossier (Executive Summary, Graph, etc.)│
│   - Exact source citations: [doc_id, chunk_id, sentence_idx]           │
│   - Provenance Validator auditing source groundedness                  │
│   - Markdown & JSON export capabilities                                │
└────────────────────────────────────────────────────────────────────────┘
                                    ▲
                                    │ Controller Agent
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             Central Controller Agent & 3 Feedback Loops                │
│   - Loop 1: Need More Evidence (Uncovered claims trigger retrieval)   │
│   - Loop 2: Need Clarification (Ambiguous contradictions re-analyzed)  │
│   - Loop 3: Need Additional Analysis (Hypothesis tie-breaker trigger)   │
│   - Hard execution safety cap: Max 2 iterations per loop               │
│   - Zero-Hallucination Case Q&A with strict evidence boundary checks   │
│   - Immutable Analysis Run Records with SHA-256 document fingerprints │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Mathematical Formula for Hypothesis Scoring (Slide 18)

Every candidate hypothesis $H$ is evaluated using the formula specified in Slide 18 of the research presentation:

$$\text{Score}(H) = \sum_{c \in C_H} \text{Support}(c) - \sum_{c \in C_H} \text{Conflict}(c) + \text{Corroboration}(H) - \text{ConflictPenalty}(H)$$

Where:
- $C_H$ is the set of atomic claims decomposed from hypothesis $H$.
- $\text{Support}(c) = 1$ if relevant retrieved evidence documents entail claim $c$, else $0$.
- $\text{Conflict}(c) = 1$ if relevant evidence contradicts claim $c$, else $0$.
- $\text{Corroboration}(H) = 1$ if supporting evidence originates from at least two distinct documents with two distinct authors, else $0$.
- $\text{ConflictPenalty}(H) = 1$ if any active cross-document contradiction directly involves a key claim in $H$, else $0$.

> **Forensic Guidance:** The hypothesis score is an auditable mathematical ranking heuristic. It is not a statistical probability of guilt or legal finding.

---

## 4. Project Directory Structure

```
Text Project/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py              # REST API endpoints (cases, evidence, runs, review, Q&A)
│   │   ├── models/
│   │   │   └── schemas.py             # Pydantic data schemas & enums
│   │   ├── services/
│   │   │   ├── ingestion/             # Module 1: Preprocessor & chunker
│   │   │   ├── extraction/            # Module 2: NER, Timeline, Case Graph
│   │   │   ├── retrieval/             # Module 3: Vector & Hybrid Retriever
│   │   │   ├── contradiction/         # Module 4: NLI & Contradiction Detector
│   │   │   ├── hypothesis/            # Module 5: Exact Slide 18 Scorer
│   │   │   ├── reporting/             # Module 6: 18-Section Report Generator
│   │   │   ├── provenance/            # Evidence Provenance Validator (Task 2)
│   │   │   ├── orchestration/         # Central Controller & 3 Feedback Loops
│   │   │   └── llm_provider.py        # MockLLM, Anthropic, and OpenAI providers
│   │   ├── storage/
│   │   │   └── case_store.py          # Isolated filesystem JSON storage & run records
│   │   ├── config.py                  # Settings via pydantic-settings
│   │   └── main.py                    # FastAPI application, rate limiter, SPA mount
│   ├── tests/
│   │   ├── test_all_modules.py        # 16 unit tests for all modules & formula
│   │   ├── test_api_endpoints.py      # 14 integration tests for REST APIs
│   │   ├── test_provenance_and_security.py # 6 tests for provenance & security
│   │   └── test_adversarial_and_injection.py # 6 tests for injection defenses
│   ├── .env.example                   # Environment configuration template
│   └── requirements.txt               # Backend Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/                # CaseGraphViewer, ContradictionCard, etc.
│   │   ├── pages/                     # 12 complete investigation pages with filters
│   │   ├── types/                     # TypeScript data interfaces
│   │   ├── App.tsx                    # React router & state management
│   │   └── main.tsx                   # Entry point
│   ├── package.json                   # React, Tailwind, @xyflow/react, lucide-react
│   └── vite.config.ts                 # Vite build configuration
├── data/
│   ├── sample_cases/
│   │   ├── case_01_meridian/          # Hand-crafted benchmark (9 documents)
│   │   ├── case_02_blackwood/         # Art heist benchmark (8 documents)
│   │   ├── case_03_helios/            # Held-out clinical trial case (8 documents)
│   │   └── case_04_apex_robotics/     # Held-out tactical drone sabotage case (8 documents)
│   └── ground_truth/                  # Verified ground-truth answer keys
├── docs/
│   ├── IMPLEMENTATION_PLAN.md         # Full architectural design specification
│   ├── POST_IMPLEMENTATION_REVIEW.md  # Comprehensive improvement & validation review
│   ├── AUTHENTICATION_AND_AUTHORIZATION_DESIGN.md # Future multi-tenant RBAC specification
│   └── evaluation/
│       ├── benchmark_results.md       # Automated evaluation summary
│       ├── benchmark_results.json     # Detailed evaluation metrics
│       └── HUMAN_EVALUATION_TEMPLATE.csv
├── scripts/
│   ├── generate_cases.py              # Synthetic benchmark case generator
│   ├── seed_demo_cases.py             # Case seeder and pipeline runner
│   └── evaluate.py                    # Benchmark evaluation harness
├── pytest.ini
└── README.md
```

---

## 5. Installation and Setup (Windows PowerShell)

### Prerequisites
- Python 3.11 or 3.12 (`python --version`)
- Node.js v18+ and npm (`node -v`, `npm -v`)

### Step 1: Backend Setup
```powershell
# Navigate to the project root
cd "c:\Users\punit\OneDrive\Desktop\Text Project"

# Create a Python 3.12 virtual environment (if not already created)
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
.\.venv\Scripts\pip.exe install -r backend/requirements.txt
```

### Step 2: Frontend Setup & Build
```powershell
npm --prefix frontend install
npm --prefix frontend run build
```

---

## 6. How to Run the Application

### Option A: Unified Full-Stack Server (FastAPI serving built React SPA)
```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
Open your browser to: **`http://localhost:8000`**

### Option B: Separate Backend and Frontend Dev Server
In Terminal 1 (Backend):
```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000
```
In Terminal 2 (Frontend with Hot Reload):
```powershell
cd frontend
npm run dev
```
Open your browser to: **`http://localhost:5173`**

---

## 7. Running Automated Tests

Run the complete test suite (42 automated tests covering all modules, the Slide 18 formula, security mechanisms, provenance validation, adversarial injection defenses, and all REST endpoints):

```powershell
.\.venv\Scripts\pytest.exe backend/tests/ -v
```

**Verified Test Result:**
```
collected 42 items
backend/tests/test_adversarial_and_injection.py (6 passed)
backend/tests/test_all_modules.py (16 passed)
backend/tests/test_api_endpoints.py (14 passed)
backend/tests/test_provenance_and_security.py (6 passed)

============================= 42 passed in 12.26s =============================
```

---

## 8. Running the Benchmark Evaluation

Run the automated evaluation against the ground-truth benchmark suite:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate.py
```

### Verified Benchmark Results (All 4 Cases)

| Metric | Result | Benchmark Target | Status |
|---|---|---|---|
| **Evaluated Cases** | 4 cases (33 documents total) | $\ge 3$ cases | **PASSED** |
| **Designated Held-Out Cases** | `case_03_helios`, `case_04_apex_robotics` | $\ge 1$ held-out case | **PASSED** |
| **Hypothesis Top-1 Rank Accuracy** | **100.0%** (4/4 cases) | $\ge 80.0\%$ | **PASSED** |
| **Timeline Chronological Accuracy**| **100.0%** | $\ge 90.0\%$ | **PASSED** |
| **Evidence Retrieval MRR** | **0.97** (Recall@5: 100.0%) | $\ge 0.70$ | **PASSED** |
| **Event Grounding F1** | **0.65** | $\ge 0.50$ | **PASSED** |
| **Case Isolation & Zero Data Leakage**| **100.0%** | 100.0% | **PASSED** |

---

## 9. Key Documentation & Reports

- **Post-Implementation Review:** [`docs/POST_IMPLEMENTATION_REVIEW.md`](docs/POST_IMPLEMENTATION_REVIEW.md)
- **Authentication & Authorization Design:** [`docs/AUTHENTICATION_AND_AUTHORIZATION_DESIGN.md`](docs/AUTHENTICATION_AND_AUTHORIZATION_DESIGN.md)
- **Implementation Plan:** [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md)
- **Benchmark Evaluation Report:** [`docs/evaluation/benchmark_results.md`](docs/evaluation/benchmark_results.md)
- **Human Evaluation Rubric Template:** [`docs/evaluation/HUMAN_EVALUATION_TEMPLATE.csv`](docs/evaluation/HUMAN_EVALUATION_TEMPLATE.csv)

---

## 10. Authors & Citation

```bibtex
@article{lokesh2024textdetective,
  title={Text Detective: An Agentic Text Analytics Framework for Evidence-Based Investigation},
  author={Makka Lokesh and Punith Sai Nallapaneni and Vamsika Kilari},
  institution={Department of Computer Science and Engineering},
  year={2024}
}
```
