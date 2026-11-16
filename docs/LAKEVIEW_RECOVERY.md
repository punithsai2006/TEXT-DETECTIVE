# Lakeview LV-3112 recovery and verification

## Why repeated retries failed

The screenshots show `LLM_PROVIDER=mock`. The production analysis service blocks
mock inference by design. Repeating the request cannot install a model or supply
credentials. The old Render blueprint explicitly selected mock mode. A later
local workaround automatically enabled fixtures; that bypass has been removed.

The updated UI shows configuration guidance before analysis, preserves uploads,
offers upload-only and Evidence Search, and avoids a blocking browser alert on
the dashboard. Missing-provider requests return HTTP 409 before creating another
failed run. Partial comparison batches expose their progress and publish only
source-backed intermediate views. A retry advances cached pairs; incomplete
comparisons are never passed to completed-report synthesis.

## Render configuration: OpenAI only

The user authorized these 11 synthetic documents to OpenAI only. The ground-truth
JSON must not be uploaded to evidence or included in any model prompt.

In the EXISTING Render service, open Environment and set:

```text
LLM_PROVIDER=openai
LLM_MODEL=<exact model ID available to your OpenAI API account>
OPENAI_API_KEY=<your API key, entered only in Render>
DEMO_MODE=false
ALLOW_MODEL_DOWNLOADS=false
```

Never put the key in frontend code, Git, screenshots, documents or this chat.
The selected model must support the existing chat-completions adapter. No model
ID or account access has been assumed or verified. A ChatGPT subscription alone
does not configure this backend API credential.

Deploy the updated code and save/redeploy the environment settings. Changing
`render.yaml` alone does not prove the existing service's environment changed.
The blueprint now requests a model ID and secret instead of selecting mock.
Use **Check provider again** on New Investigation; metadata readiness does not
prove successful generation. Then run the existing case's analysis.

The deployment still uses container-local storage unless a persistent disk is
configured separately. Preserve/download evidence and reports before replacing
the container; the original ZIP permits re-uploading the 11 documents. This work
did not modify the live Render service or claim production security readiness.

## Correct upload

Extract `Lakeview_Library_Case_LV-3112.zip`. Upload the 11 TXT files in
`lakeview_case/documents/`. Keep `lakeview_case/ground_truth/` separate. ZIP upload
now displays these instructions instead of silently ignoring the archive.

## Actual verification on 2026-11-17

- Final backend suite: **123 passed** in 26.26 seconds, including the supplied
  archive. One Starlette/httpx TestClient deprecation warning remains.
- Frontend build: passed. The main bundle is 588.71 kB and retains Vite's bundle
  size warning. Built assets were refreshed for the deployment's static serving.
- Archive SHA-256: `9ed21129f2beda0070d5cc4540bddffb08941b4fd30f0f965a2e083d192c7c05`.
- 11/11 documents parsed, 35 exact source spans, no ground truth indexed.
- Source locators: 35/35 passed; quotations versus extracted offsets: 35/35 passed.
- Six manually labelled retrieval probes: Recall@5 = 6/6; MRR@5 = 0.8889.
  These measure lexical retrieval on six queries, not general model accuracy.
- Explicit offline preview exercised the integrated graph/timeline/report,
  five-role orchestration, persistent report, question abstention and correction
  staleness. It emits uninterpreted passages, unknown times and an unscored
  insufficient-evidence alternative. It does not solve the case or claim semantic
  verification. Modern mock requests no longer invent dates or approve arbitrary
  assertions.
- Browser checked the configuration warning, disabled AI execution when missing
  a provider, evidence retrieval with the expected badge log ranked first, and
  exact-source inspection showing filename, paragraph, offsets and original.
- Real-model generation remains blocked: local configuration has no OpenAI key.
  No paid generation or archive transmission occurred. A guarded real-mode
  command refuses every provider other than the authorized OpenAI adapter.

## Manual comparison with the supplied answer key

This table is a human source review, NOT a measured or generated model result.
Paragraphs refer to extracted blank-line-separated paragraphs, not visual lines.

