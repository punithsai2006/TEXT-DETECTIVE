# Text Detective: Project Risk Register and Dependency Matrix

> **Document Type:** Project Risk Governance, Quality Assurance, and Dependency Catalog  
> **Target System:** Text Detective — An Agentic Text Analytics Framework for Evidence-Based Investigation  
> **Evaluation Date:** November 2026  
> **Methodology:** ISO 31000 / OWASP AI Application Security Risk Framework  
> **Status:** Active Risk Audit & Mitigation Reference  

---

## 1. Executive Risk Overview

Text Detective is a multi-document investigative decision-support platform combining NLP extraction, vector search, cross-document NLI, and mathematical hypothesis ranking. Because investigative conclusions carry high cognitive and ethical stakes, identifying technical, operational, and algorithmic failure modes is critical.

This Risk Register provides a comprehensive analysis of **16 identified project risks**, rated by Likelihood (Low, Medium, High) and Impact (Low, Medium, High), with actionable warning signs, preventive mitigations, and emergency contingency protocols.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 RISK SEVERITY HEATMAP                                  │
├─────────────────────┬───────────────────┬──────────────────────┬───────────────────────┤
│                     │ Low Impact        │ Medium Impact        │ High Impact           │
├─────────────────────┼───────────────────┼──────────────────────┼───────────────────────┤
│ **High Likelihood** │                   │ False Contradictions │ Entity Over-Extraction│
├─────────────────────┼───────────────────┼──────────────────────┼───────────────────────┤
│ **Med Likelihood**  │ Temporal Ambiguity│ Model Download Delay │ Live Demo Glitches    │
│                     │ Storage Concurrency│                      │                       │
├─────────────────────┼───────────────────┼──────────────────────┼───────────────────────┤
│ **Low Likelihood**  │ File Path Escape  │ Mock Dependency Bias │ Prompt Injection      │
│                     │ Missing API Keys  │ Citation Hallucination│ Test Regressions      │
└─────────────────────┴───────────────────┴──────────────────────┴───────────────────────┘
```

---

## 2. Exhaustive Project Risk Register

| Risk ID | Risk Description | Likelihood | Impact | Risk Severity | Early Warning Signs | Preventive Mitigation Implemented | Contingency Protocol | Primary Owner |
|---|---|---|---|---|---|---|---|---|
| **RSK-01** | **Incorrect / Hallucinated Source Citations:** AI report cites a document chunk or sentence that does not exist or says something else. | **Low** | **High** | **Medium** | Citations referencing out-of-bounds sentence indices; complaints from review team. | Implemented `ProvenanceValidator` (`app/services/provenance/provenance_validator.py`) which enforces substring matching against physical document text. | Report generation fails with `HTTP 422 Unprocessable Entity` if any citation fails character-offset audit. | ML / Backend Lead |
| **RSK-02** | **High False Positive Contradiction Rate:** System flags semantic paraphrases or harmless stylistic differences as active conflicts ($Precision \approx 0.025$). | **High** | **Medium** | **High** | High conflict count ($>100$) on normal cases; user complaints about noisy discrepancy lists. | Implemented **Human-in-the-Loop Review Workflow** (`pending_review`, `confirmed`, `rejected`, `investigate`). Unconfirmed conflicts are penalized conditionally. | Analyst clicks **"Reject / Dismiss"** in UI, which suppresses the conflict penalty in hypothesis scoring. | NLP Engineer |
| **RSK-03** | **Entity Over-Extraction / Spurious Noun Chunks:** System extracts non-entities (e.g., `"local terminal"`, `"0 flash drive"`) lowering precision ($0.23$). | **High** | **Low** | **Medium** | Graph page crowded with irrelevant node bubbles; benchmark entity F1 below 0.40. | Strict length filtering ($\ge 3$ characters), non-alphanumeric stripping, and entity deduplication dictionary in `extractor.py`. | Analyst uses Case Graph node type filters (`Person`, `Location`, `Organization`) to hide unclassified object nodes. | NLP Engineer |
| **RSK-04** | **Temporal Imprecision / Ambiguity:** Ingested documents use relative time expressions (*"yesterday"*, *"later that night"*) that cannot be sorted. | **Medium** | **Medium** | **Medium** | Events appearing out of chronological sequence; `parsed_timestamp` set to `None`. | Regex normalizer anchors relative expressions to the document header date; flags vague times as `is_uncertain: True`. | Uncertain events display a prominent `"Approximate Time"` tag in the UI and sort to nearest anchor. | Backend Lead |
| **RSK-05** | **Ground-Truth Benchmark Leakage:** Rule-based extraction or hypothesis scoring tuned specifically to cheat the synthetic benchmark cases. | **Low** | **High** | **Medium** | Suspicious 100% precision on training cases but failure on new text files. | Created **two strictly held-out evaluation cases** (`case_03_helios` and `case_04_apex_robotics`) that were never used for prompt or rule tuning. | Re-evaluate on freshly authored blind test case during viva if requested by examiners. | Research Lead |
| **RSK-06** | **Evaluation & Author Subjectivity Bias:** Ground truth reflects author's subjective judgment of what constitutes an "event" or "culprit". | **Medium** | **Low** | **Low** | Disagreements between peer evaluators on ground-truth answer keys. | Published standardized human evaluation protocol form (`docs/evaluation/HUMAN_EVALUATION_TEMPLATE.csv`) with explicit criteria. | Solicit independent peer reviewer grading on the 1–5 qualitative evaluation scale. | Research Lead |
| **RSK-07** | **External LLM / Mock Dependency Confusion:** Examiners suspect system is purely simulated and cannot run with real models. | **Low** | **High** | **Medium** | Examiners asking why API keys are not active or questioning mock template validity. | Built modular adapter pattern (`LLMProvider`) supporting `MockLLMProvider`, `GroqProvider`, `OpenAIProvider`, and `AnthropicProvider`. | Demonstrate dynamic runtime switching via `backend/.env` live in front of examiners if internet is available. | Full-Stack Lead |
| **RSK-08** | **Missing Cloud API Credentials / Quota Exhaustion:** Live demonstration fails due to expired credit card, rate limit, or invalid API key. | **Low** | **High** | **Low** | 429 Too Many Requests or 401 Unauthorized errors in console logs. | Set `LLM_PROVIDER=mock` as default in `.env`. System executes 100% offline with zero cloud API dependencies. | Run the 5-minute offline demonstration script (`docs/DEMO_SCRIPT.md`) with guaranteed zero downtime. | Full-Stack Lead |
| **RSK-09** | **Model Download / HuggingFace Timeout:** Server hangs on startup trying to download 1.5GB `roberta-large-mnli` weights over poor Wi-Fi. | **Medium** | **High** | **High** | Terminal stuck at `Downloading weights...`; high RAM usage during viva setup. | Implemented lazy model initialization with automatic lexical rule fallback if PyTorch / HuggingFace fails to load. | Fallback detector activates seamlessly, completing contradiction analysis in <1 second. | Backend Lead |
| **RSK-10** | **Quadratic Scaling Bottleneck on Large Cases:** 100+ documents produce tens of thousands of pairwise sentence comparisons ($O(N^2)$). | **Medium** | **Medium** | **Medium** | Investigation pipeline progress bar hangs at 65% (Module 4) for $>60$ seconds. | In-memory ChromaDB batching; candidate pair pruning based on shared entity co-occurrence. | Limit demonstration cases to 10–20 documents (~100 chunks), completing pipeline in under 12 seconds. | Backend Lead |
| **RSK-11** | **File-Based JSON Storage Race Conditions:** Simultaneous concurrent requests corrupt `case.json` during write operations. | **Low** | **Medium** | **Low** | `JSONDecodeError: Expecting value` in backend console; empty case files. | Implemented `atomic_write_json` using temporary file writing followed by atomic `os.replace` operation. | Restore case files from initial seed scripts (`python scripts/seed_demo_cases.py`). | Backend Lead |
| **RSK-12** | **Cross-Case Vector Database Data Leakage:** Evidence chunks from Case A returned in evidence search for Case B. | **Low** | **High** | **Low** | Irrelevant suspect names appearing in unrelated case evidence cards. | ChromaDB collections are strictly partitioned per case using naming convention `case_{case_id}`. | Verified in regression test `test_retriever_case_isolation` which confirms complete isolation. | Backend Lead |
| **RSK-13** | **Malicious Prompt Injection in Document Body:** Uploaded file contains adversarial instructions attempting to commandeer agent. | **Low** | **High** | **Low** | Model outputs unrelated text, discloses system prompts, or clears suspects. | Strict architectural boundary: document content is treated strictly as passive data inside `<document_context>`. | Tested in `test_prompt_injection_in_document_treated_as_literal_content`; injection treated as inert text. | Security Lead |
| **RSK-14** | **Poor Dossier Readability / Layout Clutter:** Report output is visually overwhelming, cluttered, or difficult to digest for evaluators. | **Low** | **Medium** | **Low** | Examiners frustrated by dense walls of text; inability to quickly locate findings. | Redesigned frontend with clean executive dossier layout, 18 structured sections, and printable HTML view. | Switch to Markdown view or download printable HTML dossier with one click. | UI/UX Lead |
| **RSK-15** | **Live Demonstration Port Binding Conflict:** Port `8000` or `5173` already in use on examiner laptop, blocking application startup. | **Medium** | **High** | **High** | `[WinError 10048] Only one usage of each socket address is normally permitted`. | Pre-flight script provided; port override configuration documented in `backend/app/main.py`. | Start server on alternative port: `python -m uvicorn backend.app.main:app --port 8080`. | Full-Stack Lead |
| **RSK-16** | **Regression Breaks Passing Test Suite:** Late code modification inadvertently breaks previously working pipeline modules. | **Low** | **High** | **Low** | Test failures in CI/CD or during local `pytest` run. | Comprehensive 45-test automated regression suite covering all 6 modules, provenance, and security. | Rule: Zero code modifications allowed before viva without re-running full `pytest` suite. | QA Lead |

---

## 3. Project Dependencies Breakdown

### 3.1 Technical & Software Dependencies
- **Python Runtime:** Python 3.12+ (Windows 64-bit / Linux / macOS).
- **Core Backend Libraries:**
  - `fastapi >= 0.115.0`: Asynchronous Web API server.
  - `uvicorn >= 0.30.0`: ASGI web server.
  - `pydantic >= 2.10.0` & `pydantic-settings`: Schema enforcement and config management.
  - `chromadb >= 0.6.0`: Local persistent vector database.
  - `sentence-transformers >= 3.0.0`: Dense embeddings (`all-MiniLM-L6-v2`).
  - `networkx >= 3.4.0`: Directed graph modeling.
  - `pypdf >= 5.0.0` & `python-docx >= 1.1.0`: Multi-format text ingestion.
- **Frontend Stack:**
  - `Node.js >= 18.0.0` & `npm >= 9.0.0`.
  - `React >= 18.3.1` & `TypeScript >= 5.6.0`.
  - `Vite >= 6.0.0`: Build tool and dev server.
  - `Tailwind CSS >= 3.4.0`: Responsive styling.
  - `@xyflow/react >= 12.4.0`: Interactive graph canvas visualization.
  - `lucide-react`: Modern icon library.

### 3.2 External Service Dependencies
- **HuggingFace Hub (Optional):** Used for initial download of `roberta-large-mnli` and `all-MiniLM-L6-v2` weights. If offline, system falls back automatically to TF-IDF and regex rules without crashing.
- **Cloud LLM APIs (Optional):** Groq Cloud, OpenAI, or Anthropic. 100% bypassed when running in default `LLM_PROVIDER=mock` mode.

### 3.3 Dataset & Storage Dependencies
- **File System Storage:** Requires standard OS read/write permissions in `storage/cases/` and `data/ground_truth/`.
- **Benchmark Corpus:** 4 synthetic investigation cases with hand-crafted ground truth:
  1. `case_01_meridian` (9 documents, Data Exfiltration)
  2. `case_02_blackwood` (8 documents, Art Heist)
  3. `case_03_helios` (8 documents, Clinical Trial Fraud — *Held-Out*)
  4. `case_04_apex_robotics` (8 documents, Drone Firmware Sabotage — *Held-Out*)

### 3.4 Team & Operational Constraints
- **Team Size:** 3 Undergraduate Students (Makka Lokesh, Punith Sai Nallapaneni, Vamsika Kilari).
- **Presentation Window:** 5 to 10 minutes strictly allocated during viva examination.
- **Demonstration Rig:** Local Windows development workstation with dual-server orchestration (Port 8000 + Port 5173).
