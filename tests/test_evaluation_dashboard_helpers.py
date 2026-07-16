from ui.components.evaluation_components import (
    confidence_status,
    diagnostic_label,
    format_items,
    gate_label,
    gate_variant,
)
from ui.services.evaluation_results_service import (
    DiagnosticCategory,
    QualityGateStatus,
    format_latency,
    format_percentage,
    format_score,
)


def test_display_formatters_handle_values_and_missing_data() -> None:
    assert format_percentage(0.875) == "87.5%"
    assert format_score(0.81234) == "0.81"
    assert format_score(None) == "N/A"
    assert format_latency(800) == "800 ms"
    assert format_latency(1250) == "1.25 s"
    assert format_latency(None) == "N/A"
    assert format_items([5, 9]) == "5, 9"
    assert format_items([]) == "None"


def test_confidence_status_thresholds() -> None:
    assert confidence_status(None) == "Unavailable"
    assert confidence_status(0.1) == "Insufficient"
    assert confidence_status(0.3) == "Weak"
    assert confidence_status(0.6) == "Moderate"
    assert confidence_status(0.8) == "Strong"


def test_diagnostic_labels_are_human_readable() -> None:
    assert diagnostic_label(DiagnosticCategory.PROVIDER_GENERATION_FAILURE) == "Provider generation failure"
    assert diagnostic_label("future_category") == "Future Category"


def test_quality_gate_display_mapping() -> None:
    assert gate_label(QualityGateStatus.PASSED) == "Passed"
    assert gate_variant(QualityGateStatus.PASSED) == "success"
    assert gate_label(QualityGateStatus.NEEDS_ATTENTION) == "Needs attention"
    assert gate_variant(QualityGateStatus.NEEDS_ATTENTION) == "warning"
    assert gate_label(QualityGateStatus.NOT_APPLICABLE) == "Not applicable"
    assert gate_variant(QualityGateStatus.NOT_APPLICABLE) == "neutral"
