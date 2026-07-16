from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS_PATH = Path("eval/results/latest_eval_results.json")
RESULTS_PATH_ENV = "POLICYGPT_EVAL_RESULTS_PATH"
SENSITIVE_ERROR_TERMS = (
    "api" + "key",
    "author" + "ization",
    "system" + "prompt",
    "evidence" + "text",
    "embedding" + "vector",
)
MAX_SAFE_ERROR_LENGTH = 300


class EvaluationResultsError(ValueError):
    """Raised when a result artifact cannot be loaded or validated safely."""

    def __init__(self, path: Path, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(reason)


class DiagnosticCategory(str, Enum):
    PASSED_SUPPORTED_ANSWER = "passed_supported_answer"
    PASSED_UNSUPPORTED_FALLBACK = "passed_unsupported_fallback"
    PROVIDER_GENERATION_FAILURE = "provider_generation_failure"
    RETRIEVAL_PAGE_MISS = "retrieval_page_miss"
    READINESS_MISMATCH = "readiness_mismatch"
    FALLBACK_GUARDRAIL_FAILURE = "fallback_guardrail_failure"
    ANSWER_COMPLETENESS_FAILURE = "answer_completeness_failure"
    NUMERIC_GUARDRAIL_REJECTION = "numeric_guardrail_rejection"
    LEGAL_SCOPE_GUARDRAIL_REJECTION = "legal_scope_guardrail_rejection"
    REQUEST_ERROR = "request_error"
    OTHER_EVALUATION_FAILURE = "other_evaluation_failure"


class QualityGateStatus(str, Enum):
    PASSED = "passed"
    NEEDS_ATTENTION = "needs_attention"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class QualityGate:
    key: str
    label: str
    status: QualityGateStatus
    value: str
    detail: str


@dataclass(frozen=True)
class EvaluationRunMetadata:
    run_id: str
    started_at_utc: str | None
    completed_at_utc: str | None
    duration_ms: float | None
    base_url: str | None
    endpoint: str | None
    dataset_path: str | None
    dataset_sha256: str | None
    top_k: int | None
    timeout_seconds: float | None
    request_delay_seconds: float | None
    question_count: int
    duplicate_citation_warning: bool
    question_id: str | None = None
    limit: int | None = None


@dataclass(frozen=True)
class EvaluationSummary:
    total_questions: int
    supported_questions: int
    unsupported_questions: int
    passed_questions: int
    failed_questions_count: int
    request_error_count: int
    answer_readiness_accuracy: float
    fallback_accuracy: float
    retrieval_page_hit_rate: float
    keyword_match_rate: float
    average_confidence: float
    average_supported_confidence: float
    average_latency_ms: float
    average_citation_count: float


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    question: str
    category: str
    difficulty: str
    evaluation_focus: tuple[str, ...]
    should_answer: bool
    answer_ready: bool
    readiness_correct: bool
    evidence_status: str
    confidence_score: float
    expected_pages: tuple[int, ...]
    retrieved_pages: tuple[int, ...]
    page_hit: bool | None
    expected_answer_keywords: tuple[str, ...]
    matched_keywords: tuple[str, ...]
    missing_keywords: tuple[str, ...]
    keyword_match_score: float | None
    answer: str
    fallback_used: bool
    fallback_correct: bool | None
    citation_count: int
    retrieved_filenames: tuple[str, ...]
    citation_scores: tuple[float, ...]
    top_citation_score: float | None
    average_citation_score: float | None
    duplicate_citation_count: int
    latency_ms: float
    llm_provider: str
    model_name: str | None
    case_passed: bool
    error_type: str | None
    error_message: str | None
    answerability_score: float | None = None
    top_retrieval_score: float | None = None
    average_retrieval_score: float | None = None
    retrieval_margin: float | None = None
    lexical_coverage: float | None = None
    top_chunk_lexical_coverage: float | None = None
    numeric_consistency: float | None = None
    numeric_mismatch: bool = False
    query_numeric_claims: tuple[str, ...] = ()
    evidence_numeric_claims: tuple[str, ...] = ()
    missing_numeric_claims: tuple[str, ...] = ()
    scope_risk: bool = False
    scope_risk_reason: str | None = None
    direct_support: bool | None = None
    matched_query_terms: tuple[str, ...] = ()
    missing_query_terms: tuple[str, ...] = ()
    decision_reasons: tuple[str, ...] = ()
    provider_fallback_used: bool | None = None
    generation_attempt_count: int | None = None
    generation_error_type: str | None = None
    available_fields: frozenset[str] = field(default_factory=frozenset)
    diagnostic_category: DiagnosticCategory = DiagnosticCategory.OTHER_EVALUATION_FAILURE

    @property
    def provider_fallback_detected(self) -> bool:
        return self.provider_fallback_used is True or (
            self.should_answer
            and self.answer_ready
            and self.fallback_used
            and self.citation_count > 0
        )


@dataclass(frozen=True)
class EvaluationDashboardData:
    run: EvaluationRunMetadata
    summary: EvaluationSummary
    cases: tuple[EvaluationCase, ...]
    result_path: Path
    csv_path: Path | None
    modified_at: datetime
    modified_time_ns: int
    benchmark_question_count: int | None

    @property
    def is_partial_run(self) -> bool:
        return detect_partial_run(self)


@dataclass(frozen=True)
class EvaluationFilters:
    result_status: str = "all"
    diagnostic_categories: tuple[str, ...] = ()
    support_status: str = "all"
    categories: tuple[str, ...] = ()
    difficulties: tuple[str, ...] = ()
    evidence_statuses: tuple[str, ...] = ()
    providers: tuple[str, ...] = ()
    fallback_used: bool | None = None
    numeric_mismatch: bool | None = None
    scope_risk: bool | None = None
    direct_support: bool | None = None
    search_text: str = ""


@dataclass(frozen=True)
class KPIValue:
    key: str
    label: str
    primary: str
    secondary: str
    caption: str
    status: str = "neutral"


def resolve_results_path(
    configured_path: str | Path | None = None,
    *,
    project_root: Path = PROJECT_ROOT,
) -> Path:
    raw_path = configured_path
    if raw_path is None:
        raw_path = os.getenv(RESULTS_PATH_ENV, str(DEFAULT_RESULTS_PATH))

    candidate = Path(raw_path)
    if candidate.is_absolute():
        raise EvaluationResultsError(
            candidate,
            f"{RESULTS_PATH_ENV} must be a repository-relative path.",
        )

    root = project_root.resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise EvaluationResultsError(
            resolved,
            f"{RESULTS_PATH_ENV} must remain inside the repository.",
        ) from exc
    return resolved


def get_result_file_metadata(path: Path) -> tuple[datetime, int]:
    try:
        stat = path.stat()
    except OSError as exc:
        raise EvaluationResultsError(path, "The result file could not be inspected.") from exc
    return datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc), stat.st_mtime_ns


