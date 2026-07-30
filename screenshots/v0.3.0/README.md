# PolicyGPT Enterprise v0.3.0 screenshot gallery

These are verified v0.3.0 repository captures from the running local PolicyGPT Enterprise application. They document the local release profile; they do not imply a cloud-hosted product deployment.

The evaluation screens record a controlled 16-case run with answer generation disabled: all 11 supported cases remained answer-ready and preserved page-level citations through citation-only fallback, while all 5 unsupported cases returned the expected zero-citation fallback. Because no generated answers were produced, generated-answer content and keyword quality were not validated.

Return to the [PolicyGPT Enterprise README](../../README.md).

## 1. Citation-backed answer

<img src="01-policygpt-citation-backed-answer.png" alt="PolicyGPT Enterprise citation-backed policy answer with calibrated confidence and page-level evidence" width="100%" />

*Evidence-backed remote-work policy answer with calibrated confidence and page-level source citations.*

## 2. Evidence and confidence diagnostics

<img src="02-policygpt-evidence-confidence-diagnostics.png" alt="PolicyGPT Enterprise explainable evidence and confidence diagnostics" width="100%" />

*Explainable answerability diagnostics showing retrieval strength, lexical coverage, direct support, scope risk, provider state, and page-level evidence.*

## 3. Unsupported-answer fallback

<img src="03-policygpt-unsupported-answer-fallback.png" alt="PolicyGPT Enterprise controlled unsupported-answer fallback" width="100%" />

*Controlled unsupported-answer state that blocks generation when indexed policies provide no usable evidence.*

## 4. Document registry

<img src="04-policygpt-document-registry.png" alt="PolicyGPT Enterprise persistent document registry and lifecycle metadata" width="100%" />

*Persistent document registry connecting PostgreSQL lifecycle metadata, original PDF storage, and ChromaDB evidence indexing.*

## 5. Document detail

<img src="05-policygpt-document-detail.png" alt="PolicyGPT Enterprise safe document metadata and evidence-indexing detail" width="100%" />

*Document detail view connecting safe source metadata, processing history, Chroma collection identity, and the pinned embedding model without exposing storage paths.*

## 6. Evaluation overview

<img src="06-policygpt-evaluation-overview.png" alt="PolicyGPT Enterprise controlled RAG evaluation overview" width="100%" />

*Controlled RAG benchmark showing retrieval quality, unsupported-answer safety, provider availability, and production-style quality gates.*

## 7. Supported evaluation cases

<img src="07a-policygpt-supported-evaluation-cases.png" alt="PolicyGPT Enterprise supported evaluation cases stacked at readable width" width="100%" />

*All 11 supported cases retained answer-ready evidence and expected-page citations; full generated-answer keyword quality was not validated in this provider-disabled run.*

## 8. Unsupported evaluation cases

<img src="07b-policygpt-unsupported-evaluation-cases.png" alt="PolicyGPT Enterprise unsupported evaluation cases stacked at readable width" width="100%" />

*All 5 unsupported cases exercised the controlled zero-citation fallback rather than permitting unsupported generation.*

## 9. Confidence diagnostics

<img src="08-policygpt-confidence-diagnostics.png" alt="PolicyGPT Enterprise benchmark confidence and evidence diagnostics" width="100%" />

*Benchmark-scoped confidence diagnostics separating answerability, retrieval strength, direct support, numeric consistency, and scope-risk guardrails.*

## 10. Provider reliability

<img src="09-policygpt-provider-reliability.png" alt="PolicyGPT Enterprise provider-disabled reliability and citation-only fallback view" width="100%" />

*Provider-disabled benchmark state showing 11 answer-ready cases preserved as citation-only fallback and no generated-answer quality claim.*

## 11. System readiness

<img src="10-policygpt-system-readiness.png" alt="PolicyGPT Enterprise dependency-aware local system readiness" width="100%" />

*Dependency-aware system status separating process liveness, PostgreSQL and ChromaDB readiness, provider configuration, and honest production boundaries.*

## 12. Evaluation run details

<img src="11-policygpt-evaluation-run-details.png" alt="PolicyGPT Enterprise local evaluation run metadata and artifact downloads" width="100%" />

*Read-only run provenance for the 16-case local benchmark, including dataset hash, configuration, timestamps, coverage, and JSON/CSV artifact downloads.*

## 13. Upload workflow

<img src="12-policygpt-upload-workflow.png" alt="PolicyGPT Enterprise controlled PDF upload and synchronous evidence-indexing workflow" width="100%" />

*Controlled PDF-ingestion workflow connecting persistent metadata, source storage, extraction, embedding generation, and synchronous evidence indexing.*
