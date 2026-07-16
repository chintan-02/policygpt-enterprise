from __future__ import annotations

import time
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from ui.components.badges import evidence_variant, render_badge_row
from ui.components.cards import render_page_header
from ui.components.evaluation_components import (
    confidence_status,
    diagnostic_label,
    format_items,
    render_answer_panel,
    render_case_status,
    render_chip_list,
    render_confidence_breakdown,
    render_empty_results,
    render_invalid_results,
    render_metric_card,
    render_provider_warning,
    render_quality_gate,
)
from ui.services.evaluation_results_service import (
    DiagnosticCategory,
    EvaluationCase,
    EvaluationDashboardData,
    EvaluationFilters,
    EvaluationResultsError,
    aggregate_optional_metric,
    category_chart_data,
    confidence_chart_data,
    diagnostic_chart_data,
    difficulty_chart_data,
    evaluate_quality_gates,
    evidence_status_chart_data,
    filter_cases,
    format_latency,
    format_percentage,
    format_score,
    get_result_file_metadata,
    latency_chart_data,
    load_evaluation_results,
    prepare_kpis,
    provider_chart_data,
    provider_generation_availability,
    provider_generation_counts,
    resolve_results_path,
    unique_values,
)
from ui.styles import load_global_styles


FILTER_DEFAULTS = {
    "eval_filter_status": "all",
    "eval_filter_diagnostics": [],
    "eval_filter_support": "all",
    "eval_filter_categories": [],
    "eval_filter_difficulties": [],
    "eval_filter_evidence": [],
    "eval_filter_providers": [],
    "eval_filter_fallback": "all",
    "eval_filter_numeric": "all",
    "eval_filter_scope": "all",
    "eval_filter_direct": "all",
    "eval_filter_search": "",
}


def _reset_filters() -> None:
    for key, value in FILTER_DEFAULTS.items():
        st.session_state[key] = value


def _optional_boolean(value: str) -> bool | None:
    return {"true": True, "false": False}.get(value)


@st.cache_data(show_spinner=False)
def _load_cached_results(path_text: str, modified_time_ns: int) -> EvaluationDashboardData:
    del modified_time_ns
    return load_evaluation_results(Path(path_text))


def _load_dashboard_data() -> tuple[EvaluationDashboardData | None, EvaluationResultsError | None, Path]:
    try:
        path = resolve_results_path()
    except EvaluationResultsError as exc:
        return None, exc, exc.path
    if not path.exists():
        return None, EvaluationResultsError(path, "No evaluation result file exists at this path."), path
    try:
        _, modified_time_ns = get_result_file_metadata(path)
        return _load_cached_results(str(path), modified_time_ns), None, path
    except EvaluationResultsError as exc:
        return None, exc, path


def _render_run_header(data: EvaluationDashboardData) -> None:
    run = data.run
    abbreviated_hash = f"{run.dataset_sha256[:12]}…" if run.dataset_sha256 else "N/A"
    metadata = [
        ("Run ID", run.run_id),
        ("Completed", run.completed_at_utc or run.started_at_utc or "N/A"),
        ("Dataset", abbreviated_hash),
        ("Questions", str(data.summary.total_questions)),
        ("Top-k", str(run.top_k) if run.top_k is not None else "N/A"),
        ("Backend", run.base_url or "N/A"),
        ("File updated", data.modified_at.strftime("%Y-%m-%d %H:%M:%S UTC")),
    ]
    st.markdown(
        "<div class='pgpt-card'><div class='pgpt-small-label'>Run trace</div>"
        + "<div class='pgpt-muted'>"
        + " &nbsp;·&nbsp; ".join(
            f"<b>{escape(label)}:</b> {escape(value)}" for label, value in metadata
        )
        + "</div></div>",
        unsafe_allow_html=True,
    )

    provider_fallback = any(case.provider_fallback_detected for case in data.cases)
    badges = [
        ("Run", "Completed" if run.completed_at_utc else "Recorded", "success"),
        ("Coverage", "Partial" if data.is_partial_run else "Full", "warning" if data.is_partial_run else "success"),
    ]
    if data.summary.request_error_count:
        badges.append(("Requests", f"{data.summary.request_error_count} error(s)", "danger"))
    else:
        badges.append(("Requests", "No errors", "success"))
    if provider_fallback:
        badges.append(("Generation", "Provider fallback detected", "warning"))
    render_badge_row(badges)


