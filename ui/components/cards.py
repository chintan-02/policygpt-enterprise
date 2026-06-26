from typing import Any

import streamlit as st


def render_page_header(
    title: str,
    subtitle: str,
    kicker: str = "PolicyGPT Enterprise",
) -> None:
    st.markdown(
        f"""
        <div class="pgpt-top-kicker">{kicker}</div>
        <div class="pgpt-title">{title}</div>
        <div class="pgpt-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


def render_backend_status_card(status: dict[str, Any]) -> None:
    healthy = bool(status.get("healthy"))
    message = status.get("message", "Unknown")
    latency_ms = status.get("latency_ms")

    if healthy:
        label = "Backend connected"
        detail = f"{message}"
        if latency_ms is not None:
            detail += f" · {latency_ms:.0f} ms"
        border_color = "#10B981"
    else:
        label = "Backend unavailable"
        detail = message
        border_color = "#EF4444"

    st.markdown(
        f"""
        <div class="pgpt-card" style="border-left: 4px solid {border_color};">
            <div class="pgpt-card-title">{label}</div>
            <div class="pgpt-muted">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_upload_summary(upload_data: dict[str, Any], latency_ms: float | None = None) -> None:
    filename = upload_data.get("filename", "Unknown file")
    page_count = upload_data.get("page_count", 0)
    chunk_count = upload_data.get("chunk_count", 0)
    stored_chunk_count = upload_data.get("stored_chunk_count", 0)
    collection_name = upload_data.get("collection_name", "Unknown collection")
    message = upload_data.get("message", "")

    latency_text = f" · {latency_ms:.0f} ms" if latency_ms is not None else ""

    st.markdown(
        f"""
        <div class="pgpt-card">
            <div class="pgpt-card-title">Document indexed</div>
            <div class="pgpt-muted">{filename}{latency_text}</div>
            <br/>
            <div class="pgpt-muted">
                Pages: <b>{page_count}</b> ·
                Chunks: <b>{chunk_count}</b> ·
                Stored: <b>{stored_chunk_count}</b> ·
                Collection: <b>{collection_name}</b>
            </div>
            <br/>
            <div class="pgpt-muted">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str, caption: str = "") -> None:
    st.markdown(
        f"""
        <div class="pgpt-card">
            <div class="pgpt-small-label">{label}</div>
            <div style="font-size:1.35rem;font-weight:800;color:#0F172A;">{value}</div>
            <div class="pgpt-muted">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )