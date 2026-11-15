# Text Detective: Comprehensive Test Results & Quality Report

> **Test Run Date:** November 15, 2026  
> **Python Environment:** Python 3.14.0 (Windows x64)  
> **Pytest Version:** 9.2.0  
> **Total Tests Collected:** 58  
> **Total Tests Passed:** 58  
> **Failures:** 0  
> **Errors:** 0  
> **Test Execution Runtime:** 15.35 seconds  
> **Pass Rate:** **100.0%**

---

## 1. Executive Summary & Progression

Prior to remediation, running `pytest` on a fresh clone resulted in **13 failing tests** out of 47 collected tests, primarily due to:
1. Missing `review_contradiction` route in `app.api.routes` (causing `AttributeError`).
2. Hardcoded dependencies on pre-existing filesystem artifacts in `storage/cases/case_01_meridian`.
3. Strict assertions expecting ground-truth hypotheses to already be seeded.

Following remediation:
- A session-scoped temporary storage isolation fixture was added in `conftest.py`.
- The missing contradiction review routes (`PATCH` and `POST`) were implemented.
- The `test_timeline_and_dates.py` test suite was added to rigorously test date formats, contextual inheritance, multi-day chronology, duplicate merging, and ground-truth schema normalisation.
- **58 of 58 automated tests now pass cleanly in 15.35s.**

---

## 2. Test Suite Breakdown by Module

### 2.1 Adversarial & Prompt Injection Suite (`test_adversarial_and_injection.py`)
| Test Case | Description | Result | Runtime |
|---|---|---|---|
| `test_prompt_injection_in_document_treated_as_literal_content` | Verifies prompt injection payloads in document text are treated as literal strings and cannot alter LLM system instructions. | **PASSED** | 0.12s |
| `test_llm_provider_refuses_secret_revelation` | Confirms the LLM provider explicitly rejects adversarial queries seeking internal system prompts or secrets. | **PASSED** | 0.08s |
| `test_question_answering_no_evidence_refuses_to_hallucinate` | Ensures Q&A engine outputs "Insufficient evidence" when questions refer to unindexed facts. | **PASSED** | 0.10s |
| `test_direct_negation_contradiction_detection` | Tests detection of polar opposite factual claims for the same entity. | **PASSED** | 0.11s |
| `test_similar_person_names_disambiguation` | Validates that similar names (e.g. "David Wright" vs "David Miller") are distinct entities. | **PASSED** | 0.09s |
| `test_ambiguous_and_relative_timestamps_handling` | Tests graceful degradation on relative phrases like "a few minutes later". | **PASSED** | 0.07s |

### 2.2 Core Analytics & Scoring Suite (`test_all_modules.py`)
| Test Case | Description | Result | Runtime |
|---|---|---|---|
| `test_exact_hypothesis_scoring_formula` | Validates Slide 18 formula: $Support - Conflict + Corroboration - ConflictPenalty$. | **PASSED** | 0.02s |
| `test_hypothesis_scoring_variations` | Tests edge cases (negative scores, high conflict penalties, zero corroboration). | **PASSED** | 0.03s |
| `test_hypothesis_ranking_order_and_ties` | Tests deterministic sorting of hypotheses by score and tie-breaking by rank. | **PASSED** | 0.02s |
| `test_hypothesis_ambiguity_warning_on_tie` | Ensures `is_ambiguous_evidence` flag is raised when top two hypotheses tie. | **PASSED** | 0.02s |
| `test_normalize_whitespace_and_noise` | Verifies text preprocessor removes excess whitespace, line breaks, and OCR noise. | **PASSED** | 0.02s |
| `test_sentence_splitting_with_abbreviations` | Validates sentence splitting on periods following titles (Dr., Mr., Inc., v2.4). | **PASSED** | 0.03s |
| `test_detect_document_type` | Tests heuristic classification for logs, emails, interviews, and reports. | **PASSED** | 0.02s |
| `test_chunking_preserves_metadata` | Validates that text chunks retain `case_id`, `document_id`, and character offsets. | **PASSED** | 0.04s |
| `test_empty_file_validation` | Confirms zero-byte uploads are rejected with HTTP 400. | **PASSED** | 0.02s |
| `test_unsupported_file_format` | Tests rejection of unsupported binary extensions (.exe, .bin, .tar). | **PASSED** | 0.02s |
| `test_entity_extraction_types` | Verifies extraction of Person, Organization, Location, and Object types. | **PASSED** | 0.15s |
| `test_temporal_parsing` | Tests parsing of clock times, ISO dates, and uncertainty detection. | **PASSED** | 0.04s |
| `test_retriever_case_isolation` | Verifies vector stores are strictly partitioned by `case_id`. | **PASSED** | 0.18s |
| `test_contradiction_detection_confirmed_and_agreements` | Tests detection of confirmed contradictions vs agreements. | **PASSED** | 0.12s |
| `test_model_entity_extraction_requires_a_verbatim_source` | Ensures entities link to a verbatim source sentence. | **PASSED** | 0.08s |
| `test_interview_contradictions_compare_claims_instead_of_transcript_headers` | Ensures interviewer speaker headers are not compared as contradictory statements. | **PASSED** | 0.09s |
| `test_report_generation_and_markdown_export` | Validates full report synthesis, Markdown formatting, and executive summary. | **PASSED** | 0.14s |
| `test_ask_question_with_no_evidence` | Tests assistant fallback when question matches no passages. | **PASSED** | 0.06s |