def _render_freshness_warnings(data: EvaluationDashboardData) -> None:
    if data.is_partial_run:
        benchmark_count = data.benchmark_question_count
        if benchmark_count:
            st.info(
                f"This result contains only {data.summary.total_questions} of "
                f"{benchmark_count} benchmark questions. Run the full evaluation "
                "before using these metrics as a benchmark."
            )
        else:
            st.info("This appears to be a partial evaluation run. Run the complete dataset before using these metrics as a benchmark.")

    session_started = st.session_state.setdefault("eval_dashboard_session_started_at", time.time())
    if data.modified_at.timestamp() < session_started:
        st.caption("Data freshness: this artifact predates the current dashboard session. Use Refresh results after generating a newer run.")

    if any(case.provider_fallback_detected for case in data.cases):
        render_provider_warning()


def _render_kpis(data: EvaluationDashboardData) -> None:
    metrics = prepare_kpis(data)
    for row_start in (0, 4):
        columns = st.columns(4)
        for column, metric in zip(columns, metrics[row_start : row_start + 4]):
            with column:
                render_metric_card(metric)


def _render_quality_gates(data: EvaluationDashboardData) -> None:
    st.subheader("Production Quality Gates")
    st.caption("Generation-provider availability is kept separate from retrieval and evidence-quality gates.")
    st.markdown('<div class="pgpt-card">', unsafe_allow_html=True)
    for gate in evaluate_quality_gates(data):
        render_quality_gate(gate)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_filters(data: EvaluationDashboardData) -> tuple[EvaluationCase, ...]:
    st.subheader("Benchmark Explorer")
    heading_col, reset_col = st.columns([5, 1])
    with heading_col:
        st.caption("Filter transformed in-memory results; the evaluation artifacts remain read-only.")
    with reset_col:
        st.button("Reset filters", on_click=_reset_filters, width="stretch")

    row1 = st.columns(4)
    with row1[0]:
        st.selectbox("Result status", ("all", "passed", "failed"), key="eval_filter_status")
    with row1[1]:
        st.selectbox("Support behavior", ("all", "supported", "unsupported"), key="eval_filter_support")
    with row1[2]:
        st.multiselect("Category", unique_values(data.cases, "category"), key="eval_filter_categories")
    with row1[3]:
        st.multiselect("Difficulty", unique_values(data.cases, "difficulty"), key="eval_filter_difficulties")

    row2 = st.columns(4)
    with row2[0]:
        st.multiselect(
            "Diagnostic category",
            tuple(category.value for category in DiagnosticCategory),
            format_func=lambda value: diagnostic_label(value),
            key="eval_filter_diagnostics",
        )
    with row2[1]:
        st.multiselect("Evidence status", unique_values(data.cases, "evidence_status"), key="eval_filter_evidence")
    with row2[2]:
        st.multiselect("LLM provider", unique_values(data.cases, "llm_provider"), key="eval_filter_providers")
    with row2[3]:
        st.selectbox("Fallback used", ("all", "true", "false"), key="eval_filter_fallback")

    row3 = st.columns(4)
    with row3[0]:
        st.selectbox("Numeric mismatch", ("all", "true", "false"), key="eval_filter_numeric")
    with row3[1]:
        st.selectbox("Scope risk", ("all", "true", "false"), key="eval_filter_scope")
    with row3[2]:
        st.selectbox("Direct support", ("all", "true", "false"), key="eval_filter_direct")
    with row3[3]:
        st.text_input("Search", placeholder="ID, question, answer, keyword…", key="eval_filter_search")

    filters = EvaluationFilters(
        result_status=st.session_state.get("eval_filter_status", "all"),
        diagnostic_categories=tuple(st.session_state.get("eval_filter_diagnostics", [])),
        support_status=st.session_state.get("eval_filter_support", "all"),
        categories=tuple(st.session_state.get("eval_filter_categories", [])),
        difficulties=tuple(st.session_state.get("eval_filter_difficulties", [])),
        evidence_statuses=tuple(st.session_state.get("eval_filter_evidence", [])),
        providers=tuple(st.session_state.get("eval_filter_providers", [])),
        fallback_used=_optional_boolean(st.session_state.get("eval_filter_fallback", "all")),
        numeric_mismatch=_optional_boolean(st.session_state.get("eval_filter_numeric", "all")),
        scope_risk=_optional_boolean(st.session_state.get("eval_filter_scope", "all")),
        direct_support=_optional_boolean(st.session_state.get("eval_filter_direct", "all")),
        search_text=st.session_state.get("eval_filter_search", ""),
    )
    filtered = filter_cases(data.cases, filters)
    st.caption(f"Showing {len(filtered)} of {len(data.cases)} questions")
    return filtered


