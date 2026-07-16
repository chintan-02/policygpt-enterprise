from __future__ import annotations

from html import escape
from typing import Iterable

import streamlit as st

from ui.components.badges import evidence_variant, render_badge_row
from ui.services.evaluation_results_service import (
    DiagnosticCategory,
    EvaluationCase,
    KPIValue,
    QualityGate,
    QualityGateStatus,
    format_score,
)


DIAGNOSTIC_LABELS = {
    DiagnosticCategory.PASSED_SUPPORTED_ANSWER: "Passed · supported answer",
    DiagnosticCategory.PASSED_UNSUPPORTED_FALLBACK: "Passed · unsupported fallback",
    DiagnosticCategory.PROVIDER_GENERATION_FAILURE: "Provider generation failure",
    DiagnosticCategory.RETRIEVAL_PAGE_MISS: "Retrieval page miss",
    DiagnosticCategory.READINESS_MISMATCH: "Readiness mismatch",
    DiagnosticCategory.FALLBACK_GUARDRAIL_FAILURE: "Fallback guardrail failure",
    DiagnosticCategory.ANSWER_COMPLETENESS_FAILURE: "Answer completeness failure",
    DiagnosticCategory.NUMERIC_GUARDRAIL_REJECTION: "Numeric guardrail rejection",
    DiagnosticCategory.LEGAL_SCOPE_GUARDRAIL_REJECTION: "Legal-scope guardrail rejection",
    DiagnosticCategory.REQUEST_ERROR: "Request error",
    DiagnosticCategory.OTHER_EVALUATION_FAILURE: "Other evaluation failure",
}


def diagnostic_label(category: DiagnosticCategory | str) -> str:
    try:
        normalized = category if isinstance(category, DiagnosticCategory) else DiagnosticCategory(category)
    except ValueError:
        return str(category).replace("_", " ").title()
    return DIAGNOSTIC_LABELS[normalized]


def diagnostic_variant(category: DiagnosticCategory) -> str:
    if category in {
        DiagnosticCategory.PASSED_SUPPORTED_ANSWER,
        DiagnosticCategory.PASSED_UNSUPPORTED_FALLBACK,
    }:
        return "success"
    if category in {
        DiagnosticCategory.PROVIDER_GENERATION_FAILURE,
        DiagnosticCategory.ANSWER_COMPLETENESS_FAILURE,
        DiagnosticCategory.NUMERIC_GUARDRAIL_REJECTION,
        DiagnosticCategory.LEGAL_SCOPE_GUARDRAIL_REJECTION,
    }:
        return "warning"
    return "danger"


def gate_variant(status: QualityGateStatus) -> str:
    return {
        QualityGateStatus.PASSED: "success",
        QualityGateStatus.NEEDS_ATTENTION: "warning",
        QualityGateStatus.NOT_APPLICABLE: "neutral",
    }[status]


def gate_label(status: QualityGateStatus) -> str:
    return {
        QualityGateStatus.PASSED: "Passed",
        QualityGateStatus.NEEDS_ATTENTION: "Needs attention",
        QualityGateStatus.NOT_APPLICABLE: "Not applicable",
    }[status]


def confidence_status(score: float | None) -> str:
    if score is None:
        return "Unavailable"
    if score >= 0.75:
        return "Strong"
    if score >= 0.5:
        return "Moderate"
    if score >= 0.25:
        return "Weak"
    return "Insufficient"


def format_items(values: Iterable[object], empty: str = "None") -> str:
    items = [str(value) for value in values]
    return ", ".join(items) if items else empty


