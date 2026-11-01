# Text Detective: Engineering Hardening & Improvement Roadmap

> **Target Milestone:** Final B.Tech Capstone Project Submission & Demonstration  
> **Guiding Principle:** Correctness → Security → Evidence Reliability → Evaluation Integrity → Usability → Documentation.

---

## 1. Prioritized Action Items

### Phase 1: Security & Repository Hygiene (Priority: CRITICAL)
- [x] Audit tracked files for credentials and binary database files.
- [ ] Update `.gitignore` to explicitly ignore `.env`, `*.env`, and binary Chroma databases.
- [ ] Untrack `backend/.env` from git index while preserving the local file.
- [ ] Untrack `storage/chroma/chroma_db/chroma.sqlite3` from git index.
- [ ] Fix CORS configuration in `backend/app/main.py` by removing wildcard `"*"` when `allow_credentials=True`.

### Phase 2: Evaluation Integrity & Scientific Metrics (Priority: CRITICAL)
- [ ] Audit `scripts/evaluate.py` for hardcoded metrics.
- [ ] Replace hardcoded `recall = 1.0` in `evaluate_event_extraction` with genuine ground-truth alignment against `true_timeline`.
- [ ] Compute true event precision, recall, and F1 based on participant, timestamp, and action verb overlap.
- [ ] Re-run evaluation harness and generate updated benchmark results.

### Phase 3: Contradiction Detection & Detection Engine Tracking (Priority: HIGH)
- [ ] Add `detection_engine: str = "rules"` (`nli`, `rules`, or `llm_verified`) to `ContradictionItem` schema.
- [ ] Connect `_get_nli_pipeline()` in `backend/app/services/contradiction/detector.py` to attempt NLI first when optional transformers dependency is present.
- [ ] Wire LLM judge verification for borderline cases ($0.60 \le \text{confidence} < 0.85$).
- [ ] Update `frontend/src/types/index.ts` and `frontend/src/components/ContradictionCard.tsx` to display the detection engine badge.

### Phase 4: Atomic Batch Uploads & Storage Reliability (Priority: HIGH)
- [ ] Ensure multi-file upload in `backend/app/api/routes.py` is atomic: if any file fails validation or processing, clean up all written files in that batch to avoid orphaned disk records.
- [ ] Add explicit detection for zero-byte empty uploads and scanned image PDFs.
- [ ] Implement atomic file writing in `backend/app/storage/case_store.py` using `.tmp` files and `os.replace` to prevent JSON corruption during abrupt shutdowns.

### Phase 5: UI Accessibility & Evidence Traceability (Priority: MEDIUM)
- [ ] In `frontend/src/pages/ReportPage.tsx`, support clicking source citations (`[Doc: ...]`) to open an evidence modal or scroll directly to the matching excerpt.
- [ ] Add accessible text/table fallback view in `CaseGraphPage.tsx` and `TimelinePage.tsx` for screen-reader and structured review.
- [ ] Ensure mobile responsiveness across 360px, 768px, and 1280px viewports.

### Phase 6: QA, Testing & Demo Documentation (Priority: MEDIUM)
- [ ] Add automated unit tests for detection engine tracking, atomic batch upload error handling, and genuine event recall calculation.
- [ ] Run full automated test suite to ensure 100% pass rate.
- [ ] Verify production frontend build (`npm run build`).
- [ ] Author `docs/DEMO_SCRIPT.md` detailing the 5-minute investigation walkthrough.
- [ ] Update `README.md` with verified setup instructions and limitations.