def _bar_chart(rows: list[dict[str, object]], *, x: str, y: str, color: str | None = None, horizontal: bool = False) -> None:
    if not rows:
        st.info("No cases match the active filters.")
        return
    chart_data = pd.DataFrame(rows)
    kwargs: dict[str, object] = {"x": x, "y": y, "width": "stretch"}
    if color:
        kwargs["color"] = color
    if horizontal:
        st.bar_chart(chart_data, horizontal=True, **kwargs)
    else:
        st.bar_chart(chart_data, **kwargs)


def _render_charts(cases: tuple[EvaluationCase, ...]) -> None:
    st.subheader("Quality and Outcome Analytics")
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("#### Pass / fail by category")
        _bar_chart(category_chart_data(cases), x="Category", y="Cases", color="Outcome")
        st.markdown("#### Evidence-status distribution")
        _bar_chart(evidence_status_chart_data(cases), x="Evidence status", y="Cases")
        st.markdown("#### Confidence by outcome")
        _bar_chart(confidence_chart_data(cases), x="ID", y="Answerability score", color="Outcome")
    with right:
        st.markdown("#### Pass rate by difficulty")
        _bar_chart(difficulty_chart_data(cases), x="Difficulty", y="Pass rate")
        st.markdown("#### Diagnostic-category distribution")
        _bar_chart(diagnostic_chart_data(cases), x="Diagnostic", y="Cases", horizontal=True)
        st.markdown("#### Client-observed latency by question")
        _bar_chart(latency_chart_data(cases), x="ID", y="Latency (ms)", color="Request type")
        st.caption("Provider retries can inflate end-to-end latency; fallback cases are shown separately.")


def _average_latency(cases: list[EvaluationCase]) -> float | None:
    return sum(case.latency_ms for case in cases) / len(cases) if cases else None


def _render_provider_reliability(data: EvaluationDashboardData) -> None:
    st.subheader("Provider Reliability")
    generated, eligible = provider_generation_counts(data.cases)
    fallback_cases = [case for case in data.cases if case.provider_fallback_detected]
    generated_cases = [
        case for case in data.cases
        if case.should_answer and case.answer_ready and not case.provider_fallback_detected
    ]
    availability = provider_generation_availability(data.cases)
    providers = format_items(unique_values(data.cases, "llm_provider"))
    models = format_items(unique_values(data.cases, "model_name"))

    columns = st.columns(4)
    columns[0].metric("Observed providers", providers)
    columns[1].metric("Answer-ready supported", eligible)
    columns[2].metric("Generated successfully", generated)
    columns[3].metric("Availability", format_percentage(availability, eligible))
    st.caption(f"Observed models: {models}")

    latency_columns = st.columns(3)
    latency_columns[0].metric("Provider fallbacks", len(fallback_cases))
    latency_columns[1].metric("Successful generation latency", format_latency(_average_latency(generated_cases)))
    latency_columns[2].metric("Provider fallback latency", format_latency(_average_latency(fallback_cases)))

    error_types = sorted({case.generation_error_type for case in data.cases if case.generation_error_type})
    if error_types:
        render_chip_list("Generation error types", error_types, "warning")
    if fallback_cases:
        render_provider_warning()
    provider_rows = provider_chart_data(data.cases)
    if provider_rows:
        st.markdown("#### Supported generation outcomes by provider")
        _bar_chart(
            provider_rows,
            x="Provider",
            y="Cases",
            color="Generation outcome",
        )


