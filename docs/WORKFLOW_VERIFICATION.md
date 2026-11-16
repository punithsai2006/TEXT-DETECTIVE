# Integrated workflow verification

Verified on Windows with Python 3.14 on 2026-11-16. See
[setup, configuration and walkthrough](CASE_WORKFLOW.md).

## Automated checks

- Starting suite: 95 tests passed. Final suite: **109 passed** in 42.49 seconds.
  One Starlette/httpx TestClient deprecation warning remains.
- `npm.cmd --prefix frontend run build`: passed. Vite warns about the existing
  bundle size above 500 kB; this is not a production performance assessment.
- `git diff --check`: passed.
- Tests cover case persistence/isolation, exact spans, contextual comparison
  contracts, ambiguous identities, deterministic score deduplication, abstention,
  answer-key exclusion, review/staleness, resumable checkpoints, provider-mode
  separation, report contents and download formats. Scripted model responses
  test orchestration contracts rather than real reasoning accuracy.
- A generic hypothesis question initially abstained despite persisted evidence.
  The assistant now retrieves linked hypothesis passages even without keyword
  overlap; its regression test and the final suite pass.

## Browser walkthrough

Using the explicitly labelled fixture server on port 8005, created
`Workflow QA — synthetic fixture` with two synthetic files. Verified:

1. Name/description, multiple uploads and all ten completed processing stages.
2. Two chronological events, attribution/time basis and exact-source inspection.
3. Interactive graph: eight nodes, six sourced edges, node and edge inspectors.
4. Two competing hypotheses tied at 1.8, all six score components, source links,
   assumptions and missing evidence; no leader; unscored other explanation.
5. Exact evidence search returns the original locked-door passage and links.
6. Cited assistant answer explains the tie; previous questions persist.
7. Accepted a finding as a lead with notes; restart preserved the case and review.
8. Generated and previewed the persisted report with hypotheses, timeline,
   relationships, quotations and review state; PDF download completed.

Screenshot: `output/screenshots/workflow-report.jpg`. Synthetic browser case ID:
`case_01a26287`. Existing user cases were not used as evaluation data.

## Report rendering and measured evaluation

`output/pdf/text-detective-fixture-report.pdf` was rendered with Poppler and all
four pages visually inspected, including score details, graph and appendix.
The report is clearly marked scripted/fixture only.

The tiny two-document mechanics evaluation recorded lexical Recall@1 of 2/2,
valid citation locators 2/2 and exact quotations 2/2. Fixture pipeline latency was
12.054 seconds with ten scripted provider calls. These counts are not real-model
accuracy, latency or cost estimates. Results:
[case workflow](evaluation/case_workflow_results.json) and
[pilot safeguards](evaluation/evidence_review_results.json).

The pilot safeguard checks matched/deferred as expected for 12/12 pairs; five
were explicitly deferred. They do not establish contradiction precision/recall.

## Blocked and remaining checks

The configured provider is mock and no live cloud-provider credentials were
configured. Real extraction, semantic verification, hypothesis quality, report
quality, contradiction precision/recall, token usage/cost and real-model latency
remain unmeasured. The normal endpoint rejects mock analysis; only the explicit
fixture demo injects scripted responses. No held-out real-model benchmark was
completed.

OCR/audio remain deferred. Entity resolution is conservative. Bounded retrieval
and candidate generation can miss evidence; model verification can be wrong.
This local prototype lacks multi-user authentication, encryption at rest and
parser sandboxing. Source-backed suggestions and human acceptance never prove
what occurred. See the setup guide for all processing limits.
