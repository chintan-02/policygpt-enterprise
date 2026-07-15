import pytest

from app.services.confidence_service import (
    ConfidenceConfig,
    EvidenceCandidate,
    assess_confidence,
)


@pytest.fixture
def confidence_config() -> ConfidenceConfig:
    return ConfidenceConfig()


def test_low_score_lost_device_evidence_is_recovered(
    confidence_config: ConfidenceConfig,
) -> None:
    assessment = assess_confidence(
        "How quickly must a lost or stolen company device be reported?",
        [
            EvidenceCandidate(
                "Lost or stolen devices must be reported to IT immediately "
                "and within one hour.",
                0.3745,
            )
        ],
        confidence_config,
    )

    assert assessment.direct_support is True
    assert assessment.evidence_status == "moderate"
    assert assessment.answer_ready is True


def test_low_score_expense_receipt_evidence_is_recovered(
    confidence_config: ConfidenceConfig,
) -> None:
    assessment = assess_confidence(
        "Are itemized receipts required and what happens if a receipt is missing?",
        [
            EvidenceCandidate(
                "Itemized receipts are required. If a receipt is missing, the "
                "employee must provide an explanation and obtain manager approval.",
                0.3646,
            )
        ],
        confidence_config,
    )

    assert assessment.direct_support is True
    assert assessment.evidence_status == "moderate"
    assert assessment.answer_ready is True


def test_numeric_contradiction_preserves_unsupported_fallback(
    confidence_config: ConfidenceConfig,
) -> None:
    assessment = assess_confidence(
        "Does the policy provide a CAD 1,000 wellness allowance?",
        [
            EvidenceCandidate(
                "The policy provides a CAD 300 wellness allowance.",
                0.4080,
            )
        ],
        confidence_config,
    )

    assert assessment.numeric_mismatch is True
    assert assessment.evidence_status == "insufficient"
    assert assessment.answer_ready is False
    assert assessment.public_confidence_score == 0.0


def test_external_law_question_preserves_unsupported_fallback(
    confidence_config: ConfidenceConfig,
) -> None:
    assessment = assess_confidence(
        "What does Alberta law require for severance after two years?",
        [
            EvidenceCandidate(
                "This handbook is a policy summary, not legal advice. Applicable "
                "law and written employment agreements take priority.",
                0.4202,
            )
        ],
        confidence_config,
    )

    assert assessment.scope_risk is True
    assert assessment.evidence_status == "insufficient"
    assert assessment.answer_ready is False
    assert assessment.public_confidence_score == 0.0


def test_semantically_nearby_but_lexically_weak_evidence_does_not_answer(
    confidence_config: ConfidenceConfig,
) -> None:
    assessment = assess_confidence(
        "What private health insurance plan covers prescription glasses?",
        [
            EvidenceCandidate(
                "Employees can review general workplace wellness resources.",
                0.39,
            )
        ],
        confidence_config,
    )

    assert assessment.direct_support is False
    assert assessment.evidence_status in {"weak", "insufficient"}
    assert assessment.answer_ready is False