def _render_confidence_diagnostics(data: EvaluationDashboardData) -> None:
    st.subheader("Confidence Diagnostics")
    st.caption(
        "Confidence is based on retrieval strength, lexical support, retrieval separation, "
        "numeric consistency, and scope guardrails. It is not an LLM self-rating."
    )
    metrics = (
        ("Answerability", aggregate_optional_metric(data.cases, "answerability_score")),
        ("Top retrieval", aggregate_optional_metric(data.cases, "top_retrieval_score")),
        ("Average retrieval", aggregate_optional_metric(data.cases, "average_retrieval_score")),
        ("Lexical coverage", aggregate_optional_metric(data.cases, "lexical_coverage")),
        ("Top-chunk lexical", aggregate_optional_metric(data.cases, "top_chunk_lexical_coverage")),
    )
    columns = st.columns(5)
    for column, (label, value) in zip(columns, metrics):
        column.metric(label, format_score(value))

    direct_denominator = sum(case.direct_support is not None for case in data.cases)
    direct_numerator = sum(case.direct_support is True for case in data.cases)
    flag_columns = st.columns(4)
    flag_columns[0].metric("Direct-support rate", format_percentage(direct_numerator / direct_denominator if direct_denominator else None, direct_denominator))
    flag_columns[1].metric("Numeric mismatches", sum(case.numeric_mismatch for case in data.cases))
    flag_columns[2].metric("Scope risks", sum(case.scope_risk for case in data.cases))
    avg_answerability = aggregate_optional_metric(data.cases, "answerability_score")
    flag_columns[3].metric("Aggregate status", confidence_status(avg_answerability))
    status_order = ("insufficient", "weak", "moderate", "strong")
    render_badge_row(
        [
            (
                "Confidence status",
                f"{status.title()} · {sum(case.evidence_status == status for case in data.cases)}",
                evidence_variant(status),
            )
            for status in status_order
        ]
    )


def _review_rows(cases: tuple[EvaluationCase, ...]) -> list[dict[str, object]]:
    return [
        {
            "ID": case.id,
            "Question": case.question,
            "Category": case.category,
            "Difficulty": case.difficulty,
            "Diagnostic": diagnostic_label(case.diagnostic_category),
            "Should answer": case.should_answer,
            "Answer ready": case.answer_ready,
            "Evidence": case.evidence_status,
            "Expected pages": format_items(case.expected_pages),
            "Retrieved pages": format_items(case.retrieved_pages),
            "Keyword score": format_score(case.keyword_match_score),
            "Missing": len(case.missing_keywords),
            "Confidence": format_score(case.answerability_score if case.answerability_score is not None else case.confidence_score),
            "Provider": case.llm_provider,
            "Fallback": case.fallback_used,
            "Latency": format_latency(case.latency_ms),
            "Passed": case.case_passed,
        }
        for case in cases
    ]


def _render_review_table(cases: tuple[EvaluationCase, ...]) -> None:
    st.subheader("Cases Requiring Review")
    include_all = st.toggle("Include passed cases", value=False, key="eval_include_passed")
    review_cases = cases if include_all else tuple(case for case in cases if not case.case_passed)
    if not review_cases:
        st.success("All cases in the current view passed. Diagnostic detail remains available below.")
        return
    st.dataframe(
        pd.DataFrame(_review_rows(review_cases)),
        width="stretch",
        hide_index=True,
        column_config={"Question": st.column_config.TextColumn(width="large")},
    )


