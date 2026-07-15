# PolicyGPT RAG Evaluation Dataset

## Purpose

This directory contains the human-authored ground truth for Phase 2, Step 11.
It is a compact benchmark for checking whether PolicyGPT retrieves the right
policy pages, cites them, includes material answer facts, and declines questions
that the source cannot support.

Step 11 defines and validates the dataset only. Step 12 will implement automated
execution and scoring. Nothing in this directory calls the API, an embedding
model, ChromaDB, Groq, or OpenAI.

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

## Limitations and preparation for Step 12

- This small benchmark covers one fictional handbook and is not statistically
  representative of real HR or compliance corpora.
- Keyword ground truth cannot capture every acceptable answer formulation.
- Expected pages identify source relevance; they do not prescribe a future
  retrieval rank or confidence score.
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

The current local ChromaDB collection appears to contain repeated copies of the
sample PDF. Before Step 12 is run, reset the vector collection and index
`examples/sample_hr_policy.pdf` exactly once so duplicate vectors do not distort
retrieval or scoring metrics. Step 11 does not alter or delete ChromaDB data.
