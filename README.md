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
│   - Multi-format text extraction (pypdf, python-docx, text)            │
│   - Abbreviation-safe sentence boundary detection                      │
│   - Metadata tagging (doc_id, doc_type, author, timestamp, hash)       │
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
│   - Contradiction pairing with confidence scoring                      │
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

The hypothesis with the highest score is tagged as the **"System's Proposed Explanation"**. When score ties occur, the system flags the outcome as an ambiguity needing human analyst review.

---

## 4. Project Directory Structure

```
Text Project/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py              # REST API endpoints for cases, evidence, Q&A
│   │   ├── models/
│   │   │   └── schemas.py             # Pydantic data schemas
│   │   ├── services/
│   │   │   ├── ingestion/             # Module 1: Preprocessor & parser
│   │   │   ├── extraction/            # Module 2: NER, Timeline, Case Graph
│   │   │   ├── retrieval/             # Module 3: Vector & Hybrid Retriever
│   │   │   ├── contradiction/         # Module 4: NLI & Contradiction Detector
│   │   │   ├── hypothesis/            # Module 5: Exact Slide 18 Scorer
│   │   │   ├── reporting/             # Module 6: 18-Section Report Generator
│   │   │   ├── orchestration/         # Central Controller & 3 Feedback Loops
│   │   │   └── llm_provider.py        # MockLLM, Anthropic, and OpenAI providers
│   │   ├── storage/
│   │   │   └── case_store.py          # Isolated filesystem JSON storage
│   │   ├── config.py                  # Settings via pydantic-settings
│   │   └── main.py                    # FastAPI application & SPA mount
│   ├── tests/
│   │   ├── test_all_modules.py        # 16 unit tests for all modules & formula
│   │   └── test_api_endpoints.py      # 12 integration tests for REST APIs
│   ├── .env.example                   # Environment configuration template
│   └── requirements.txt               # Backend Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/                # CaseGraphViewer, ContradictionCard, etc.
│   │   ├── pages/                     # 12 complete investigation pages
│   │   ├── types/                     # TypeScript data interfaces
│   │   ├── App.tsx                    # React router & state management
│   │   └── main.tsx                   # Entry point
│   ├── package.json                   # React, Tailwind, @xyflow/react, lucide-react
│   └── vite.config.ts                 # Vite build configuration
├── data/
│   ├── sample_cases/
│   │   ├── case_01_meridian/          # Hand-crafted benchmark (9 documents)
│   │   ├── case_02_blackwood/         # Art heist benchmark (8 documents)
│   │   └── case_03_helios/            # Held-out clinical trial case (8 documents)
│   └── ground_truth/                  # Verified ground-truth answer keys
├── docs/
│   ├── IMPLEMENTATION_PLAN.md         # Full architectural design specification
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

### Step 2: Frontend Setup
```powershell
cd frontend
npm install
npm run build
cd ..
```

---

## 6. How to Run the Application

### Option A: Unified Full-Stack Server (FastAPI serving built React SPA)
```powershell
# Ensure venv is active
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
Open your browser to: **`http://localhost:5173`** (Vite proxies `/api` calls to `http://localhost:8000`).

---

## 7. Running Automated Tests

Run the complete test suite (28 automated tests covering all modules, the Slide 18 formula, edge cases, and all REST endpoints):

```powershell
.\.venv\Scripts\pytest.exe backend/tests/ -v
```