def render_metric_card(metric: KPIValue) -> None:
    secondary = (
        f'<div class="pgpt-eval-metric-secondary">{escape(metric.secondary)}</div>'
        if metric.secondary
        else ""
    )
    st.markdown(
        f"""
        <div class="pgpt-eval-metric pgpt-eval-metric-{escape(metric.status)}">
            <div class="pgpt-small-label">{escape(metric.label)}</div>
            <div class="pgpt-eval-metric-value">{escape(metric.primary)}</div>
            {secondary}
            <div class="pgpt-eval-metric-caption">{escape(metric.caption)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_quality_gate(gate: QualityGate) -> None:
    variant = gate_variant(gate.status)
    st.markdown(
        f"""
        <div class="pgpt-eval-gate">
            <div>
                <div class="pgpt-eval-gate-title">{escape(gate.label)}</div>
                <div class="pgpt-muted">{escape(gate.detail)}</div>
            </div>
            <div class="pgpt-eval-gate-result">
                <span class="pgpt-badge pgpt-badge-{variant}">{escape(gate_label(gate.status))}</span>
                <span class="pgpt-eval-gate-value">{escape(gate.value)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_provider_warning() -> None:
    st.markdown(
        """
        <div class="pgpt-eval-provider-warning">
            <div class="pgpt-card-title">Provider fallback detected</div>
            <div class="pgpt-muted">
                The evidence pipeline remained answer-ready, but one or more generated
                answers were replaced by the citation-only fallback because the configured
                LLM provider was unavailable.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_results(path: str) -> None:
    st.markdown(
        f"""
        <div class="pgpt-eval-empty">
            <div class="pgpt-card-title">No evaluation results found</div>
            <div class="pgpt-muted">Expected result file: {escape(path)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.code(
        "python eval/validate_dataset.py\n"
        "python eval/run_eval.py --request-delay-seconds 5",
        language="bash",
    )


def render_invalid_results(path: str, reason: str) -> None:
    st.markdown(
        f"""
        <div class="pgpt-eval-invalid">
            <div class="pgpt-card-title">The evaluation result file could not be validated.</div>
            <div class="pgpt-muted">{escape(reason)}</div>
            <div class="pgpt-eval-path">{escape(path)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Regenerate the artifact from the repository root after validating the dataset.")
    st.code(
        "python eval/validate_dataset.py\n"
        "python eval/run_eval.py --request-delay-seconds 5",
        language="bash",
    )


def render_case_status(case: EvaluationCase) -> None:
    render_badge_row(
        [
            ("Result", "Passed" if case.case_passed else "Review", "success" if case.case_passed else "danger"),
            ("Diagnostic", diagnostic_label(case.diagnostic_category), diagnostic_variant(case.diagnostic_category)),
            ("Evidence", case.evidence_status.title(), evidence_variant(case.evidence_status)),
            ("Answer ready", str(case.answer_ready), "success" if case.answer_ready == case.should_answer else "danger"),
            ("Fallback", str(case.fallback_used), "warning" if case.fallback_used else "neutral"),
        ]
    )


def render_answer_panel(case: EvaluationCase) -> None:
    if case.provider_fallback_detected:
        css_class = "pgpt-eval-answer-provider"
        title = "Citation-only provider fallback"
    elif not case.should_answer and case.fallback_used:
        css_class = "pgpt-eval-answer-unsupported"
        title = "Unsupported-answer fallback"
    else:
        css_class = "pgpt-eval-answer-generated"
        title = "Generated answer"
    st.markdown(
        f"""
        <div class="pgpt-eval-answer {css_class}">
            <div class="pgpt-card-title">{escape(title)}</div>
            <div class="pgpt-answer">{escape(case.answer) or "No answer text recorded."}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chip_list(label: str, values: Iterable[object], variant: str = "neutral") -> None:
    items = list(values)
    chips = "".join(
        f'<span class="pgpt-badge pgpt-badge-{variant}">{escape(str(value))}</span>'
        for value in items
    )
    if not chips:
        chips = '<span class="pgpt-muted">None recorded</span>'
    st.markdown(
        f'<div class="pgpt-small-label">{escape(label)}</div><div class="pgpt-eval-chips">{chips}</div>',
        unsafe_allow_html=True,
    )


def render_confidence_breakdown(case: EvaluationCase) -> None:
    score_fields = [
        ("Answerability", case.answerability_score),
        ("Top retrieval", case.top_retrieval_score),
        ("Average retrieval", case.average_retrieval_score),
        ("Retrieval margin", case.retrieval_margin),
        ("Lexical coverage", case.lexical_coverage),
        ("Top-chunk lexical", case.top_chunk_lexical_coverage),
        ("Numeric consistency", case.numeric_consistency),
    ]
    available_scores = [(label, value) for label, value in score_fields if value is not None]
    if not available_scores:
        st.info("This result predates the optional confidence-breakdown fields.")
        return
    columns = st.columns(min(4, len(available_scores)))
    for index, (label, value) in enumerate(available_scores):
        with columns[index % len(columns)]:
            st.metric(label, format_score(value, 4))

    flags = [
        ("Direct support", str(case.direct_support) if case.direct_support is not None else "N/A", "success" if case.direct_support else "neutral"),
        ("Numeric mismatch", str(case.numeric_mismatch), "danger" if case.numeric_mismatch else "success"),
        ("Scope risk", str(case.scope_risk), "danger" if case.scope_risk else "success"),
    ]
    render_badge_row(flags)