def _render_case_detail(case: EvaluationCase) -> None:
    st.markdown(f"### {case.id} · Case Detail")
    render_case_status(case)

    st.markdown("#### Question")
    st.markdown(case.question)
    meta_columns = st.columns(4)
    meta_columns[0].metric("Category", case.category)
    meta_columns[1].metric("Difficulty", case.difficulty.title())
    meta_columns[2].metric("Expected behavior", "Supported" if case.should_answer else "Fallback")
    meta_columns[3].metric("Evaluation focus", len(case.evaluation_focus))
    render_chip_list("Evaluation focus", case.evaluation_focus)

    st.markdown("#### Decision")
    decision_columns = st.columns(4)
    decision_columns[0].metric("Case passed", str(case.case_passed))
    decision_columns[1].metric("Readiness correct", str(case.readiness_correct))
    decision_columns[2].metric("Fallback correct", "N/A" if case.fallback_correct is None else str(case.fallback_correct))
    decision_columns[3].metric("Evidence status", case.evidence_status.title())
    render_chip_list("Decision reasons", case.decision_reasons)

    st.markdown("#### Answer")
    render_answer_panel(case)

    st.markdown("#### Evidence Validation")
    evidence_columns = st.columns(4)
    evidence_columns[0].metric("Page hit", "N/A" if case.page_hit is None else str(case.page_hit))
    evidence_columns[1].metric("Citations", case.citation_count)
    evidence_columns[2].metric("Top citation", format_score(case.top_citation_score, 4))
    evidence_columns[3].metric("Average citation", format_score(case.average_citation_score, 4))
    render_chip_list("Expected pages", case.expected_pages)
    render_chip_list("Retrieved pages", case.retrieved_pages, "info")
    render_chip_list("Filenames", case.retrieved_filenames)
    render_chip_list("Citation scores", (f"{score:.4f}" for score in case.citation_scores))
    st.caption(f"Duplicate citation count: {case.duplicate_citation_count}")

    st.markdown("#### Answer Completeness")
    completeness_columns = st.columns(2)
    completeness_columns[0].metric("Keyword-match score", format_percentage(case.keyword_match_score, len(case.expected_answer_keywords)))
    completeness_columns[1].metric("Missing keyword count", len(case.missing_keywords))
    render_chip_list("Expected keywords", case.expected_answer_keywords)
    render_chip_list("Matched keywords", case.matched_keywords, "success")
    render_chip_list("Missing keywords", case.missing_keywords, "danger" if case.missing_keywords else "neutral")

    st.markdown("#### Confidence Breakdown")
    render_confidence_breakdown(case)
    confidence_lists = (
        ("Query numeric claims", case.query_numeric_claims),
        ("Evidence numeric claims", case.evidence_numeric_claims),
        ("Missing numeric claims", case.missing_numeric_claims),
        ("Matched query terms", case.matched_query_terms),
        ("Missing query terms", case.missing_query_terms),
    )
    for label, values in confidence_lists:
        if values or label.lower().replace(" ", "_") in case.available_fields:
            render_chip_list(label, values)
    if case.scope_risk_reason:
        st.warning(f"Scope-risk reason: {case.scope_risk_reason}")

    st.markdown("#### Provider Diagnostics")
    provider_columns = st.columns(3)
    provider_columns[0].metric("Provider", case.llm_provider)
    provider_columns[1].metric("Model", case.model_name or "N/A")
    provider_columns[2].metric("Latency", format_latency(case.latency_ms))
    optional_provider = []
    if case.provider_fallback_used is not None:
        optional_provider.append(("Provider fallback used", str(case.provider_fallback_used), "warning" if case.provider_fallback_used else "success"))
    if case.generation_attempt_count is not None:
        optional_provider.append(("Generation attempts", str(case.generation_attempt_count), "neutral"))
    if case.generation_error_type:
        optional_provider.append(("Generation error", case.generation_error_type, "warning"))
    if optional_provider:
        render_badge_row(optional_provider)

    if case.error_type or case.error_message:
        st.markdown("#### Evaluation Error")
        st.error(f"{case.error_type or 'Request error'}: {case.error_message or 'No safe error detail recorded.'}")