def _safe_error(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return "Invalid error detail"
    normalized = " ".join(value.split()).strip()
    if not normalized:
        return None
    compact = "".join(character for character in normalized.casefold() if character.isalnum())
    if any(term in compact for term in SENSITIVE_ERROR_TERMS):
        return "[sensitive error detail redacted]"
    return normalized[:MAX_SAFE_ERROR_LENGTH]


def _require_mapping(value: Any, path: Path, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise EvaluationResultsError(path, f"{label} must be a JSON object.")
    return value


def _required_str(data: Mapping[str, Any], key: str, path: Path, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise EvaluationResultsError(path, f"{label}.{key} must be a non-empty string.")
    return value


def _required_bool(data: Mapping[str, Any], key: str, path: Path, label: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise EvaluationResultsError(path, f"{label}.{key} must be boolean.")
    return value


def _number(
    value: Any,
    path: Path,
    label: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvaluationResultsError(path, f"{label} must be numeric.")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise EvaluationResultsError(path, f"{label} must be finite.")
    if minimum is not None and parsed < minimum:
        raise EvaluationResultsError(path, f"{label} must be at least {minimum:g}.")
    if maximum is not None and parsed > maximum:
        raise EvaluationResultsError(path, f"{label} must be at most {maximum:g}.")
    return parsed


def _integer(value: Any, path: Path, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise EvaluationResultsError(path, f"{label} must be an integer of at least {minimum}.")
    return value


def _optional_number(
    data: Mapping[str, Any],
    key: str,
    path: Path,
    label: str,
    *,
    minimum: float = 0.0,
    maximum: float | None = None,
) -> float | None:
    value = data.get(key)
    if value is None:
        return None
    return _number(value, path, f"{label}.{key}", minimum=minimum, maximum=maximum)


def _optional_bool(data: Mapping[str, Any], key: str, path: Path, label: str) -> bool | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, bool):
        raise EvaluationResultsError(path, f"{label}.{key} must be boolean when present.")
    return value


def _optional_str(data: Mapping[str, Any], key: str) -> str | None:
    value = data.get(key)
    return value if isinstance(value, str) and value.strip() else None


def _string_tuple(value: Any, path: Path, label: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise EvaluationResultsError(path, f"{label} must be a list of strings.")
    return tuple(value)


def _int_tuple(value: Any, path: Path, label: str) -> tuple[int, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise EvaluationResultsError(path, f"{label} must be a list of integers.")
    return tuple(_integer(item, path, label, minimum=1) for item in value)


def _float_tuple(value: Any, path: Path, label: str) -> tuple[float, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise EvaluationResultsError(path, f"{label} must be a list of numbers.")
    return tuple(_number(item, path, label, minimum=0.0) for item in value)


SUMMARY_COUNT_FIELDS = (
    "total_questions",
    "supported_questions",
    "unsupported_questions",
    "passed_questions",
    "failed_questions_count",
    "request_error_count",
)
SUMMARY_RATE_FIELDS = (
    "answer_readiness_accuracy",
    "fallback_accuracy",
    "retrieval_page_hit_rate",
    "keyword_match_rate",
)
SUMMARY_AVERAGE_FIELDS = (
    "average_confidence",
    "average_supported_confidence",
    "average_latency_ms",
    "average_citation_count",
)


def _parse_summary(data: Any, path: Path) -> EvaluationSummary:
    summary = _require_mapping(data, path, "summary")
    counts = {
        key: _integer(summary.get(key), path, f"summary.{key}")
        for key in SUMMARY_COUNT_FIELDS
    }
    rates = {
        key: _number(summary.get(key), path, f"summary.{key}", minimum=0.0, maximum=1.0)
        for key in SUMMARY_RATE_FIELDS
    }
    averages = {
        key: _number(summary.get(key), path, f"summary.{key}", minimum=0.0)
        for key in SUMMARY_AVERAGE_FIELDS
    }
    if counts["supported_questions"] + counts["unsupported_questions"] != counts["total_questions"]:
        raise EvaluationResultsError(path, "summary support counts do not equal total_questions.")
    if counts["passed_questions"] + counts["failed_questions_count"] != counts["total_questions"]:
        raise EvaluationResultsError(path, "summary pass counts do not equal total_questions.")
    return EvaluationSummary(**counts, **rates, **averages)


def _parse_run(data: Any, path: Path) -> EvaluationRunMetadata:
    run = _require_mapping(data, path, "run")
    run_id = _required_str(run, "run_id", path, "run")
    question_count = _integer(run.get("question_count"), path, "run.question_count")
    duplicate_warning = run.get("duplicate_citation_warning", False)
    if not isinstance(duplicate_warning, bool):
        raise EvaluationResultsError(path, "run.duplicate_citation_warning must be boolean.")
    return EvaluationRunMetadata(
        run_id=run_id,
        started_at_utc=_optional_str(run, "started_at_utc"),
        completed_at_utc=_optional_str(run, "completed_at_utc"),
        duration_ms=_optional_number(run, "duration_ms", path, "run"),
        base_url=_optional_str(run, "base_url"),
        endpoint=_optional_str(run, "endpoint"),
        dataset_path=_optional_str(run, "dataset_path"),
        dataset_sha256=_optional_str(run, "dataset_sha256"),
        top_k=(
            _integer(run["top_k"], path, "run.top_k", minimum=1)
            if run.get("top_k") is not None
            else None
        ),
        timeout_seconds=_optional_number(run, "timeout_seconds", path, "run"),
        request_delay_seconds=_optional_number(run, "request_delay_seconds", path, "run"),
        question_count=question_count,
        duplicate_citation_warning=duplicate_warning,
        question_id=_optional_str(run, "question_id"),
        limit=(
            _integer(run["limit"], path, "run.limit", minimum=1)
            if run.get("limit") is not None
            else None
        ),
    )


REQUIRED_CASE_FIELDS = {
    "id",
    "question",
    "category",
    "difficulty",
    "should_answer",
    "answer_ready",
    "readiness_correct",
    "evidence_status",
    "confidence_score",
    "expected_pages",
    "retrieved_pages",
    "page_hit",
    "expected_answer_keywords",
    "matched_keywords",
    "missing_keywords",
    "keyword_match_score",
    "answer",
    "fallback_used",
    "fallback_correct",
    "citation_count",
    "latency_ms",
    "llm_provider",
    "case_passed",
}


def _parse_case(data: Any, index: int, path: Path) -> EvaluationCase:
    label = f"results[{index}]"
    case = _require_mapping(data, path, label)
    missing = REQUIRED_CASE_FIELDS - case.keys()
    if missing:
        raise EvaluationResultsError(path, f"{label} is missing fields: {', '.join(sorted(missing))}.")

    confidence_breakdown = case.get("confidence_breakdown")
    if confidence_breakdown is None:
        breakdown: Mapping[str, Any] = {}
    else:
        breakdown = _require_mapping(confidence_breakdown, path, f"{label}.confidence_breakdown")

    def source(key: str) -> Any:
        return case[key] if key in case else breakdown.get(key)

    page_hit = case.get("page_hit")
    if page_hit is not None and not isinstance(page_hit, bool):
        raise EvaluationResultsError(path, f"{label}.page_hit must be boolean or null.")
    fallback_correct = case.get("fallback_correct")
    if fallback_correct is not None and not isinstance(fallback_correct, bool):
        raise EvaluationResultsError(path, f"{label}.fallback_correct must be boolean or null.")
    keyword_score = case.get("keyword_match_score")
    parsed_keyword_score = (
        None
        if keyword_score is None
        else _number(keyword_score, path, f"{label}.keyword_match_score", minimum=0.0, maximum=1.0)
    )
    answer = case.get("answer")
    if not isinstance(answer, str):
        raise EvaluationResultsError(path, f"{label}.answer must be a string.")

    optional_score_names = (
        "answerability_score",
        "top_retrieval_score",
        "average_retrieval_score",
        "retrieval_margin",
        "lexical_coverage",
        "top_chunk_lexical_coverage",
        "numeric_consistency",
    )
    optional_scores: dict[str, float | None] = {}
    for key in optional_score_names:
        value = source(key)
        optional_scores[key] = (
            None
            if value is None
            else _number(value, path, f"{label}.{key}", minimum=0.0, maximum=1.0)
        )

    def optional_flag(key: str, default: bool | None = None) -> bool | None:
        value = source(key)
        if value is None:
            return default
        if not isinstance(value, bool):
            raise EvaluationResultsError(path, f"{label}.{key} must be boolean when present.")
        return value

    provisional = EvaluationCase(
        id=_required_str(case, "id", path, label),
        question=_required_str(case, "question", path, label),
        category=_required_str(case, "category", path, label),
        difficulty=_required_str(case, "difficulty", path, label),
        evaluation_focus=_string_tuple(case.get("evaluation_focus"), path, f"{label}.evaluation_focus"),
        should_answer=_required_bool(case, "should_answer", path, label),
        answer_ready=_required_bool(case, "answer_ready", path, label),
        readiness_correct=_required_bool(case, "readiness_correct", path, label),
        evidence_status=_required_str(case, "evidence_status", path, label),
        confidence_score=_number(case.get("confidence_score"), path, f"{label}.confidence_score", minimum=0.0, maximum=1.0),
        expected_pages=_int_tuple(case.get("expected_pages"), path, f"{label}.expected_pages"),
        retrieved_pages=_int_tuple(case.get("retrieved_pages"), path, f"{label}.retrieved_pages"),
        page_hit=page_hit,
        expected_answer_keywords=_string_tuple(case.get("expected_answer_keywords"), path, f"{label}.expected_answer_keywords"),
        matched_keywords=_string_tuple(case.get("matched_keywords"), path, f"{label}.matched_keywords"),
        missing_keywords=_string_tuple(case.get("missing_keywords"), path, f"{label}.missing_keywords"),
        keyword_match_score=parsed_keyword_score,
        answer=answer,
        fallback_used=_required_bool(case, "fallback_used", path, label),
        fallback_correct=fallback_correct,
        citation_count=_integer(case.get("citation_count"), path, f"{label}.citation_count"),
        retrieved_filenames=_string_tuple(case.get("retrieved_filenames"), path, f"{label}.retrieved_filenames"),
        citation_scores=_float_tuple(case.get("citation_scores"), path, f"{label}.citation_scores"),
        top_citation_score=_optional_number(case, "top_citation_score", path, label),
        average_citation_score=_optional_number(case, "average_citation_score", path, label),
        duplicate_citation_count=(
            _integer(case.get("duplicate_citation_count", 0), path, f"{label}.duplicate_citation_count")
        ),
        latency_ms=_number(case.get("latency_ms"), path, f"{label}.latency_ms", minimum=0.0),
        llm_provider=_required_str(case, "llm_provider", path, label),
        model_name=_optional_str(case, "model_name"),
        case_passed=_required_bool(case, "case_passed", path, label),
        error_type=_safe_error(case.get("error_type")),
        error_message=_safe_error(case.get("error_message")),
        **optional_scores,
        numeric_mismatch=bool(optional_flag("numeric_mismatch", False)),
        query_numeric_claims=_string_tuple(source("query_numeric_claims"), path, f"{label}.query_numeric_claims"),
        evidence_numeric_claims=_string_tuple(source("evidence_numeric_claims"), path, f"{label}.evidence_numeric_claims"),
        missing_numeric_claims=_string_tuple(source("missing_numeric_claims"), path, f"{label}.missing_numeric_claims"),
        scope_risk=bool(optional_flag("scope_risk", False)),
        scope_risk_reason=_safe_error(source("scope_risk_reason")),
        direct_support=optional_flag("direct_support"),
        matched_query_terms=_string_tuple(source("matched_query_terms"), path, f"{label}.matched_query_terms"),
        missing_query_terms=_string_tuple(source("missing_query_terms"), path, f"{label}.missing_query_terms"),
        decision_reasons=_string_tuple(source("decision_reasons"), path, f"{label}.decision_reasons"),
        provider_fallback_used=_optional_bool(case, "provider_fallback_used", path, label),
        generation_attempt_count=(
            _integer(case["generation_attempt_count"], path, f"{label}.generation_attempt_count", minimum=1)
            if case.get("generation_attempt_count") is not None
            else None
        ),
        generation_error_type=_safe_error(case.get("generation_error_type")),
        available_fields=frozenset(case.keys()) | frozenset(breakdown.keys()),
    )
    return EvaluationCase(
        **{
            field_name: getattr(provisional, field_name)
            for field_name in provisional.__dataclass_fields__
            if field_name != "diagnostic_category"
        },
        diagnostic_category=classify_case(provisional),
    )


def _benchmark_question_count(project_root: Path) -> int | None:
    dataset_path = project_root / "eval" / "questions.jsonl"
    try:
        return sum(1 for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip())
    except OSError:
        return None


def load_evaluation_results(
    path: Path | None = None,
    *,
    project_root: Path = PROJECT_ROOT,
) -> EvaluationDashboardData:
    result_path = path or resolve_results_path(project_root=project_root)
    if not result_path.exists():
        raise EvaluationResultsError(result_path, "No evaluation result file exists at this path.")
    modified_at, modified_time_ns = get_result_file_metadata(result_path)
    try:
        content = result_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise EvaluationResultsError(result_path, "The evaluation result file could not be read.") from exc
    if not content.strip():
        raise EvaluationResultsError(result_path, "The evaluation result file is empty.")
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise EvaluationResultsError(result_path, "The evaluation result file is not valid JSON.") from exc
    root = _require_mapping(payload, result_path, "result file")
    missing_top_level = {"run", "summary", "results"} - root.keys()
    if missing_top_level:
        raise EvaluationResultsError(
            result_path,
            f"The result file is missing top-level fields: {', '.join(sorted(missing_top_level))}.",
        )
    run = _parse_run(root["run"], result_path)
    summary = _parse_summary(root["summary"], result_path)
    raw_results = root["results"]
    if not isinstance(raw_results, list):
        raise EvaluationResultsError(result_path, "results must be a JSON array.")
    cases = tuple(_parse_case(item, index, result_path) for index, item in enumerate(raw_results))
    if len(cases) != summary.total_questions or run.question_count != summary.total_questions:
        raise EvaluationResultsError(path=result_path, reason="Run, summary, and result question counts do not agree.")
    csv_candidate = result_path.with_suffix(".csv")
    return EvaluationDashboardData(
        run=run,
        summary=summary,
        cases=cases,
        result_path=result_path,
        csv_path=csv_candidate if csv_candidate.is_file() else None,
        modified_at=modified_at,
        modified_time_ns=modified_time_ns,
        benchmark_question_count=_benchmark_question_count(project_root),
    )


def classify_case(case: EvaluationCase) -> DiagnosticCategory:
    if case.error_type or case.error_message:
        return DiagnosticCategory.REQUEST_ERROR
    if case.provider_fallback_detected:
        return DiagnosticCategory.PROVIDER_GENERATION_FAILURE
    if case.should_answer and case.page_hit is False:
        return DiagnosticCategory.RETRIEVAL_PAGE_MISS
    if not case.readiness_correct:
        return DiagnosticCategory.READINESS_MISMATCH
    if not case.should_answer and case.fallback_correct is False:
        return DiagnosticCategory.FALLBACK_GUARDRAIL_FAILURE
    if (
        case.should_answer
        and case.answer_ready
        and not case.fallback_used
        and case.page_hit is True
        and bool(case.missing_keywords)
    ):
        return DiagnosticCategory.ANSWER_COMPLETENESS_FAILURE
    if case.case_passed and not case.should_answer:
        return DiagnosticCategory.PASSED_UNSUPPORTED_FALLBACK
    if case.numeric_mismatch:
        return DiagnosticCategory.NUMERIC_GUARDRAIL_REJECTION
    if case.scope_risk:
        return DiagnosticCategory.LEGAL_SCOPE_GUARDRAIL_REJECTION
    if case.case_passed and case.should_answer:
        return DiagnosticCategory.PASSED_SUPPORTED_ANSWER
    return DiagnosticCategory.OTHER_EVALUATION_FAILURE


def provider_generation_counts(cases: Sequence[EvaluationCase]) -> tuple[int, int]:
    eligible = [case for case in cases if case.should_answer and case.answer_ready]
    generated = sum(not case.provider_fallback_detected for case in eligible)
    return generated, len(eligible)


def provider_generation_availability(cases: Sequence[EvaluationCase]) -> float | None:
    generated, eligible = provider_generation_counts(cases)
    return generated / eligible if eligible else None


def detect_partial_run(data: EvaluationDashboardData) -> bool:
    if data.run.question_id or data.run.limit:
        return True
    if data.benchmark_question_count is not None:
        return data.summary.total_questions < data.benchmark_question_count
    return False


def format_percentage(value: float | None, denominator: int | None = None) -> str:
    if value is None or denominator == 0:
        return "N/A"
    return f"{value * 100:.1f}%"


def format_score(value: float | None, digits: int = 2) -> str:
    return "N/A" if value is None else f"{value:.{digits}f}"


def format_latency(value_ms: float | None) -> str:
    if value_ms is None:
        return "N/A"
    if value_ms >= 1000:
        return f"{value_ms / 1000:.2f} s"
    return f"{value_ms:.0f} ms"


def prepare_kpis(data: EvaluationDashboardData) -> tuple[KPIValue, ...]:
    summary = data.summary
    successful_supported = [case for case in data.cases if case.should_answer and not case.error_type]
    keyword_cases = [case for case in data.cases if case.should_answer and case.keyword_match_score is not None]
    fallback_numerator = sum(case.fallback_correct is True for case in data.cases if not case.should_answer)
    retrieval_numerator = sum(case.page_hit is True for case in successful_supported)
    readiness_numerator = sum(case.readiness_correct for case in data.cases)
    keyword_numerator = sum(case.keyword_match_score == 1.0 for case in keyword_cases)

    def ratio_card(key: str, label: str, numerator: int, denominator: int, value: float, empty: str) -> KPIValue:
        if denominator == 0:
            return KPIValue(key, label, "N/A", "", empty)
        return KPIValue(key, label, f"{numerator} / {denominator}", format_percentage(value), "")

    return (
        ratio_card("case_pass_rate", "Case Pass Rate", summary.passed_questions, summary.total_questions, summary.passed_questions / summary.total_questions if summary.total_questions else 0.0, "No cases in this run"),
        ratio_card("readiness", "Answer Readiness", readiness_numerator, summary.total_questions, summary.answer_readiness_accuracy, "No cases in this run"),
        ratio_card("fallback", "Fallback Accuracy", fallback_numerator, summary.unsupported_questions, summary.fallback_accuracy, "No unsupported cases in this run"),
        ratio_card("retrieval", "Page-Hit Rate", retrieval_numerator, len(successful_supported), summary.retrieval_page_hit_rate, "No successful supported cases in this run"),
        ratio_card("keywords", "Keyword Match", keyword_numerator, len(keyword_cases), summary.keyword_match_rate, "No supported answer scores in this run"),
        KPIValue("confidence", "Supported Confidence", format_score(summary.average_supported_confidence), "", "Calibrated answerability"),
        KPIValue("latency", "Average Latency", format_latency(summary.average_latency_ms), "", "Client-observed end to end"),
        KPIValue("errors", "Request Errors", str(summary.request_error_count), "", "Evaluation transport or response errors", "danger" if summary.request_error_count else "success"),
    )


def evaluate_quality_gates(data: EvaluationDashboardData) -> tuple[QualityGate, ...]:
    summary = data.summary

    def exact_gate(key: str, label: str, passed: bool, value: str, detail: str) -> QualityGate:
        return QualityGate(key, label, QualityGateStatus.PASSED if passed else QualityGateStatus.NEEDS_ATTENTION, value, detail)

    gates: list[QualityGate] = [
        exact_gate("request_errors", "Request errors", summary.request_error_count == 0, str(summary.request_error_count), "Must remain zero."),
        exact_gate("readiness", "Answer-readiness accuracy", summary.total_questions > 0 and summary.answer_readiness_accuracy == 1.0, format_percentage(summary.answer_readiness_accuracy, summary.total_questions), "Evidence gating matches benchmark support labels."),
    ]
    if summary.unsupported_questions == 0:
        gates.append(QualityGate("fallback", "Unsupported fallback accuracy", QualityGateStatus.NOT_APPLICABLE, "N/A", "No unsupported cases in this run."))
    else:
        gates.append(exact_gate("fallback", "Unsupported fallback accuracy", summary.fallback_accuracy == 1.0, format_percentage(summary.fallback_accuracy), "Unsupported questions must use a zero-citation fallback."))

    successful_supported_count = sum(case.should_answer and not case.error_type for case in data.cases)
    if successful_supported_count == 0:
        gates.append(QualityGate("retrieval", "Retrieval page-hit rate", QualityGateStatus.NOT_APPLICABLE, "N/A", "No successful supported cases in this run."))
    else:
        gates.append(exact_gate("retrieval", "Retrieval page-hit rate", summary.retrieval_page_hit_rate == 1.0, format_percentage(summary.retrieval_page_hit_rate), "Supported cases must cite an expected page."))

    gates.append(exact_gate("duplicates", "Duplicate citation warning", not data.run.duplicate_citation_warning, str(data.run.duplicate_citation_warning).lower(), "Duplicate citation identities should not occur."))
    generated, eligible = provider_generation_counts(data.cases)
    if eligible == 0:
        gates.append(QualityGate("provider", "Generated-answer availability", QualityGateStatus.NOT_APPLICABLE, "N/A", "No supported answer-ready cases in this run."))
    else:
        availability = generated / eligible
        gates.append(exact_gate("provider", "Generated-answer availability", generated == eligible, f"{generated} / {eligible} · {format_percentage(availability)}", "Provider availability is reported separately from RAG evidence quality."))
    return tuple(gates)


def filter_cases(cases: Sequence[EvaluationCase], filters: EvaluationFilters | None = None) -> tuple[EvaluationCase, ...]:
    active = filters or EvaluationFilters()
    query = active.search_text.casefold().strip()
    filtered: list[EvaluationCase] = []
    for case in cases:
        if active.result_status == "passed" and not case.case_passed:
            continue
        if active.result_status == "failed" and case.case_passed:
            continue
        if active.diagnostic_categories and case.diagnostic_category.value not in active.diagnostic_categories:
            continue
        if active.support_status == "supported" and not case.should_answer:
            continue
        if active.support_status == "unsupported" and case.should_answer:
            continue
        if active.categories and case.category not in active.categories:
            continue
        if active.difficulties and case.difficulty not in active.difficulties:
            continue
        if active.evidence_statuses and case.evidence_status not in active.evidence_statuses:
            continue
        if active.providers and case.llm_provider not in active.providers:
            continue
        if active.fallback_used is not None and case.fallback_used != active.fallback_used:
            continue
        if active.numeric_mismatch is not None and case.numeric_mismatch != active.numeric_mismatch:
            continue
        if active.scope_risk is not None and case.scope_risk != active.scope_risk:
            continue
        if active.direct_support is not None and case.direct_support != active.direct_support:
            continue
        if query:
            haystack = " ".join((case.id, case.question, case.category, case.answer, *case.missing_keywords)).casefold()
            if query not in haystack:
                continue
        filtered.append(case)
    return tuple(filtered)


def category_chart_data(cases: Sequence[EvaluationCase]) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], int] = {}
    for case in cases:
        outcome = "Passed" if case.case_passed else "Failed"
        counts[(case.category, outcome)] = counts.get((case.category, outcome), 0) + 1
    return [
        {"Category": category, "Outcome": outcome, "Cases": count}
        for (category, outcome), count in sorted(counts.items())
    ]


def difficulty_chart_data(cases: Sequence[EvaluationCase]) -> list[dict[str, Any]]:
    order = {"easy": 0, "moderate": 1, "hard": 2}
    rows = []
    for difficulty in sorted({case.difficulty for case in cases}, key=lambda value: (order.get(value, 99), value)):
        group = [case for case in cases if case.difficulty == difficulty]
        passed = sum(case.case_passed for case in group)
        rows.append({"Difficulty": difficulty.title(), "Pass rate": passed / len(group), "Passed": passed, "Total": len(group)})
    return rows


def evidence_status_chart_data(cases: Sequence[EvaluationCase]) -> list[dict[str, Any]]:
    order = ("insufficient", "weak", "moderate", "strong")
    statuses = list(order) + sorted({case.evidence_status for case in cases} - set(order))
    return [{"Evidence status": status.title(), "Cases": sum(case.evidence_status == status for case in cases)} for status in statuses if any(case.evidence_status == status for case in cases)]


def diagnostic_chart_data(cases: Sequence[EvaluationCase]) -> list[dict[str, Any]]:
    return [
        {"Diagnostic": category.replace("_", " ").title(), "Cases": sum(case.diagnostic_category.value == category for case in cases)}
        for category in sorted({case.diagnostic_category.value for case in cases})
    ]


def confidence_chart_data(cases: Sequence[EvaluationCase]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        score = case.answerability_score
        if score is None and not case.fallback_used:
            score = case.confidence_score
        if score is None:
            continue
        rows.append({"ID": case.id, "Outcome": "Passed" if case.case_passed else "Failed", "Answerability score": score})
    return rows


def latency_chart_data(cases: Sequence[EvaluationCase]) -> list[dict[str, Any]]:
    rows = []
    for case in cases:
        if case.provider_fallback_detected:
            classification = "Provider fallback"
        elif not case.should_answer:
            classification = "Unsupported"
        else:
            classification = "Generated answer"
        rows.append({"ID": case.id, "Request type": classification, "Latency (ms)": case.latency_ms})
    return rows


def provider_chart_data(cases: Sequence[EvaluationCase]) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], int] = {}
    for case in cases:
        if not (case.should_answer and case.answer_ready):
            continue
        outcome = "Provider fallback" if case.provider_fallback_detected else "Generated answer"
        key = (case.llm_provider, outcome)
        counts[key] = counts.get(key, 0) + 1
    return [
        {"Provider": provider, "Generation outcome": outcome, "Cases": count}
        for (provider, outcome), count in sorted(counts.items())
    ]


def aggregate_optional_metric(cases: Sequence[EvaluationCase], field_name: str) -> float | None:
    values = [getattr(case, field_name) for case in cases if getattr(case, field_name) is not None]
    return sum(values) / len(values) if values else None


def unique_values(cases: Iterable[EvaluationCase], field_name: str) -> tuple[str, ...]:
    return tuple(sorted({str(getattr(case, field_name)) for case in cases if getattr(case, field_name) not in (None, "")}))
