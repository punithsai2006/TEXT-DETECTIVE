# Text Detective: Benchmark Evaluation Methodology & Integrity Protocol

> **Version:** 2.0  
> **Date:** November 15, 2026  
> **Harness:** `scripts/evaluate.py`  
> **Ground Truth Path:** `data/ground_truth/`  
> **Evaluation Mode:** Fully Isolated Offline Evaluation (Mock / Self-Contained)

---

## 1. Overview & Benchmark Integrity Mandate

The Text Detective Benchmark provides an empirical, reproducible framework for assessing the accuracy, explainability, and stability of agentic text analytics pipelines in evidence-based investigations.

### Core Integrity Rules
1. **Strict Evaluation Isolation:** Ground-truth files located in `data/ground_truth/` are strictly decoupled from application runtime logic. The application controller, extraction pipeline, retriever, contradiction engine, and hypothesis scorer **never read, import, or receive ground-truth data** during investigation execution.
2. **Autonomous Analysis:** All case timelines, entities, contradictions, candidate hypotheses, and ranking scores must be derived solely from raw uploaded documents.
3. **No Synthetic Manipulation:** Scoring formulas, threshold cutoffs, and evaluation metrics must never be tweaked to produce artificial benchmark scores.
4. **Transparent Disclosures:** Real-world limitations (e.g. synthetic document constraints, OCR variability) must be explicitly documented.

---

## 2. Dataset Architecture & Split Design

The benchmark consists of 5 multi-document investigation cases spanning corporate insider leaks, art theft, clinical trial data tampering, aerospace sabotage, and museum archival theft.

| Case ID | Case Name | Documents | Words | Planted Contradictions | Role in Benchmark | Domain |
|---|---|---|---|---|---|---|
| `case_01_meridian` | The Meridian Tech Data Leak | 9 | ~3,200 | 5 | **Development Set** | Cybersecurity / Database Theft |
| `case_02_blackwood` | The Blackwood Manor Art Heist | 8 | ~2,800 | 3 | **Development Set** | Physical Security / Art Heist |
| `case_03_helios` | The Helios Pharma Clinical Trial Discrepancy | 8 | ~2,950 | 3 | **Held-Out Evaluation** | Biotech / Regulatory Fraud |
| `case_04_apex_robotics` | The Apex Robotics Drone Sabotage | 8 | ~3,100 | 3 | **Held-Out Evaluation** | Aerospace / Firmware Tampering |
| `case_05_lakeview` | Lakeview Library Rare Map Theft (LV-3112) | 11 | ~4,100 | 4 | **Held-Out Evaluation** | Archival / Insider Property Theft |

### Split Protocol:
- **Development Set (Cases 1 & 2):** Used for initial prompt development, regex pattern refinement, and baseline pipeline construction.
- **Held-Out Evaluation Set (Cases 3, 4 & 5):** Strictly reserved for unbiased validation. Extraction heuristics, NLI classification patterns, and scoring weights were never tuned against held-out cases.

---

## 3. Mathematical Metric Definitions

The automated evaluation harness evaluates 6 distinct dimensions across the investigative lifecycle:

### 3.1 Entity Extraction Precision, Recall, and F1
Evaluated by comparing extracted entity names against the ground-truth entity registry:
$$\text{Precision}_{\text{ent}} = \frac{|\text{Pred} \cap \text{True}|}{|\text{Pred}|}, \quad \text{Recall}_{\text{ent}} = \frac{|\text{Pred} \cap \text{True}|}{|\text{True}|}$$
$$\text{F1}_{\text{ent}} = \frac{2 \cdot \text{Precision}_{\text{ent}} \cdot \text{Recall}_{\text{ent}}}{\text{Precision}_{\text{ent}} + \text{Recall}_{\text{ent}}}$$

### 3.2 Event Grounding Precision, Recall, and F1
An extracted event is considered a true positive if its description and verbatim source sentence match at least two distinct semantic tokens from a ground-truth timeline entry.
$$\text{Precision}_{\text{ev}} = \frac{\text{TP}_{\text{ev}}}{\text{Total Extracted Events}}, \quad \text{Recall}_{\text{ev}} = \frac{\text{TP}_{\text{ev}}}{\text{Total True Events}}$$
$$\text{F1}_{\text{ev}} = \frac{2 \cdot \text{Precision}_{\text{ev}} \cdot \text{Recall}_{\text{ev}}}{\text{Precision}_{\text{ev}} + \text{Recall}_{\text{ev}}}$$

