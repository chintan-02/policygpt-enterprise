from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from ui.services.evaluation_results_service import (
    DiagnosticCategory,
    EvaluationFilters,
    EvaluationResultsError,
    QualityGateStatus,
    category_chart_data,
    classify_case,
    confidence_chart_data,
    diagnostic_chart_data,
    difficulty_chart_data,
    evaluate_quality_gates,
    evidence_status_chart_data,
    filter_cases,
    format_percentage,
    latency_chart_data,
    load_evaluation_results,
    provider_generation_availability,
    provider_chart_data,
    resolve_results_path,
)


def _supported_case(**overrides: object) -> dict[str, object]:
    case: dict[str, object] = {
        "id": "remote_work_001",
        "question": "What is the allowance and approval rule?",
        "category": "remote_work",
        "difficulty": "easy",
        "evaluation_focus": ["retrieval", "answer_content"],
        "should_answer": True,
        "answer_ready": True,
        "readiness_correct": True,
        "evidence_status": "strong",
        "confidence_score": 0.8,
        "confidence_breakdown": {
            "answerability_score": 0.8,
            "top_retrieval_score": 0.7,
            "average_retrieval_score": 0.6,
            "retrieval_margin": 0.5,
            "lexical_coverage": 0.9,
            "top_chunk_lexical_coverage": 0.85,
            "numeric_consistency": 1.0,
            "numeric_mismatch": False,
            "query_numeric_claims": [],
            "evidence_numeric_claims": ["CAD:300"],
            "missing_numeric_claims": [],
            "scope_risk": False,
            "scope_risk_reason": None,
            "direct_support": True,
            "matched_query_terms": ["allowance"],
            "missing_query_terms": [],
            "decision_reasons": ["Direct support was found."],
        },
        "expected_pages": [5],
        "retrieved_pages": [5],
        "page_hit": True,
        "expected_answer_keywords": ["CAD 300"],
        "matched_keywords": ["CAD 300"],
        "missing_keywords": [],
        "keyword_match_score": 1.0,
        "answer": "The allowance is CAD 300.",
        "fallback_used": False,
        "fallback_correct": None,
        "citation_count": 1,
        "retrieved_filenames": ["sample.pdf"],
        "citation_scores": [0.7],
        "top_citation_score": 0.7,
        "average_citation_score": 0.7,
        "duplicate_citation_count": 0,
        "latency_ms": 120.0,
        "llm_provider": "groq",
        "model_name": "test-model",
        "case_passed": True,
        "error_type": None,
        "error_message": None,
    }
    case.update(overrides)
    return case


def _unsupported_case(**overrides: object) -> dict[str, object]:
    case = _supported_case(
        id="unsupported_001",
        question="What is an unsupported private fact?",
        category="unsupported",
        difficulty="moderate",
        should_answer=False,
        answer_ready=False,
        readiness_correct=True,
        evidence_status="insufficient",
        confidence_score=0.0,
        confidence_breakdown=None,
        expected_pages=[],
        retrieved_pages=[],
        page_hit=None,
        expected_answer_keywords=[],
        matched_keywords=[],
        missing_keywords=[],
        keyword_match_score=None,
        answer="I could not find enough supporting evidence.",
        fallback_used=True,
        fallback_correct=True,
        citation_count=0,
        retrieved_filenames=[],
        citation_scores=[],
        top_citation_score=0.0,
        average_citation_score=0.0,
        latency_ms=40.0,
        llm_provider="none",
        model_name=None,
        case_passed=True,
    )
    case.update(overrides)
    return case


