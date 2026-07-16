import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any


def normalize_text(value: str) -> str:
    """Normalize text for deterministic phrase matching without losing numbers."""

    normalized = unicodedata.normalize("NFKC", value).casefold()
    characters: list[str] = []

    for character in normalized:
        category = unicodedata.category(character)
        if character.isalnum() or category == "Sc":
            characters.append(character)
        else:
            characters.append(" ")

    return " ".join("".join(characters).split())


def score_expected_keywords(
    answer: str,
    expected_keywords: list[str],
) -> tuple[list[str], list[str], float | None]:
    if not expected_keywords:
        return [], [], None

    normalized_answer = f" {normalize_text(answer)} "
    matched_keywords: list[str] = []
    missing_keywords: list[str] = []

    for keyword in expected_keywords:
        normalized_keyword = normalize_text(keyword)
        if normalized_keyword and f" {normalized_keyword} " in normalized_answer:
            matched_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)

    score = len(matched_keywords) / len(expected_keywords)
    return matched_keywords, missing_keywords, round(score, 4)


def calculate_page_hit(
    should_answer: bool,
    expected_pages: list[int],
    retrieved_pages: list[int],
) -> bool | None:
    if not should_answer:
        return None

    return bool(set(expected_pages) & set(retrieved_pages))


def calculate_readiness_correct(
    should_answer: bool,
    answer_ready: bool,
) -> bool:
    return should_answer == answer_ready


def calculate_fallback_correct(
    should_answer: bool,
    answer_ready: bool,
    fallback_used: bool,
    citation_count: int,
) -> bool | None:
    if should_answer:
        return None

    return not answer_ready and fallback_used and citation_count == 0


def calculate_case_passed(
    *,
    should_answer: bool,
    answer_ready: bool,
    readiness_correct: bool,
    page_hit: bool | None,
    keyword_match_score: float | None,
    fallback_used: bool,
    citation_count: int,
    has_error: bool,
) -> bool:
    if has_error:
        return False

    if should_answer:
        return (
            answer_ready
            and readiness_correct
            and page_hit is True
            and keyword_match_score == 1.0
        )

    return (
        not answer_ready
        and readiness_correct
        and fallback_used
        and citation_count == 0
    )


def _safe_average(values: Sequence[float], decimal_places: int) -> float:
    if not values:
        return 0.0

    return round(sum(values) / len(values), decimal_places)


def calculate_aggregate_metrics(
    results: Sequence[Mapping[str, Any]],
) -> dict[str, int | float]:
    total_questions = len(results)
    supported_results = [result for result in results if result["should_answer"]]
    unsupported_results = [
        result for result in results if not result["should_answer"]
    ]
    successful_results = [result for result in results if not result["error_type"]]
    successful_supported_results = [
        result
        for result in supported_results
        if not result["error_type"]
    ]

    passed_questions = sum(bool(result["case_passed"]) for result in results)
    request_error_count = sum(bool(result["error_type"]) for result in results)
    readiness_correct_count = sum(
        bool(result["readiness_correct"]) for result in results
    )
    fallback_correct_count = sum(
        result["fallback_correct"] is True for result in unsupported_results
    )
    page_hit_count = sum(
        result["page_hit"] is True for result in successful_supported_results
    )

    keyword_scores = [
        float(result["keyword_match_score"])
        for result in supported_results
        if result["keyword_match_score"] is not None
    ]
    confidence_scores = [
        float(result["confidence_score"]) for result in successful_results
    ]
    supported_confidence_scores = [
        float(result["confidence_score"])
        for result in successful_supported_results
    ]
    latency_values = [float(result["latency_ms"]) for result in results]
    citation_counts = [float(result["citation_count"]) for result in results]

    return {
        "total_questions": total_questions,
        "supported_questions": len(supported_results),
        "unsupported_questions": len(unsupported_results),
        "passed_questions": passed_questions,
        "failed_questions_count": total_questions - passed_questions,
        "request_error_count": request_error_count,
        "answer_readiness_accuracy": round(
            readiness_correct_count / total_questions,
            4,
        )
        if total_questions
        else 0.0,
        "fallback_accuracy": round(
            fallback_correct_count / len(unsupported_results),
            4,
        )
        if unsupported_results
        else 0.0,
        "retrieval_page_hit_rate": round(
            page_hit_count / len(successful_supported_results),
            4,
        )
        if successful_supported_results
        else 0.0,
        "keyword_match_rate": _safe_average(keyword_scores, 4),
        "average_confidence": _safe_average(confidence_scores, 4),
        "average_supported_confidence": _safe_average(
            supported_confidence_scores,
            4,
        ),
        "average_latency_ms": _safe_average(latency_values, 2),
        "average_citation_count": _safe_average(citation_counts, 2),
    }
