import pytest

from eval.scoring import (
    calculate_aggregate_metrics,
    calculate_case_passed,
    calculate_fallback_correct,
    calculate_page_hit,
    calculate_readiness_correct,
    normalize_text,
    score_expected_keywords,
)


def test_normalization_is_case_insensitive() -> None:
    assert normalize_text("Security AND Legal") == "security and legal"


def test_normalization_handles_unicode_punctuation_and_whitespace() -> None:
    assert normalize_text("  ＣＡＤ 300—approved!\n Receipts. ") == (
        "cad 300 approved receipts"
    )


def test_numeric_and_currency_phrase_matching() -> None:
    matched, missing, score = score_expected_keywords(
        "The one-time allowance is up to CAD 300.",
        ["CAD 300", "one-time"],
    )

    assert matched == ["CAD 300", "one-time"]
    assert missing == []
    assert score == 1.0


def test_all_keywords_matched() -> None:
    matched, missing, score = score_expected_keywords(
        "Receipts are required and approval comes before reimbursement.",
        ["receipts are required", "before reimbursement"],
    )

    assert matched == ["receipts are required", "before reimbursement"]
    assert missing == []
    assert score == 1.0


def test_partial_keyword_match() -> None:
    matched, missing, score = score_expected_keywords(
        "Receipts are required.",
        ["receipts", "manager approval"],
    )

    assert matched == ["receipts"]
    assert missing == ["manager approval"]
    assert score == 0.5


def test_no_keywords_returns_null_score() -> None:
    assert score_expected_keywords("Fallback answer", []) == ([], [], None)


@pytest.mark.parametrize(
    ("should_answer", "expected_pages", "retrieved_pages", "expected"),
    [
        (True, [5], [2, 5], True),
        (True, [5], [2, 7], False),
        (False, [], [1], None),
    ],
)
def test_page_hit_behavior(
    should_answer: bool,
    expected_pages: list[int],
    retrieved_pages: list[int],
    expected: bool | None,
) -> None:
    assert (
        calculate_page_hit(should_answer, expected_pages, retrieved_pages)
        is expected
    )


def test_readiness_correctness() -> None:
    assert calculate_readiness_correct(True, True) is True
    assert calculate_readiness_correct(False, False) is True
    assert calculate_readiness_correct(True, False) is False


def test_fallback_correctness() -> None:
    assert calculate_fallback_correct(False, False, True, 0) is True
    assert calculate_fallback_correct(False, False, True, 1) is False
    assert calculate_fallback_correct(True, True, False, 1) is None


def test_supported_case_passes() -> None:
    assert calculate_case_passed(
        should_answer=True,
        answer_ready=True,
        readiness_correct=True,
        page_hit=True,
        keyword_match_score=1.0,
        fallback_used=False,
        citation_count=1,
        has_error=False,
    ) is True


def test_supported_case_fails_for_missing_page() -> None:
    assert calculate_case_passed(
        should_answer=True,
        answer_ready=True,
        readiness_correct=True,
        page_hit=False,
        keyword_match_score=1.0,
        fallback_used=False,
        citation_count=1,
        has_error=False,
    ) is False


def test_supported_case_fails_for_missing_keyword() -> None:
    assert calculate_case_passed(
        should_answer=True,
        answer_ready=True,
        readiness_correct=True,
        page_hit=True,
        keyword_match_score=0.5,
        fallback_used=False,
        citation_count=1,
        has_error=False,
    ) is False


def test_unsupported_case_passes() -> None:
    assert calculate_case_passed(
        should_answer=False,
        answer_ready=False,
        readiness_correct=True,
        page_hit=None,
        keyword_match_score=None,
        fallback_used=True,
        citation_count=0,
        has_error=False,
    ) is True


def test_unsupported_case_fails_when_citations_are_returned() -> None:
    assert calculate_case_passed(
        should_answer=False,
        answer_ready=False,
        readiness_correct=True,
        page_hit=None,
        keyword_match_score=None,
        fallback_used=True,
        citation_count=1,
        has_error=False,
    ) is False


def _aggregate_result(**overrides: object) -> dict[str, object]:
    result: dict[str, object] = {
        "should_answer": True,
        "case_passed": True,
        "error_type": None,
        "readiness_correct": True,
        "fallback_correct": None,
        "page_hit": True,
        "keyword_match_score": 1.0,
        "confidence_score": 0.8,
        "latency_ms": 100.0,
        "citation_count": 2,
    }
    result.update(overrides)
    return result


def test_aggregate_metric_calculations() -> None:
    results = [
        _aggregate_result(),
        _aggregate_result(
            should_answer=False,
            fallback_correct=True,
            page_hit=None,
            keyword_match_score=None,
            confidence_score=0.0,
            latency_ms=50.0,
            citation_count=0,
        ),
        _aggregate_result(
            case_passed=False,
            error_type="Timeout",
            readiness_correct=False,
            page_hit=False,
            keyword_match_score=0.0,
            confidence_score=0.0,
            latency_ms=25.0,
            citation_count=0,
        ),
    ]

    summary = calculate_aggregate_metrics(results)

    assert summary == {
        "total_questions": 3,
        "supported_questions": 2,
        "unsupported_questions": 1,
        "passed_questions": 2,
        "failed_questions_count": 1,
        "request_error_count": 1,
        "answer_readiness_accuracy": 0.6667,
        "fallback_accuracy": 1.0,
        "retrieval_page_hit_rate": 1.0,
        "keyword_match_rate": 0.5,
        "average_confidence": 0.4,
        "average_supported_confidence": 0.8,
        "average_latency_ms": 58.33,
        "average_citation_count": 0.67,
    }


def test_empty_denominators_return_zero() -> None:
    assert calculate_aggregate_metrics([]) == {
        "total_questions": 0,
        "supported_questions": 0,
        "unsupported_questions": 0,
        "passed_questions": 0,
        "failed_questions_count": 0,
        "request_error_count": 0,
        "answer_readiness_accuracy": 0.0,
        "fallback_accuracy": 0.0,
        "retrieval_page_hit_rate": 0.0,
        "keyword_match_rate": 0.0,
        "average_confidence": 0.0,
        "average_supported_confidence": 0.0,
        "average_latency_ms": 0.0,
        "average_citation_count": 0.0,
    }