def _summary(cases: list[dict[str, object]], **overrides: object) -> dict[str, object]:
    total = len(cases)
    supported = [case for case in cases if case["should_answer"]]
    unsupported = [case for case in cases if not case["should_answer"]]
    successful_supported = [case for case in supported if not case.get("error_type")]
    values: dict[str, object] = {
        "total_questions": total,
        "supported_questions": len(supported),
        "unsupported_questions": len(unsupported),
        "passed_questions": sum(case["case_passed"] is True for case in cases),
        "failed_questions_count": sum(case["case_passed"] is False for case in cases),
        "request_error_count": sum(bool(case.get("error_type")) for case in cases),
        "answer_readiness_accuracy": sum(case["readiness_correct"] is True for case in cases) / total if total else 0.0,
        "fallback_accuracy": sum(case["fallback_correct"] is True for case in unsupported) / len(unsupported) if unsupported else 0.0,
        "retrieval_page_hit_rate": sum(case["page_hit"] is True for case in successful_supported) / len(successful_supported) if successful_supported else 0.0,
        "keyword_match_rate": sum(float(case["keyword_match_score"]) for case in supported if case["keyword_match_score"] is not None) / len(supported) if supported else 0.0,
        "average_confidence": sum(float(case["confidence_score"]) for case in cases) / total if total else 0.0,
        "average_supported_confidence": sum(float(case["confidence_score"]) for case in supported) / len(supported) if supported else 0.0,
        "average_latency_ms": sum(float(case["latency_ms"]) for case in cases) / total if total else 0.0,
        "average_citation_count": sum(int(case["citation_count"]) for case in cases) / total if total else 0.0,
    }
    values.update(overrides)
    return values


def _payload(cases: list[dict[str, object]], **summary_overrides: object) -> dict[str, object]:
    return {
        "run": {
            "run_id": "run-123",
            "started_at_utc": "2026-01-01T00:00:00Z",
            "completed_at_utc": "2026-01-01T00:00:01Z",
            "duration_ms": 1000.0,
            "base_url": "http://localhost:8000",
            "endpoint": "/api/v1/documents/ask",
            "dataset_path": "eval/questions.jsonl",
            "dataset_sha256": "a" * 64,
            "top_k": 5,
            "timeout_seconds": 60.0,
            "request_delay_seconds": 0.0,
            "question_count": len(cases),
            "duplicate_citation_warning": False,
        },
        "summary": _summary(cases, **summary_overrides),
        "results": cases,
        "future_optional_field": {"ignored": True},
    }


def _write_payload(root: Path, payload: dict[str, object], name: str = "latest_eval_results.json") -> Path:
    path = root / "eval" / "results" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _write_dataset(root: Path, count: int) -> None:
    path = root / "eval" / "questions.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join("{}" for _ in range(count)), encoding="utf-8")


def test_loads_valid_step_13_results_and_file_metadata(tmp_path: Path) -> None:
    path = _write_payload(tmp_path, _payload([_supported_case()]))

    data = load_evaluation_results(path, project_root=tmp_path)

    assert data.run.run_id == "run-123"
    assert data.summary.passed_questions == 1
    assert data.cases[0].answerability_score == 0.8
    assert data.modified_time_ns > 0
    assert data.modified_at.tzinfo is not None


def test_loads_older_step_12_results_without_confidence_fields(tmp_path: Path) -> None:
    case = _supported_case()
    case.pop("confidence_breakdown")
    path = _write_payload(tmp_path, _payload([case]))

    loaded = load_evaluation_results(path, project_root=tmp_path).cases[0]

    assert loaded.answerability_score is None
    assert loaded.direct_support is None
    assert loaded.decision_reasons == ()


@pytest.mark.parametrize(
    ("content", "message"),
    [("", "empty"), ("{broken", "valid JSON")],
)
def test_rejects_empty_and_invalid_json(tmp_path: Path, content: str, message: str) -> None:
    path = tmp_path / "result.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(EvaluationResultsError, match=message):
        load_evaluation_results(path, project_root=tmp_path)


