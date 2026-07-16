from dataclasses import fields

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.services.confidence_service import (
    ConfidenceAssessment,
    ConfidenceConfig,
    EvidenceCandidate,
    assess_confidence,
    calculate_answerability_score,
    calculate_lexical_coverage,
    calculate_numeric_consistency,
    calculate_scope_risk,
    detect_external_authority_request,
    extract_numeric_claims,
    normalize_retrieval_margin,
    normalize_text,
    normalize_token,
    tokenize_significant_terms,
)


def _assess(
    query: str,
    candidates: list[EvidenceCandidate],
    **config_overrides: float | int,
) -> ConfidenceAssessment:
    config = ConfidenceConfig(**config_overrides)
    return assess_confidence(query, candidates, config)


def test_normalize_text_handles_unicode_case_punctuation_and_whitespace() -> None:
    assert normalize_text("  RÉSUMÉ—Policy\nCAD $1,000! ") == (
        "résumé policy cad $1 000"
    )


@pytest.mark.parametrize(
    ("variant", "expected"),
    [
        ("devices", "device"),
        ("reported", "report"),
        ("receipts", "receipt"),
        ("approved", "approve"),
        ("covered", "cover"),
        ("reporting", "report"),
    ],
)
def test_normalize_token_conservatively_handles_common_suffixes(
    variant: str,
    expected: str,
) -> None:
    assert normalize_token(variant) == expected


def test_tokenize_significant_terms_removes_stopwords_and_short_letters() -> None:
    assert tokenize_significant_terms("What is a Device, and x receipts?") == [
        "device",
        "receipt",
    ]


def test_lexical_coverage_complete_and_sorted() -> None:
    coverage, matched, missing = calculate_lexical_coverage(
        "Report stolen devices immediately",
        "Stolen device incidents must be reported immediately.",
    )

    assert coverage == 1.0
    assert matched == ["device", "immediate", "report", "stolen"]
    assert missing == []


def test_lexical_coverage_partial() -> None:
    coverage, matched, missing = calculate_lexical_coverage(
        "itemized receipt missing approval",
        "An itemized receipt is required.",
    )

    assert coverage == 0.5
    assert matched == ["itemize", "receipt"]
    assert missing == ["approval", "miss"]


def test_lexical_coverage_with_no_significant_query_terms_is_safe() -> None:
    assert calculate_lexical_coverage("What is it?", "Anything") == (
        0.0,
        [],
        [],
    )


def test_extract_numeric_claims_supports_required_formats() -> None:
    assert extract_numeric_claims(
        "CAD 1,000, $2,500.50, 25%, 30 days, one hour, and two years"
    ) == [
        "1",
        "2",
        "30",
        "CAD:1000",
        "MONEY:2500.5",
        "PERCENT:25",
    ]


def test_extract_numeric_claims_supports_plain_decimals() -> None:
    assert extract_numeric_claims("The multiplier is 1.50") == ["1.5"]


def test_numeric_consistency_matches_all_question_claims() -> None:
    result = calculate_numeric_consistency(
        "Can I claim CAD 300 within 30 days?",
        "Employees may claim CAD 300 and must apply within 30 calendar days.",
    )

    assert result[0] == 1.0
    assert result[1] is False
    assert result[4] == []


def test_numeric_consistency_rejects_a_mismatch() -> None:
    result = calculate_numeric_consistency(
        "Is the allowance CAD 1,000?",
        "The allowance is CAD 300.",
    )

    assert result[0] == 0.0
    assert result[1] is True
    assert result[4] == ["CAD:1000"]


def test_numeric_consistency_is_null_when_query_has_no_numeric_claim() -> None:
    result = calculate_numeric_consistency(
        "What is the allowance?",
        "The allowance is CAD 300.",
    )

    assert result[0] is None
    assert result[1] is False
    assert result[2] == []


@pytest.mark.parametrize(
    "query",
    [
        "Does the law require severance?",
        "What does Alberta law require for severance?",
        "Am I legally entitled to this payment?",
        "Is this legally enforceable?",
        "What severance is required by law?",
    ],
)
def test_detect_external_legal_scope_queries(query: str) -> None:
    assert detect_external_authority_request(query) is True


def test_internal_security_and_legal_approval_is_not_external_scope() -> None:
    query = "Does this purchase need Security and Legal team approval?"
    evidence = "Security and Legal team approval is required for this purchase."

    assert detect_external_authority_request(query) is False
    assert calculate_scope_risk(query, evidence) == (False, None)


def test_external_scope_can_be_resolved_only_by_an_explicit_authority_rule() -> None:
    query = "What does Alberta law require for the notice period?"
    evidence = "Alberta law requires a notice period of two weeks."

    assert calculate_scope_risk(query, evidence) == (False, None)


