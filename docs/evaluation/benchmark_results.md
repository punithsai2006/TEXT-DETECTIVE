# TEXT DETECTIVE BENCHMARK EVALUATION RESULTS
**Date:** 2026-11-16T19:01:26.650525+00:00
**LLM Provider:** `mock` (Model: `mock-investigator-v1`)
**Execution Mode:** MockLLM (Offline Functional Verification)
**Provider Readiness Status:** `explicit_mock_ai_analysis_unavailable`

## 1. Summary Metrics Across Evaluated Cases
Total Cases Evaluated: 4 (including 2 designated held-out cases)
- **Total Documents Processed:** 33
- **Hypothesis Ranking Accuracy (Correct Ranked #1):** **100.0%** (4/4 cases)
- **Average Timeline Chronological Accuracy:** **100.0%**
- **Average MAS Milestone Chronological Accuracy:** **100.0%**
- **Average Retrieval MRR (Mean Reciprocal Rank):** **0.97** (Recall@5: 100.0%)
- **Average Entity Extraction F1:** **0.30**
- **Average Event Grounding F1:** **0.53**
- **Average Contradiction F1:** **0.36**
- **Average Citation Locator Validity:** **100.0%**
- **Average Quotation Verbatim Accuracy:** **0.0%**

## 2. Detailed Breakdown by Case
| Case ID | Case Name | Held-Out? | Entity F1 | Event F1 | Timeline Acc | Retrieval MRR | Top Hyp #1? |
|---|---|---|---|---|---|---|---|
| `case_01_meridian` | The Meridian Tech Data Leak | No | 0.25 | 0.56 | 100.0% | 0.90 | **PASSED (Rank #1)** |
| `case_02_blackwood` | The Blackwood Manor Art Heist | No | 0.30 | 0.64 | 100.0% | 1.00 | **PASSED (Rank #1)** |
| `case_03_helios` | The Helios Pharma Clinical Trial Discrepancy | Yes (Held-Out) | 0.35 | 0.25 | 100.0% | 1.00 | **PASSED (Rank #1)** |
| `case_04_apex_robotics` | The Apex Robotics Drone Sabotage | Yes (Held-Out) | 0.30 | 0.68 | 100.0% | 1.00 | **PASSED (Rank #1)** |

## 3. Five-Agent Multi-Agent System (MAS) Deliberation Metrics
| Case ID | Agents Active | Messages Logged | Milestone Count | Milestone Acc | Cross-Exam Findings | Adversarial Arguments | Neutral Assessment? |
|---|---|---|---|---|---|---|---|
| `case_01_meridian` | 5 Agents | 8 | 3 | 100.0% | 0 | 0 | No |
| `case_02_blackwood` | 5 Agents | 8 | 3 | 100.0% | 0 | 0 | No |
| `case_03_helios` | 5 Agents | 8 | 2 | 100.0% | 0 | 0 | No |
| `case_04_apex_robotics` | 5 Agents | 8 | 1 | 100.0% | 0 | 0 | No |

## 4. Citation Locator Validity & Quotation Accuracy
| Case ID | Citations Checked | Citation Validity | Quotes Checked | Verbatim Accuracy |
|---|---|---|---|---|
| `case_01_meridian` | 0 | 100.0% | 1 | 0.0% |
| `case_02_blackwood` | 0 | 100.0% | 1 | 0.0% |
| `case_03_helios` | 0 | 100.0% | 1 | 0.0% |
| `case_04_apex_robotics` | 0 | 100.0% | 1 | 0.0% |

## 5. Architecture Comparison: Single Pipeline vs Five-Agent MAS
| Dimension | Baseline Single Pipeline | Five-Agent Collaborative MAS | Improvement / Benefit |
|---|---|---|---|
| **Orchestration Model** | Monolithic sequential controller | Bounded 5-agent specialized workflow with Lead Investigator coordinator | Structured separation of concerns, delegated budgets, verifiable stages |
| **Timeline Synthesis** | Simple event sort with raw timestamps | Forensic timeline with phase classification and timestamp uncertainty | Granular categorization (Preparation, Access, Incident, Exit, Aftermath) |
| **Contradiction Analysis** | Heuristic pairwise detector | CrossExaminationAgent with 4-outcome taxonomy and context retrieval | Resolves ambiguity and prevents false perjury/lying accusations |
| **Hypothesis Reasoning** | Basic formula evaluation | Adversarial debate (Supporting vs Challenging Advocates + Neutral Arbiter) | Transparent multi-perspective debate with objective formula verification |
| **Evidence Grounding** | Flat chunk retrieval | Graph-RAG: 2-hop neighborhood expansion + Hybrid dense/sparse search | Discovers multi-hop relational leads connecting entities to actions |
| **Auditability** | Direct report output | Full observable action transcript + human review checkpoints | Complete provenance traceability for investigative and legal oversight |

## 6. Provider Execution Modes & Real-Model Readiness
- **Active Provider:** `mock`
- **Model Name:** `mock-investigator-v1`
- **Provider Status:** `explicit_mock_ai_analysis_unavailable`
- **Mock Mode Active:** `Yes (Offline verification mode)`
- **Real Provider Support:** Supported providers include OpenAI (`OPENAI_API_KEY`), Anthropic (`ANTHROPIC_API_KEY`), Ollama (`OLLAMA_BASE_URL`), and Local Transformers. When credentials are unconfigured, the system explicitly reports mock/offline status and never silently substitutes synthetic metrics.

## 7. Evaluation Methodology & Integrity Disclosure
- **Ground-Truth Construction:** Hand-crafted ground-truth answer keys specify planted entities, contradictory statement pairs, and validated culprit hypotheses.
- **Strict Held-Out Isolation:** `case_03_helios` and `case_04_apex_robotics` were created exclusively as held-out evaluation sets without parameter tuning.
- **Real-World Limitation:** Synthetic benchmark metrics demonstrate internal framework consistency, deterministic formula enforcement, and logic verification; they do not guarantee real-world messy OCR or multi-lingual accuracy.

## 8. Human Evaluation Protocol (Report Quality 1-5)
Human evaluation template is saved at `docs/evaluation/HUMAN_EVALUATION_TEMPLATE.csv`.
Evaluators rate Clarity, Source Traceability, Contradiction Completeness, and Logical Coherence on a 1-5 scale.

---
*Benchmark produced by Text Detective Automated Evaluation Harness*