def test_missing_result_file_has_safe_error(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"
    with pytest.raises(EvaluationResultsError, match="No evaluation result") as error:
        load_evaluation_results(path, project_root=tmp_path)
    assert error.value.path == path


@pytest.mark.parametrize("missing_field", ["run", "summary", "results"])
def test_rejects_missing_top_level_fields(tmp_path: Path, missing_field: str) -> None:
    payload = _payload([_supported_case()])
    payload.pop(missing_field)
    path = _write_payload(tmp_path, payload)

    with pytest.raises(EvaluationResultsError, match=missing_field):
        load_evaluation_results(path, project_root=tmp_path)


def test_rejects_malformed_summary(tmp_path: Path) -> None:
    payload = _payload([_supported_case()])
    payload["summary"] = {"total_questions": "one"}
    path = _write_payload(tmp_path, payload)

    with pytest.raises(EvaluationResultsError, match="summary.total_questions"):
        load_evaluation_results(path, project_root=tmp_path)


def test_rejects_malformed_result_entry(tmp_path: Path) -> None:
    payload = _payload([_supported_case()])
    payload["results"] = ["not-an-object"]
    path = _write_payload(tmp_path, payload)

    with pytest.raises(EvaluationResultsError, match=r"results\[0\]"):
        load_evaluation_results(path, project_root=tmp_path)


def test_rejects_malformed_required_result_field(tmp_path: Path) -> None:
    path = _write_payload(tmp_path, _payload([_supported_case(answer=123)]))

    with pytest.raises(EvaluationResultsError, match=r"results\[0\]\.answer"):
        load_evaluation_results(path, project_root=tmp_path)


def test_future_and_secret_fields_are_not_exposed(tmp_path: Path) -> None:
    case = _supported_case(api_key="secret", evidence_text="hidden evidence")
    path = _write_payload(tmp_path, _payload([case]))

    loaded = load_evaluation_results(path, project_root=tmp_path).cases[0]

    assert not hasattr(loaded, "api_key")
    assert not hasattr(loaded, "evidence_text")
    assert "secret" not in repr(loaded)
    assert "hidden evidence" not in repr(loaded)


def test_sensitive_error_detail_is_redacted(tmp_path: Path) -> None:
    case = _supported_case(case_passed=False, error_type="HTTPError", error_message="authorization token leaked")
    path = _write_payload(tmp_path, _payload([case]))

    loaded = load_evaluation_results(path, project_root=tmp_path).cases[0]

    assert loaded.error_message == "[sensitive error detail redacted]"


def test_partial_and_full_run_detection_from_dataset(tmp_path: Path) -> None:
    _write_dataset(tmp_path, 2)
    partial_path = _write_payload(tmp_path, _payload([_supported_case()]))
    partial = load_evaluation_results(partial_path, project_root=tmp_path)

    full_path = _write_payload(tmp_path, _payload([_supported_case(), _unsupported_case()]), "full.json")
    full = load_evaluation_results(full_path, project_root=tmp_path)

    assert partial.is_partial_run is True
    assert full.is_partial_run is False


def test_environment_override_is_repo_relative_and_safe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POLICYGPT_EVAL_RESULTS_PATH", "custom/results.json")
    assert resolve_results_path(project_root=tmp_path) == (tmp_path / "custom/results.json").resolve()

    monkeypatch.setenv("POLICYGPT_EVAL_RESULTS_PATH", "../outside.json")
    with pytest.raises(EvaluationResultsError, match="inside the repository"):
        resolve_results_path(project_root=tmp_path)


def test_absolute_environment_override_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(EvaluationResultsError, match="repository-relative"):
        resolve_results_path(tmp_path / "result.json", project_root=tmp_path)


def test_zero_denominator_percentage_is_na() -> None:
    assert format_percentage(0.0, 0) == "N/A"
    assert format_percentage(None) == "N/A"


def _loaded_case(tmp_path: Path, case: dict[str, object]):
    path = _write_payload(tmp_path, _payload([case]))
    return load_evaluation_results(path, project_root=tmp_path).cases[0]


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        (_supported_case(), DiagnosticCategory.PASSED_SUPPORTED_ANSWER),
        (_unsupported_case(), DiagnosticCategory.PASSED_UNSUPPORTED_FALLBACK),
        (_supported_case(case_passed=False, fallback_used=True), DiagnosticCategory.PROVIDER_GENERATION_FAILURE),
        (_supported_case(case_passed=False, page_hit=False), DiagnosticCategory.RETRIEVAL_PAGE_MISS),
        (_supported_case(case_passed=False, readiness_correct=False), DiagnosticCategory.READINESS_MISMATCH),
        (_unsupported_case(case_passed=False, fallback_correct=False), DiagnosticCategory.FALLBACK_GUARDRAIL_FAILURE),
        (_supported_case(case_passed=False, missing_keywords=["approval"], keyword_match_score=0.5), DiagnosticCategory.ANSWER_COMPLETENESS_FAILURE),
        (_supported_case(case_passed=False, numeric_mismatch=True), DiagnosticCategory.NUMERIC_GUARDRAIL_REJECTION),
        (_supported_case(case_passed=False, scope_risk=True), DiagnosticCategory.LEGAL_SCOPE_GUARDRAIL_REJECTION),
        (_supported_case(case_passed=False, error_type="Timeout"), DiagnosticCategory.REQUEST_ERROR),
        (_supported_case(case_passed=False), DiagnosticCategory.OTHER_EVALUATION_FAILURE),
    ],
)
def test_diagnostic_classification(tmp_path: Path, case: dict[str, object], expected: DiagnosticCategory) -> None:
    assert _loaded_case(tmp_path, case).diagnostic_category == expected