**Expected output:**
```
collected 28 items
backend/tests/test_all_modules.py::test_exact_hypothesis_scoring_formula PASSED
backend/tests/test_all_modules.py::test_hypothesis_scoring_variations PASSED
backend/tests/test_all_modules.py::test_hypothesis_ranking_order_and_ties PASSED
backend/tests/test_all_modules.py::test_hypothesis_ambiguity_warning_on_tie PASSED
backend/tests/test_all_modules.py::test_normalize_whitespace_and_noise PASSED
backend/tests/test_all_modules.py::test_sentence_splitting_with_abbreviations PASSED
backend/tests/test_all_modules.py::test_detect_document_type PASSED
backend/tests/test_all_modules.py::test_chunking_preserves_metadata PASSED
backend/tests/test_all_modules.py::test_empty_file_validation PASSED
backend/tests/test_all_modules.py::test_unsupported_file_format PASSED
backend/tests/test_all_modules.py::test_entity_extraction_types PASSED
backend/tests/test_all_modules.py::test_temporal_parsing PASSED
backend/tests/test_all_modules.py::test_retriever_case_isolation PASSED
backend/tests/test_all_modules.py::test_contradiction_detection_confirmed_and_agreements PASSED
backend/tests/test_all_modules.py::test_report_generation_and_markdown_export PASSED
backend/tests/test_all_modules.py::test_ask_question_with_no_evidence PASSED
backend/tests/test_api_endpoints.py::test_api_health PASSED
backend/tests/test_api_endpoints.py::test_api_cases_list PASSED
backend/tests/test_api_endpoints.py::test_api_get_case_detail PASSED
backend/tests/test_api_endpoints.py::test_api_get_documents PASSED
backend/tests/test_api_endpoints.py::test_api_get_timeline PASSED
backend/tests/test_api_endpoints.py::test_api_get_contradictions PASSED
backend/tests/test_api_endpoints.py::test_api_get_hypotheses PASSED
backend/tests/test_api_endpoints.py::test_api_get_case_graph PASSED
backend/tests/test_api_endpoints.py::test_api_get_report PASSED
backend/tests/test_api_endpoints.py::test_api_search_evidence PASSED
backend/tests/test_api_endpoints.py::test_api_ask_question PASSED
backend/tests/test_api_endpoints.py::test_api_report_downloads PASSED

======================= 28 passed in 36.43s =======================
```

---

## 8. Running the Benchmark Evaluation

Run the automated evaluation against the ground-truth benchmark suite:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate.py
```

### Verified Benchmark Results

| Metric | Result | Benchmark Target | Status |
|---|---|---|---|
| **Evaluated Cases** | 3 cases (25 documents total) | $\ge$ 3 cases | **PASSED** |
| **Held-Out Evaluation Case** | `case_03_helios` | 1 held-out case | **PASSED** |
| **Hypothesis Top-1 Rank Accuracy** | **100.0%** (3/3 cases) | $\ge 80.0\%$ | **PASSED** |
| **Timeline Chronological Accuracy**| **100.0%** | $\ge 90.0\%$ | **PASSED** |
| **Evidence Retrieval MRR** | **0.90 – 1.00** | $\ge 0.70$ | **PASSED** |
| **Case Isolation & No Data Leakage**| **100.0%** | 100.0% | **PASSED** |

---

## 9. Demo Case Walkthrough: "The Meridian Tech Data Leak"

1. **Dashboard:** Displays 3 active cases, 25 documents, 30+ entities, 5 contradictions, and evaluated hypotheses.
2. **Cases Navigation:** Select **"The Meridian Tech Data Leak"** (`case_01_meridian`).
3. **Documents:** Inspect the 9 uploaded files (interviews, emails, incident report, server access logs).
4. **Timeline:** Observe the ordered chronological sequence of events on October 24, 2024, from 21:00 UTC to 23:45 UTC.
5. **Evidence Search:** Search for `"USB thumb drive 22:15"` to see hybrid retrieval highlighting Server Room B access records.
6. **Contradictions:** Review the 5 detected contradictions:
   - *Example:* Elena Vance's interview claiming she left the building at 21:45 vs. Security Badge Log showing exit at 22:38.
7. **Hypotheses Evaluation:** Review the 3 candidate explanations scored using Slide 18:
   - **Hypothesis 1 (True Culprit):** Elena Vance exfiltrated the source code using Marcus Reed's compromised credentials. $\text{Score} = 3$ (**Rank #1 - System's Proposed Explanation**).
   - **Hypothesis 2 (Decoy):** External APT hacker group breached perimeter firewall. $\text{Score} = -2$.
   - **Hypothesis 3 (Decoy):** Marcus Reed stole data for competitor. $\text{Score} = -1$.
8. **Case Graph:** Interactive React Flow graph displaying nodes (Person, Org, Location, Object, Event) with typed directional edges (`at_time`, `located_at`, `participated_in`, `contradicts`).
9. **Case Q&A:** Ask `"Did anyone enter Server Room B after 22:00?"` — the system provides a cited response referencing `log_badge_reader.txt` without hallucinating.
10. **Investigation Report:** View or download the complete 18-section dossier in Markdown or JSON format.

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