| Reference lead | Exact supporting source locations | Appropriate interpretation |
|---|---|---|
| Tom denies returning after approximately 17:30; card re-entry at 18:02 | `03_interview_tom_reyes.txt`, paragraph 2, dialogue 11:01; `06_badge_access_log.txt`, paragraph 2, row 18:02:19 | Potential conflict, conditional on who used the card and event/clock alignment. |
| Tom denies opening the case; KEY_02 unlock at 18:16 | `03_interview_tom_reyes.txt`, paragraph 2, dialogue 11:03; `07_alarm_and_case_lock_log.txt`, paragraph 2, row 18:16:33; paragraph 3 identifies assignment | Key activity conflicts with a personal-use account only if exclusive custody/use is established. Assignment alone does not establish the operator. |
| Tom says he had already gone home; Greg reports seeing him with a tube | `03_interview_tom_reyes.txt`, paragraph 2, dialogue 11:04; `05_interview_greg_hall.txt`, paragraph 2, dialogue 13:03; `10_cleaning_shift_log.txt`, paragraph 2, row 18:29 | Competing attributed accounts. Greg's interview and his shift log are not independent witnesses. One person seeing another does not itself prove mutual recognition. |
| Denial of dealer contact about this map versus valuation email | `03_interview_tom_reyes.txt`, paragraph 2, dialogue 11:05; `09_dealer_email.txt`, paragraph 1 (author/date) and paragraph 3 (valuation request) | Potential conflict about a matching 1824 Lakeview map, subject to identifying the asset. The email does not establish a completed sale. |
| Nina's approximate 16:30 departure versus 16:32 badge exit | `04_interview_nina_patel.txt`, paragraph 2, dialogue 12:03; `06_badge_access_log.txt`, paragraph 2, row 16:32:09 | Ordinarily compatible in this context; do not flag merely because two minutes differ. |

The reference's leading explanation is an investigation hypothesis, not proof:
`08_cctv_review_report.txt`, paragraphs 5-6, explicitly leaves the face partly
hidden and the tube's contents unestablished. `01_incident_report.txt`, paragraph
6, says no sale/transfer is confirmed. The reference's 09:00 library opening is
not explicitly stated in these documents and should not be invented. Discovery
at approximately 08:00 and reporting at 08:05 are separate events.

Real-model contradiction precision/recall, hypothesis agreement and semantic
support accuracy remain **unmeasured**, rather than being filled with fixture
scores or forced answer-key conclusions.

## Reproduce locally (PowerShell, repository root)

```powershell
.\.venv\Scripts\python.exe scripts/verify_case_archive.py "C:\Users\punit\Downloads\Text_Project\Lakeview_Library_Case_LV-3112.zip" --mode inspect
.\.venv\Scripts\python.exe scripts/verify_case_archive.py "C:\Users\punit\Downloads\Text_Project\Lakeview_Library_Case_LV-3112.zip" --mode offline-preview
# Only after OpenAI credentials/model are configured; sends evidence to OpenAI:
.\.venv\Scripts\python.exe scripts/verify_case_archive.py "C:\Users\punit\Downloads\Text_Project\Lakeview_Library_Case_LV-3112.zip" --mode real --output output/lakeview-real-check
$env:TEXT_DETECTIVE_CASE_ARCHIVE="C:\Users\punit\Downloads\Text_Project\Lakeview_Library_Case_LV-3112.zip"
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd --prefix frontend run build
```

The runner uses isolated `output/` storage, never existing user cases. Results
are in `output/lakeview-verification/verification.json`. The offline report is a
source-preview rendering test; its unknown-time items are not an extracted
chronology. Answer-key data is read only after analysis/indexing and remains
outside prompts and persisted evidence.

On real-model failures, inspect the saved run's schema errors/model budget and
retry successful checkpoints. The runner currently performs one bounded batch;
interactive case retries continue pending comparisons. It deliberately cannot
silently multiply the per-request budget to finish every pair.