def test_correct_unsupported_guardrail_remains_a_pass(tmp_path: Path) -> None:
    case = _loaded_case(tmp_path, _unsupported_case(numeric_mismatch=True, scope_risk=True))
    assert classify_case(case) == DiagnosticCategory.PASSED_UNSUPPORTED_FALLBACK


def test_filters_cover_each_supported_dimension(tmp_path: Path) -> None:
    cases = [
        _supported_case(),
        _unsupported_case(),
        _supported_case(
            id="expense_001",
            category="expenses",
            difficulty="hard",
            evidence_status="moderate",
            llm_provider="openai",
            fallback_used=True,
            case_passed=False,
            numeric_mismatch=True,
            scope_risk=True,
            direct_support=False,
            answer="Missing receipt keyword",
            missing_keywords=["receipt"],
        ),
    ]
    path = _write_payload(tmp_path, _payload(cases))
    loaded = load_evaluation_results(path, project_root=tmp_path).cases

    assert len(filter_cases(loaded, EvaluationFilters(result_status="passed"))) == 2
    assert len(filter_cases(loaded, EvaluationFilters(result_status="failed"))) == 1
    assert len(filter_cases(loaded, EvaluationFilters(support_status="unsupported"))) == 1
    assert len(filter_cases(loaded, EvaluationFilters(categories=("expenses",)))) == 1
    assert len(filter_cases(loaded, EvaluationFilters(difficulties=("hard",)))) == 1
    assert len(filter_cases(loaded, EvaluationFilters(evidence_statuses=("moderate",)))) == 1
    assert len(filter_cases(loaded, EvaluationFilters(providers=("openai",)))) == 1
    assert len(filter_cases(loaded, EvaluationFilters(fallback_used=True))) == 2
    assert len(filter_cases(loaded, EvaluationFilters(numeric_mismatch=True))) == 1
    assert len(filter_cases(loaded, EvaluationFilters(scope_risk=True))) == 1
    assert len(filter_cases(loaded, EvaluationFilters(direct_support=False))) == 1
    assert len(filter_cases(loaded, EvaluationFilters(search_text="receipt"))) == 1
    assert len(filter_cases(loaded, EvaluationFilters(result_status="failed", categories=("expenses",), providers=("openai",)))) == 1
    assert filter_cases(loaded) == loaded