def _render_case_explorer(cases: tuple[EvaluationCase, ...], all_cases: tuple[EvaluationCase, ...]) -> None:
    st.subheader("Case Detail Explorer")
    selectable = cases or all_cases
    if not selectable:
        st.info("No evaluation cases are available.")
        return
    case_ids = [case.id for case in selectable]
    selected_id = st.selectbox(
        "Evaluation case",
        case_ids,
        format_func=lambda case_id: next(
            f"{case_id} — {case.question}" for case in selectable if case.id == case_id
        ),
    )
    selected_case = next(case for case in selectable if case.id == selected_id)
    _render_case_detail(selected_case)


def _render_traceability(data: EvaluationDashboardData) -> None:
    st.subheader("Downloads and Traceability")
    download_columns = st.columns(2)
    download_columns[0].download_button(
        "Download current JSON",
        data=data.result_path.read_bytes(),
        file_name=data.result_path.name,
        mime="application/json",
        width="stretch",
    )
    if data.csv_path:
        download_columns[1].download_button(
            "Download current CSV",
            data=data.csv_path.read_bytes(),
            file_name=data.csv_path.name,
            mime="text/csv",
            width="stretch",
        )
    else:
        download_columns[1].button("CSV result not available", disabled=True, width="stretch")

    with st.expander("Run metadata", expanded=False):
        run = data.run
        rows = {
            "Dataset SHA-256": run.dataset_sha256 or "N/A",
            "Run ID": run.run_id,
            "Started": run.started_at_utc or "N/A",
            "Completed": run.completed_at_utc or "N/A",
            "Duration": format_latency(run.duration_ms),
            "Endpoint": run.endpoint or "N/A",
            "Top-k": run.top_k if run.top_k is not None else "N/A",
            "Timeout": f"{run.timeout_seconds:g} seconds" if run.timeout_seconds is not None else "N/A",
            "Request delay": f"{run.request_delay_seconds:g} seconds" if run.request_delay_seconds is not None else "N/A",
            "Result path": str(data.result_path),
        }
        st.dataframe(
            pd.DataFrame(
                [{"Field": key, "Value": str(value)} for key, value in rows.items()]
            ),
            hide_index=True,
            width="stretch",
        )
    st.caption("Generated evaluation outputs are ignored by Git and should be regenerated for each environment.")
    st.code("python eval/run_eval.py --request-delay-seconds 5", language="bash")


load_global_styles()

render_page_header(
    title="RAG Evaluation Dashboard",
    subtitle=(
        "Trace retrieval quality, answerability, confidence, fallback safety, and "
        "provider reliability across the verified PolicyGPT benchmark."
    ),
)

refresh_col, command_col = st.columns([1, 4])
with refresh_col:
    if st.button("Refresh results", type="primary", width="stretch"):
        _load_cached_results.clear()
        st.rerun()
with command_col:
    st.caption("Read-only dashboard · generate results separately with `python eval/run_eval.py --request-delay-seconds 5`")

dashboard_data, load_error, resolved_path = _load_dashboard_data()
if dashboard_data is None:
    if load_error and "No evaluation result file" in load_error.reason:
        render_badge_row([("Results", "No result file", "warning")])
        render_empty_results(str(resolved_path))
    else:
        render_badge_row([("Results", "Invalid result file", "danger")])
        render_invalid_results(str(resolved_path), load_error.reason if load_error else "Unknown validation error.")
    st.stop()

_render_run_header(dashboard_data)
_render_freshness_warnings(dashboard_data)
_render_kpis(dashboard_data)
st.divider()
_render_quality_gates(dashboard_data)
st.divider()
filtered_cases = _render_filters(dashboard_data)
_render_charts(filtered_cases)
st.divider()
_render_provider_reliability(dashboard_data)
_render_confidence_diagnostics(dashboard_data)
st.divider()
_render_review_table(filtered_cases)
_render_case_explorer(filtered_cases, dashboard_data.cases)
st.divider()
_render_traceability(dashboard_data)
