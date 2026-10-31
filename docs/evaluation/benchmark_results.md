# TEXT DETECTIVE BENCHMARK EVALUATION RESULTS
**Date:** 2026-10-31T22:38:09.346166+00:00
**LLM Provider:** `mock` (Model: `mock-investigator-v1`)
**Execution Mode:** MockLLM (Offline Functional Verification)

## Summary Metrics Across Evaluated Cases
- **Total Cases Evaluated:** 4 (including 2 designated held-out cases)
- **Total Documents Processed:** 33
- **Hypothesis Ranking Accuracy (Correct Ranked #1):** **100.0%** (4/4 cases)
- **Average Timeline Chronological Accuracy:** **100.0%**
- **Average Retrieval MRR (Mean Reciprocal Rank):** **0.97** (Recall@5: 100.0%)
- **Average Entity Extraction F1:** **0.30**
- **Average Event Grounding F1:** **0.65**

## Detailed Breakdown by Case
| Case ID | Case Name | Held-Out? | Entity F1 | Event F1 | Timeline Acc | Retrieval MRR | Top Hyp #1? |
|---|---|---|---|---|---|---|---|
| `case_01_meridian` | The Meridian Tech Data Leak | No | 0.26 | 0.71 | 100.0% | 0.90 | **PASSED (Rank #1)** |
| `case_02_blackwood` | The Blackwood Manor Art Heist | No | 0.31 | 0.68 | 100.0% | 1.00 | **PASSED (Rank #1)** |
| `case_03_helios` | The Helios Pharma Clinical Trial Discrepancy | Yes (Held-Out) | 0.34 | 0.44 | 100.0% | 1.00 | **PASSED (Rank #1)** |
| `case_04_apex_robotics` | The Apex Robotics Drone Sabotage | Yes (Held-Out) | 0.27 | 0.76 | 100.0% | 1.00 | **PASSED (Rank #1)** |

## Evaluation Methodology & Integrity Disclosure
- **Ground-Truth Construction:** Hand-crafted ground-truth answer keys specify planted entities, contradictory statement pairs, and validated culprit hypotheses.
- **Strict Held-Out Isolation:** `case_03_helios` and `case_04_apex_robotics` were created exclusively as held-out evaluation sets without parameter tuning.
- **Real-World Limitation:** Synthetic benchmark metrics demonstrate internal framework consistency, deterministic formula enforcement, and logic verification; they do not guarantee real-world messy OCR or multi-lingual accuracy.

## Human Evaluation Protocol (Report Quality 1-5)
Human evaluation template is saved at `docs/evaluation/HUMAN_EVALUATION_TEMPLATE.csv`.
Evaluators rate Clarity, Source Traceability, Contradiction Completeness, and Logical Coherence on a 1-5 scale.

---
*Benchmark produced by Text Detective Automated Evaluation Harness*