def test_all_quality_gates_pass_for_complete_good_run(tmp_path: Path) -> None:
    path = _write_payload(tmp_path, _payload([_supported_case(), _unsupported_case()]))
    gates = evaluate_quality_gates(load_evaluation_results(path, project_root=tmp_path))
    assert all(gate.status == QualityGateStatus.PASSED for gate in gates)


def test_quality_gate_failures_and_not_applicable_states(tmp_path: Path) -> None:
    request_error = _supported_case(case_passed=False, readiness_correct=False, error_type="Timeout")
    path = _write_payload(
        tmp_path,
        _payload(
            [request_error],
            request_error_count=1,
            answer_readiness_accuracy=0.0,
            retrieval_page_hit_rate=0.0,
        ),
    )
    data = load_evaluation_results(path, project_root=tmp_path)
    data = replace(data, run=replace(data.run, duplicate_citation_warning=True))
    gates = {gate.key: gate for gate in evaluate_quality_gates(data)}

    assert gates["request_errors"].status == QualityGateStatus.NEEDS_ATTENTION
    assert gates["readiness"].status == QualityGateStatus.NEEDS_ATTENTION
    assert gates["fallback"].status == QualityGateStatus.NOT_APPLICABLE
    assert gates["retrieval"].status == QualityGateStatus.NOT_APPLICABLE
    assert gates["duplicates"].status == QualityGateStatus.NEEDS_ATTENTION


def test_provider_fallback_only_affects_provider_gate(tmp_path: Path) -> None:
    provider_case = _supported_case(case_passed=False, fallback_used=True, missing_keywords=["CAD 300"], keyword_match_score=0.0)
    path = _write_payload(tmp_path, _payload([provider_case]))
    gates = {gate.key: gate for gate in evaluate_quality_gates(load_evaluation_results(path, project_root=tmp_path))}

    assert gates["request_errors"].status == QualityGateStatus.PASSED
    assert gates["readiness"].status == QualityGateStatus.PASSED
    assert gates["retrieval"].status == QualityGateStatus.PASSED
    assert gates["provider"].status == QualityGateStatus.NEEDS_ATTENTION
    assert provider_generation_availability(_loaded_case_list(tmp_path, provider_case)) == 0.0


def _loaded_case_list(tmp_path: Path, *cases: dict[str, object]):
    path = _write_payload(tmp_path, _payload(list(cases)), "case_list.json")
    return load_evaluation_results(path, project_root=tmp_path).cases


def test_chart_data_handles_empty_and_one_case(tmp_path: Path) -> None:
    case = _loaded_case(tmp_path, _supported_case())
    for helper in (
        category_chart_data,
        difficulty_chart_data,
        evidence_status_chart_data,
        diagnostic_chart_data,
        confidence_chart_data,
        latency_chart_data,
        provider_chart_data,
    ):
        assert helper([]) == []
        assert len(helper([case])) == 1


def test_chart_aggregations_and_confidence_preference(tmp_path: Path) -> None:
    cases = _loaded_case_list(tmp_path, _supported_case(), _unsupported_case())

    assert {row["Outcome"] for row in category_chart_data(cases)} == {"Passed"}
    assert {row["Difficulty"] for row in difficulty_chart_data(cases)} == {"Easy", "Moderate"}
    assert {row["Evidence status"] for row in evidence_status_chart_data(cases)} == {"Strong", "Insufficient"}
    confidence_rows = confidence_chart_data(cases)
    assert confidence_rows == [{"ID": "remote_work_001", "Outcome": "Passed", "Answerability score": 0.8}]
    latency_classes = {row["Request type"] for row in latency_chart_data(cases)}
    assert latency_classes == {"Generated answer", "Unsupported"}


def test_provider_fallback_latency_classification(tmp_path: Path) -> None:
    case = _loaded_case(tmp_path, _supported_case(case_passed=False, fallback_used=True))
    assert latency_chart_data([case])[0]["Request type"] == "Provider fallback"
    assert provider_chart_data([case]) == [
        {
            "Provider": "groq",
            "Generation outcome": "Provider fallback",
            "Cases": 1,
        }
    ]