def test_retrieval_margin_normalization_is_bounded_and_single_is_zero() -> None:
    assert normalize_retrieval_margin(0.60, None) == 0.0
    assert normalize_retrieval_margin(0.60, 0.57) == 0.2
    assert normalize_retrieval_margin(0.60, 0.30) == 1.0
    assert normalize_retrieval_margin(0.40, 0.50) == 0.0


def test_confidence_formula_matches_documented_weights() -> None:
    assert calculate_answerability_score(0.6, 0.5, 0.75, 0.2) == 0.6325


def test_candidate_floor_excludes_low_scoring_evidence() -> None:
    assessment = _assess(
        "report a stolen device",
        [EvidenceCandidate("Report a stolen device immediately.", 0.2999)],
    )

    assert assessment.evidence_status == "insufficient"
    assert assessment.answer_ready is False
    assert assessment.top_retrieval_score == 0.0


def test_malformed_or_unusable_candidates_are_rejected_safely() -> None:
    assessment = _assess(
        "report a stolen device",
        [
            EvidenceCandidate("", 0.90),
            EvidenceCandidate("Relevant text", float("nan")),
            EvidenceCandidate("Relevant text", True),
        ],
    )

    assert assessment.evidence_status == "insufficient"
    assert assessment.answer_ready is False
    assert assessment.decision_reasons


def test_direct_support_promotes_low_score_evidence_to_moderate() -> None:
    assessment = _assess(
        "report stolen device company procedure",
        [EvidenceCandidate("Report a stolen device.", 0.36)],
    )

    assert assessment.answerability_score < 0.55
    assert assessment.direct_support is True
    assert assessment.evidence_status == "moderate"
    assert assessment.answer_ready is True


def test_strong_evidence_classification() -> None:
    assessment = _assess(
        "employees report stolen devices immediately",
        [
            EvidenceCandidate(
                "Employees must report stolen devices immediately.",
                0.90,
            ),
            EvidenceCandidate("Report stolen employee devices.", 0.70),
        ],
    )

    assert assessment.evidence_status == "strong"
    assert assessment.answer_ready is True


def test_moderate_evidence_classification() -> None:
    assessment = _assess(
        "employee travel receipt approval",
        [EvidenceCandidate("Employee travel rules require approval.", 0.70)],
    )

    assert assessment.answerability_score >= 0.55
    assert assessment.top_chunk_lexical_coverage == 0.75
    assert assessment.evidence_status == "moderate"


def test_weak_evidence_classification_does_not_answer() -> None:
    assessment = _assess(
        "employee travel receipt",
        [
            EvidenceCandidate("Employee conduct guidance.", 0.55),
            EvidenceCandidate("Employee workplace overview.", 0.54),
        ],
    )

    assert assessment.evidence_status == "weak"
    assert assessment.answer_ready is False
    assert assessment.public_confidence_score == 0.0


def test_insufficient_evidence_classification() -> None:
    assessment = _assess(
        "employee travel receipt",
        [EvidenceCandidate("Office closure guidance.", 0.31)],
    )

    assert assessment.evidence_status == "insufficient"
    assert assessment.answer_ready is False


def test_numeric_mismatch_is_a_hard_rejection() -> None:
    assessment = _assess(
        "Is the wellness allowance CAD 1,000?",
        [
            EvidenceCandidate(
                "The wellness allowance is CAD 300.",
                0.90,
            )
        ],
    )

    assert assessment.numeric_mismatch is True
    assert assessment.evidence_status == "insufficient"
    assert assessment.answer_ready is False
    assert assessment.public_confidence_score == 0.0


def test_unresolved_scope_risk_is_a_hard_rejection() -> None:
    assessment = _assess(
        "What does Alberta law require for severance?",
        [
            EvidenceCandidate(
                "This handbook is not legal advice and applicable law may vary.",
                0.90,
            )
        ],
    )

    assert assessment.scope_risk is True
    assert assessment.evidence_status == "insufficient"
    assert assessment.answer_ready is False


def test_decision_reasons_are_populated_without_exposing_evidence() -> None:
    secret_evidence = "Confidential full evidence body"
    assessment = _assess(
        "What is the unrelated benefit?",
        [EvidenceCandidate(secret_evidence, 0.31)],
    )

    assert assessment.decision_reasons
    assert secret_evidence not in repr(assessment)
    assert "evidence_text" not in {field.name for field in fields(assessment)}


@pytest.mark.parametrize(
    "overrides",
    [
        {"RAG_CANDIDATE_RETRIEVAL_FLOOR": 0.5, "RAG_DIRECT_SUPPORT_SCORE_FLOOR": 0.4},
        {"RAG_WEAK_CONFIDENCE_THRESHOLD": 0.6, "RAG_MODERATE_CONFIDENCE_THRESHOLD": 0.5},
        {"RAG_DIRECT_SUPPORT_COVERAGE_MIN": 1.1},
        {"RAG_CONFIDENCE_MAX_EVIDENCE_CHUNKS": 0},
    ],
)
def test_settings_reject_invalid_confidence_configuration(
    overrides: dict[str, float | int],
) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **overrides)