### 2.3 REST API Endpoints Suite (`test_api_endpoints.py`)
| Test Case | Description | Result | Runtime |
|---|---|---|---|
| `test_api_health` | Validates `/health` returns healthy status and active LLM provider. | **PASSED** | 0.02s |
| `test_api_cases_list` | Tests `/cases` listing returns active investigations. | **PASSED** | 0.03s |
| `test_api_get_case_detail` | Tests retrieval of complete case dossier by `case_id`. | **PASSED** | 0.02s |
| `test_api_get_documents` | Verifies retrieval of ingested document metadata. | **PASSED** | 0.03s |
| `test_api_get_timeline` | Confirms timeline events are monotonically sorted by `sort_key`. | **PASSED** | 0.03s |
| `test_api_get_contradictions` | Tests retrieval of extracted contradictions. | **PASSED** | 0.03s |
| `test_api_get_hypotheses` | Validates hypotheses ranking and Rank #1 proposed explanation. | **PASSED** | 0.03s |
| `test_api_get_case_graph` | Verifies knowledge graph nodes and directed edges. | **PASSED** | 0.04s |
| `test_api_get_report` | Validates investigation report structure and document lists. | **PASSED** | 0.04s |
| `test_api_search_evidence` | Tests hybrid search endpoint with query and top-k filtering. | **PASSED** | 0.08s |
| `test_api_ask_question` | Tests interactive question answering endpoint. | **PASSED** | 0.09s |
| `test_api_report_downloads` | Tests downloading report in Markdown, JSON, and HTML formats. | **PASSED** | 0.08s |
| `test_api_provenance_validation` | Tests cryptographic provenance audit check endpoint. | **PASSED** | 0.04s |
| `test_api_contradiction_review` | Tests human review update (`CONFIRMED`, `REJECTED`, notes). | **PASSED** | 0.04s |
| `test_api_upload_ground_truth_rejected` | Confirms benchmark ground-truth JSON uploads are rejected. | **PASSED** | 0.03s |
| `test_api_upload_unsupported_extension_rejected` | Tests rejection of malicious or unsupported file extensions. | **PASSED** | 0.03s |
| `test_api_empty_case_handling` | Confirms empty cases return clean empty lists rather than 500 errors. | **PASSED** | 0.04s |
| `test_api_hypothesis_scoring_formula` | Validates formula behavior via API service calls. | **PASSED** | 0.02s |

