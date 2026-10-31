# TEXT DETECTIVE BENCHMARK EVALUATION RESULTS
**Date:** 2026-10-31T22:10:26.430509
**LLM Provider:** `mock` (Model: `mock-investigator-v1`)
**Execution Mode:** MockLLM (Offline Functional Verification)

## Summary Metrics Across Evaluated Cases
- **Total Cases Evaluated:** 3
- **Total Documents Processed:** 25
- **Hypothesis Ranking Accuracy (Correct Ranked #1):** **100.0%**

## Detailed Breakdown by Case
| Case ID | Case Name | Held-Out? | Entity F1 | Timeline Order Acc | Retrieval MRR | Contradiction F1 | Top Hyp #1? |
|---|---|---|---|---|---|---|---|
| `case_01_meridian` | The Meridian Tech Data Leak | No | 0.26 | 100.0% | 0.90 | 0.03 | **PASSED (Rank #1)** |
| `case_02_blackwood` | The Blackwood Manor Art Heist | No | 0.31 | 100.0% | 1.00 | 0.15 | **PASSED (Rank #1)** |
| `case_03_helios` | The Helios Pharma Clinical Trial Discrepancy | Yes | 0.34 | 100.0% | 1.00 | 0.00 | **PASSED (Rank #1)** |

## Human Evaluation Protocol (Report Quality 1-5)
Human evaluation template is saved at `docs/evaluation/HUMAN_EVALUATION_TEMPLATE.csv`.
Evaluators rate Clarity, Source Traceability, Contradiction Completeness, and Logical Coherence on a 1-5 scale.

---
*Benchmark produced by Text Detective Automated Evaluation Harness*