### 3.3 Timeline Chronological Accuracy
Evaluates whether chronological precedence is preserved across all pairwise combinations of ground-truth events present in the extracted timeline:
$$\text{Accuracy}_{\text{time}} = \frac{\sum_{i < j} \mathbf{1}(\text{sort\_key}(e_i) \le \text{sort\_key}(e_j))}{\binom{N}{2}}$$
Where $N$ is the count of matched ground-truth event pairs.

### 3.4 Hybrid Evidence Retrieval (Recall@k & MRR)
For each planted contradiction pair involving source documents $D_a$ and $D_b$, a search query is dispatched to the hybrid retriever.
- **Recall@5:** Percentage of planted contradiction queries where either $D_a$ or $D_b$ appears in the top 5 retrieved passages.
- **Mean Reciprocal Rank (MRR):**
$$\text{MRR} = \frac{1}{|Q|} \sum_{q=1}^{|Q|} \frac{1}{\text{rank}_q}$$
Where $\text{rank}_q$ is the first rank where a relevant document appears ($\text{rank}_q \in [1, k]$), or $0$ if unretrieved.

### 3.5 Contradiction Detection Precision, Recall, and F1
Evaluated against planted contradiction pairs:
- **True Positive (TP):** An extracted contradiction matching the target entity or linking the exact opposing document pair ($D_a, D_b$).
- **False Positive (FP):** Extracted contradiction not corresponding to any planted conflict.
- **False Negative (FN):** Planted contradiction completely missed by the engine.
$$\text{Precision}_{\text{contra}} = \frac{\text{TP}}{\text{TP} + \text{FP}}, \quad \text{Recall}_{\text{contra}} = \frac{\text{TP}}{\text{TP} + \text{FN}}$$
$$\text{F1}_{\text{contra}} = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

### 3.6 Hypothesis Ranking Accuracy (Top-1 Correctness)
Evaluates whether the true explanatory hypothesis (identifying the actual culprit and primary mechanism) is autonomously assigned Rank #1:
$$\text{Accuracy}_{\text{hyp}} = \frac{1}{|C|} \sum_{c \in C} \mathbf{1}(\text{Rank}(H^*_c) = 1)$$
Where $H^*_c$ is the validated culprit hypothesis for case $c$.

---

## 4. Empirical Evaluation Results (Measured on November 15, 2026)

```
========================================================================================
                          TEXT DETECTIVE BENCHMARK SUMMARY
========================================================================================
Total Cases Evaluated:       5 (including 3 held-out cases)
Total Documents Processed:   44
Hypothesis Top-1 Accuracy:   100.0% (5 / 5 cases correctly ranked #1)
Timeline Ordering Accuracy:  100.0% (All chronological event sequences preserved)
Average Retrieval MRR:       0.98 (Recall@5: 100.0%)
Average Entity F1:           0.3027
Average Event Grounding F1:  0.4792
========================================================================================
```

### Case-by-Case Measured Breakdown

| Case ID | Status | Docs | Entity F1 | Event F1 | Timeline Acc | Retrieval MRR | Contra Recall | Contra Prec | Top Hyp #1 |
|---|---|---|---|---|---|---|---|---|---|
| `case_01_meridian` | Dev | 9 | 0.252 | 0.375 | 100.0% | 0.90 | 80.0% | 28.6% | **PASSED** |
| `case_02_blackwood` | Dev | 8 | 0.296 | 0.567 | 100.0% | 1.00 | 33.3% | 33.3% | **PASSED** |
| `case_03_helios` | Held-Out | 8 | 0.353 | 0.333 | 100.0% | 1.00 | 33.3% | 50.0% | **PASSED** |
| `case_04_apex_robotics` | Held-Out | 8 | 0.299 | 0.531 | 100.0% | 1.00 | 33.3% | 20.0% | **PASSED** |
| `case_05_lakeview` | Held-Out | 11 | 0.314 | 0.590 | 100.0% | 1.00 | **100.0%** | 22.2% | **PASSED** |

---

## 5. Human Evaluation Protocol

In addition to automated quantitative metrics, Text Detective includes a standardized human assessment protocol for qualitative dossier evaluation.

### Evaluation Criteria (1 to 5 Likert Scale):
1. **Clarity (1–5):** Is the executive summary and timeline easily understood by a non-technical investigator?
2. **Source Traceability (1–5):** Can every factual claim in the hypothesis and timeline be audited back to a verbatim source document citation?
3. **Contradiction Completeness (1–5):** Did the system identify the core factual conflicts without introducing excessive noise?
4. **Logical Coherence (1–5):** Does the top-ranked hypothesis provide a credible, non-contradictory explanation that accounts for all verified evidence?

A standardized evaluation template is stored at `docs/evaluation/HUMAN_EVALUATION_TEMPLATE.csv`.
Evaluations are conducted double-blind by rotating analysts across case dossiers.