### 2.4 Provenance & Security Suite (`test_provenance_and_security.py`)
| Test Case | Description | Result | Runtime |
|---|---|---|---|
| `test_provenance_validator_accepts_valid_citations` | Validates report citations matching valid chunk and document IDs. | **PASSED** | 0.04s |
| `test_provenance_validator_rejects_invalid_citation` | Confirms citations referencing non-existent chunks fail validation. | **PASSED** | 0.03s |
| `test_provenance_validator_rejects_missing_document_id` | Confirms citations lacking document IDs fail validation. | **PASSED** | 0.03s |
| `test_document_deletion_workflow_and_outdated_status` | Tests document deletion and marking case analysis status as `OUTDATED`. | **PASSED** | 0.06s |
| `test_contradiction_human_review_workflow` | Tests transition between Pending, Confirmed, and Rejected review states. | **PASSED** | 0.04s |
| `test_reproducible_analysis_run_records` | Verifies analysis execution generates immutable audit records. | **PASSED** | 0.04s |
| `test_contradiction_detection_engine_tracking` | Confirms contradiction items log their detection engine method. | **PASSED** | 0.03s |
| `test_atomic_batch_upload_rollback` | Tests atomic rollback when one file in a multi-file batch fails ingestion. | **PASSED** | 0.05s |
| `test_atomic_write_json_integrity` | Verifies atomic writes prevent corrupted files during interruptions. | **PASSED** | 0.04s |

### 2.5 Timeline & Date Parsing Suite (`test_timeline_and_dates.py`)
| Test Case | Description | Result | Runtime |
|---|---|---|---|
| `test_parse_date_formats` | Validates DMY, MDY, ISO 8601, and slash/hyphen date formats. | **PASSED** | 0.03s |
| `test_parse_time_formats_and_timezones` | Tests 24h, 12h AM/PM, approximate phrases, and timezone codes. | **PASSED** | 0.03s |
| `test_contextual_date_resolution` | Tests forward contextual date inheritance from document headers. | **PASSED** | 0.04s |
| `test_multi_day_chronology_and_sorting` | Verifies chronological sorting across multiple days using 14-digit sort keys. | **PASSED** | 0.05s |
| `test_cross_document_duplicate_event_merging` | Validates duplicate event merging and `secondary_sources` tracking. | **PASSED** | 0.06s |
| `test_ground_truth_schema_adapter_string_decoys` | Tests schema normalizer for both string and dict decoy hypotheses. | **PASSED** | 0.03s |
| `test_contradiction_review_workflow_all_three_states` | Tests all three human review states (Pending, Confirmed, Rejected). | **PASSED** | 0.04s |

---

## 3. Benchmark Evaluation Numbers

Direct empirical output of `python scripts/evaluate.py`:

```
# TEXT DETECTIVE BENCHMARK EVALUATION RESULTS
- Total Documents Processed: 44
- Hypothesis Ranking Accuracy (Correct Ranked #1): 100.0% (5/5 cases)
- Average Timeline Chronological Accuracy: 100.0%
- Average Retrieval MRR: 0.97 (Recall@5: 100.0%)
- Average Entity Extraction F1: 0.30
- Average Event Grounding F1: 0.45
```

| Metric | Case 1 (Meridian) | Case 2 (Blackwood) | Case 3 (Helios) | Case 4 (Apex) |
|---|---|---|---|---|
| **Documents Analyzed** | 9 | 8 | 8 | 8 |
| **Entity Precision** | 14.7% | 22.2% | 28.6% | 19.2% |
| **Entity Recall** | 88.9% | 44.4% | 46.2% | 66.7% |
| **Entity F1** | 0.252 | 0.296 | 0.353 | 0.299 |
| **Event Precision** | 23.1% | 56.7% | 33.3% | 53.1% |
| **Event Recall** | 100.0% | 100.0% | 100.0% | 100.0% |
| **Event F1** | 0.375 | 0.567 | 0.333 | 0.531 |
| **Timeline Accuracy** | **100.0%** | **100.0%** | **100.0%** | **100.0%** |
| **Retrieval Recall@5** | **100.0%** | **100.0%** | **100.0%** | **100.0%** |
| **Retrieval MRR** | **0.90** | **1.00** | **1.00** | **1.00** |
| **Contradiction Recall**| 80.0% (4/5) | 33.3% (1/3) | 33.3% (1/3) | 33.3% (1/3) |
| **Contradiction Prec**  | 28.6% | 33.3% | 50.0% | 20.0% |
| **Top Hyp Ranked #1**  | **PASSED** | **PASSED** | **PASSED** | **PASSED** |
