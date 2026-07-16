# PolicyGPT RAG Evaluation Dataset

## Purpose

This directory contains the human-authored ground truth from Phase 2, Step 11,
the repeatable evaluation runner added in Step 12, and the explainable
confidence diagnostics added in Step 13. The benchmark checks
whether PolicyGPT retrieves the right policy pages, cites them, includes material
answer facts, and declines questions that the source cannot support.

`scoring.py` contains pure, unit-tested scoring functions. `run_eval.py` owns the
CLI, HTTP calls, response validation, orchestration, and result writing. The
runner calls the existing PolicyGPT API; it does not import or duplicate the
production retrieval or answer-generation pipeline.

## Calibrated evidence confidence

The production retrieval path assesses up to three highest-scoring, unique
chunks at or above the configured candidate floor. The default floor is `0.30`;
it only controls which evidence is assessed and is not an answer threshold.
The calibrated answerability score is:

```text
0.35 * top retrieval score
+ 0.15 * average candidate retrieval score
+ 0.45 * combined lexical coverage
+ 0.05 * normalized retrieval margin
```

The retrieval margin is `(top - second) / 0.15`, bounded to `[0, 1]`. A single
candidate receives a conservative margin of zero. Public values are rounded to
four decimal places.

Evidence is classified as `insufficient`, `weak`, `moderate`, or `strong`; only
`moderate` and `strong` evidence can generate an answer. Exact top-chunk support
may promote evidence to `moderate` when its retrieval score is at least `0.35`
and lexical coverage is at least `0.60`. A missing numeric claim or unresolved
external legal-authority request is always rejected, regardless of score.

The API retains the top-level `confidence_score`. It reports the calibrated
score for answer-ready results and zero for fallbacks. The optional
`confidence_breakdown` contains safe component metrics, normalized terms,
numeric claims, guardrail flags, and decision reasons; it never contains full
evidence or prompts.

## Source document

All supported records were verified against
`examples/sample_hr_policy.pdf`, a 12-page fictional handbook for AtlasWorks AI
Inc. The sample contains no real employee or company data and is not legal or HR
advice.

Run the reproducible page-level inspection from the project root:

```bash
python eval/inspect_sample_policy.py
```

An alternate PDF can be inspected by passing its path:

```bash
python eval/inspect_sample_policy.py path/to/document.pdf
```

The inspection script reuses the production `PDFExtractionService`, which uses
PyMuPDF and preserves one-based page numbers.

## Verified page-to-topic mapping

| Page | Verified topic |
| ---: | --- |
| 1 | Handbook metadata, scope, and suggested test questions |
| 2 | Table of contents and RAG testing note |
| 3 | Employment classifications, schedules, breaks, and overtime approval |
| 4 | Attendance, vacation notice, sick time, emergency leave, and statutory leaves |
| 5 | Remote/hybrid eligibility, work-location limits, equipment allowance, availability, and home security |
| 6 | Professional conduct, respectful workplace, manager responsibility, and conflicts of interest |
| 7 | Confidentiality, minimum-necessary access, AI-tool restrictions, approved AI use, and personal information |
| 8 | Account, device, software, phishing, and company-system security rules |
| 9 | Expense reimbursement, receipt rules, submission deadline, travel, and excluded expenses |
| 10 | Performance reviews, goals, coaching, corrective action, and documentation |
| 11 | Reporting channels, reportable concerns, non-retaliation, investigations, and false reports |
| 12 | Acknowledgment, policy updates, contract limits, and RAG demo limitations |

Expected pages use the substantive policy page where the answer appears, not the
table of contents or the suggested-question list on the front page.

## Dataset format

`questions.jsonl` contains one JSON object per non-empty line with these fields:

| Field | Meaning |
| --- | --- |
| `id` | Stable, unique lowercase identifier |
| `question` | Natural-language enterprise policy question |
| `expected_answer_keywords` | Up to six short facts or terms expected in a supported answer |
| `expected_pages` | One-based PDF pages containing the supporting facts |
| `should_answer` | Whether the source contains enough information to answer |
| `category` | Policy topic or unsupported-query class |
| `difficulty` | `easy`, `moderate`, or `hard` |
| `evaluation_focus` | Scoring dimensions relevant to the question |
| `notes` | Human rationale describing what the record tests |

The dataset has exactly 16 records: 11 supported and 5 unsupported. Unsupported
records intentionally have empty expected keyword and page lists.

## Difficulty definitions

- `easy`: A direct fact or short rule found in one clearly relevant passage.
- `moderate`: A paraphrased rule, two related details, or an important condition
  that must be included for a useful answer.
- `hard`: Multiple decision factors, a deadline plus an exception, or a normal
  rule whose limitation must be included to avoid a misleading answer.

The fixed distribution is six easy, six moderate, and four hard questions.

## Evaluation-focus values

- `retrieval`: The relevant source passage should be retrieved.
- `citation`: The answer should cite the expected one-based PDF page.
- `answer_content`: The answer should cover the material policy facts.
- `fallback`: The system should decline because the source lacks evidence.
- `condition`: An eligibility, approval, or decision condition matters.
- `exception`: A limitation or exception must be preserved.
- `deadline`: A time period or notice/reporting deadline must be accurate.
- `numeric_accuracy`: A monetary threshold or other number must be accurate.

## Interpreting expected keywords

Keywords are normalized semantic checkpoints, not a complete reference answer
and not an exact-order string match. Amounts, time periods, approval authorities,
prohibitions, and exceptions retain the terminology used in the PDF. A future
scorer should compare case-insensitively and tolerate reasonable phrasing while
requiring every material fact represented by the list.

For example, `CAD 300`, `receipts are required`, and `approved before
reimbursement` represent separate facts. An answer that mentions only the amount
is incomplete even if its wording is fluent.

## Validation

The validator uses only the Python standard library:

```bash
python eval/validate_dataset.py
python -m pytest -q
```

It checks JSONL structure, required fields, record and support counts, unique
IDs, supported/unsupported ground-truth rules, allowed values, and the exact
difficulty distribution. The tests additionally verify page bounds against the
actual PDF and confirm that supported keywords occur on their expected pages.

## Running the evaluation

The evaluation requires a running FastAPI backend and an indexed source
document. Start the backend from the project root:

```bash
python -m uvicorn app.api.main:app \
  --reload \
  --reload-dir app \
  --host 0.0.0.0 \
  --port 8000
```

Before comparing metrics, reset the vector collection manually and index
`examples/sample_hr_policy.pdf` exactly once. The runner never deletes or
modifies ChromaDB data.

Run all 16 questions:

```bash
python eval/run_eval.py
```

Run one exact benchmark record for debugging:

```bash
python eval/run_eval.py --question-id remote_work_001
```

Run only the first three records:

```bash
python eval/run_eval.py --limit 3
```

Pace evaluation requests when a provider has tight rate limits:

```bash
python eval/run_eval.py --request-delay-seconds 2
```

This delay applies only between benchmark questions and is not production
request throttling.

Other options configure the base URL, dataset, output directory, retrieval
`top_k`, request timeout, health-check behavior, and whether the first request
error should stop the run. `--limit` and `--question-id` are mutually exclusive.

### Metrics

- **Answer readiness accuracy:** Fraction of all evaluated cases where
  `answer_ready` equals the benchmark's `should_answer` value.
- **Fallback accuracy:** Fraction of unsupported cases that return
  `answer_ready=false`, `fallback_used=true`, and zero citations.
- **Retrieval page hit rate:** Fraction of successfully processed supported
  cases where at least one expected page is cited.
- **Keyword match rate:** Macro average of supported-case keyword match scores.
  Unsupported cases have a null keyword score and are excluded.
- **Average confidence:** Mean API-provided confidence across successfully
  processed cases; the runner does not recalculate confidence.
- **Average supported confidence:** Mean API confidence for successfully
  processed supported cases only.
- **Average latency:** Mean client-observed end-to-end request latency.
- **Average citations:** Mean citation count across all evaluated cases.

Per-question JSON and CSV rows also record the optional confidence component
scores, numeric and scope flags, direct-support result, and decision reasons.
Object and list values in CSV are encoded as JSON strings.

Confidence is recorded as observed data and is not a direct pass/fail gate.
A supported case passes only when it is answer-ready, cites an expected page,
and matches every expected keyword. An unsupported case passes only when it
uses the zero-citation fallback correctly.

### Result files and exit codes

Each completed run atomically replaces:

```text
eval/results/latest_eval_results.json
eval/results/latest_eval_results.csv
```

The JSON artifact is the source of truth for run metadata, aggregate metrics,
and per-question results. The CSV contains one row per question and serializes
list fields as JSON strings. Both generated files are ignored by Git; only
`eval/results/.gitkeep` is tracked.

The runner returns exit code 0 when the evaluation completes, even if individual
cases fail. It returns non-zero for invalid arguments or datasets, an unavailable
required health check, result-writing failure, or a request error when
`--fail-on-request-error` is enabled.

If repeated citation cards share the same filename, page, chunk index, and
excerpt, the runner records their count and prints a duplicate-citation warning.
This warning does not fail a case and never triggers an automatic ChromaDB reset.

## Next.js evaluation product

Phase 14C exposes the latest generated artifacts through read-only FastAPI
endpoints:

```text
GET /api/v1/evaluations/latest
GET /api/v1/evaluations/latest.csv
```

The Next.js product routes are `/evaluations/overview`, `/evaluations/cases`,
`/evaluations/confidence`, `/evaluations/provider`, and
`/evaluations/runs/latest`. Browser downloads use same-origin Next.js routes;
the frontend never reads the backend filesystem or starts the evaluator.

The JSON `summary` remains authoritative. The product derives presentation
groupings and primary diagnostic categories without recalculating official
metrics. Partial artifacts are labeled diagnostic runs, and distributions are
suppressed when fewer than three cases are present. Provider citation-only
fallback is reported independently from evidence retrieval and unsupported
answer safety.

Confidence describes calibrated evidence support, not an LLM self-rating.
The Streamlit evaluation dashboard remains the internal QA console. Persistent
PostgreSQL evaluation history remains pending.

## Limitations

- This small benchmark covers one fictional handbook and is not statistically
  representative of real HR or compliance corpora.
- Keyword ground truth cannot capture every acceptable answer formulation.
- Keyword matching is normalized exact phrase matching; it intentionally does
  not use stemming, fuzzy matching, embeddings, or semantic similarity.
- Expected pages identify source relevance; they do not prescribe a future
  retrieval rank or confidence score.
- Latency is measured by the client and includes local networking and API work,
  so it is not a provider-only or server-only timing measurement.
- Unsupported questions verify absence from this source, not truth in the real
  world or applicability of external law.
- This benchmark is for software evaluation only and does not represent legal,
  employment, privacy, security, or HR advice.

Several tempting questions were deliberately excluded because the handbook does
not define enough ground truth: exact meal/rest-break lengths, whether statutory
leaves are paid and how long they last, specific benefit eligibility by worker
classification, and jurisdiction-specific overtime or severance calculations.
Those subjects are mentioned only generally or deferred to local law, so assigning
keywords or answer pages would create false precision.

For comparable local runs, use a clean vector collection with
`examples/sample_hr_policy.pdf` indexed exactly once. Duplicate vectors can
distort retrieval and confidence component metrics; the evaluator reports
duplicate citation cards but never modifies ChromaDB data.
