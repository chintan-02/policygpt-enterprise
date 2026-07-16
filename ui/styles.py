import streamlit as st


def load_global_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --pgpt-navy: #0F172A;
            --pgpt-teal: #0F766E;
            --pgpt-teal-soft: #CCFBF1;
            --pgpt-slate: #475569;
            --pgpt-border: #E2E8F0;
            --pgpt-bg: #F8FAFC;
            --pgpt-card: #FFFFFF;
            --pgpt-green: #047857;
            --pgpt-amber: #B45309;
            --pgpt-red: #B91C1C;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1240px;
        }

        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }

        .pgpt-top-kicker {
            color: var(--pgpt-teal);
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-size: 0.78rem;
            margin-bottom: 0.25rem;
        }

        .pgpt-title {
            font-size: 2.15rem;
            line-height: 1.15;
            font-weight: 800;
            color: #0F172A;
            margin-bottom: 0.45rem;
        }

        .pgpt-subtitle {
            color: var(--pgpt-slate);
            font-size: 1rem;
            max-width: 860px;
            margin-bottom: 1.2rem;
        }

        .pgpt-card {
            background: var(--pgpt-card);
            border: 1px solid var(--pgpt-border);
            border-radius: 16px;
            padding: 1.05rem 1.1rem;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
            margin-bottom: 1rem;
        }

        .pgpt-card-title {
            font-weight: 750;
            color: #0F172A;
            font-size: 1rem;
            margin-bottom: 0.35rem;
        }

        .pgpt-muted {
            color: var(--pgpt-slate);
            font-size: 0.9rem;
        }

        .pgpt-answer {
            color: #111827;
            font-size: 1.02rem;
            line-height: 1.65;
            margin-top: 0.65rem;
        }

        .pgpt-badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin: 0.75rem 0 0.25rem 0;
        }

        .pgpt-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            border-radius: 999px;
            padding: 0.32rem 0.65rem;
            font-size: 0.78rem;
            font-weight: 700;
            border: 1px solid transparent;
            white-space: nowrap;
        }

        .pgpt-badge-success {
            color: #065F46;
            background: #D1FAE5;
            border-color: #A7F3D0;
        }

        .pgpt-badge-info {
            color: #075985;
            background: #E0F2FE;
            border-color: #BAE6FD;
        }

        .pgpt-badge-warning {
            color: #92400E;
            background: #FEF3C7;
            border-color: #FDE68A;
        }

        .pgpt-badge-danger {
            color: #991B1B;
            background: #FEE2E2;
            border-color: #FECACA;
        }

        .pgpt-badge-neutral {
            color: #334155;
            background: #F1F5F9;
            border-color: #E2E8F0;
        }

        .pgpt-citation {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-left: 4px solid #0F766E;
            border-radius: 14px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.85rem;
        }

        .pgpt-citation-title {
            font-weight: 750;
            color: #0F172A;
            margin-bottom: 0.25rem;
        }

        .pgpt-citation-meta {
            color: #475569;
            font-size: 0.82rem;
            margin-bottom: 0.55rem;
        }

        .pgpt-citation-excerpt {
            color: #1F2937;
            font-size: 0.9rem;
            line-height: 1.55;
        }

        .pgpt-fallback {
            background: #FFF7ED;
            border: 1px solid #FED7AA;
            border-left: 4px solid #F97316;
            border-radius: 16px;
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
        }

        .pgpt-small-label {
            color: #64748B;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 0.25rem;
        }

        .pgpt-flow {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 16px;
            padding: 1rem;
            margin-bottom: 0.75rem;
        }

        .pgpt-flow-step {
            padding: 0.65rem 0.75rem;
            border-radius: 12px;
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            margin-bottom: 0.5rem;
            color: #0F172A;
            font-weight: 650;
        }

        .pgpt-eval-metric {
            min-height: 152px;
            background: var(--pgpt-card);
            border: 1px solid var(--pgpt-border);
            border-top: 3px solid #CBD5E1;
            border-radius: 14px;
            padding: 0.95rem 1rem;
            box-shadow: 0 7px 20px rgba(15, 23, 42, 0.035);
            margin-bottom: 0.8rem;
        }

        .pgpt-eval-metric-success { border-top-color: #10B981; }
        .pgpt-eval-metric-danger { border-top-color: #EF4444; }

        .pgpt-eval-metric-value {
            color: var(--pgpt-navy);
            font-size: 1.42rem;
            font-weight: 800;
            margin-top: 0.25rem;
        }

        .pgpt-eval-metric-secondary {
            color: var(--pgpt-teal);
            font-size: 0.95rem;
            font-weight: 750;
            margin-top: 0.1rem;
        }

        .pgpt-eval-metric-caption {
            color: #64748B;
            font-size: 0.78rem;
            line-height: 1.35;
            margin-top: 0.35rem;
        }

        .pgpt-eval-gate {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.85rem 0;
            border-bottom: 1px solid var(--pgpt-border);
        }

        .pgpt-eval-gate:last-child { border-bottom: 0; }

        .pgpt-eval-gate-title {
            color: var(--pgpt-navy);
            font-weight: 750;
        }

        .pgpt-eval-gate-result {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 0.55rem;
            min-width: 210px;
        }

        .pgpt-eval-gate-value {
            color: var(--pgpt-slate);
            font-size: 0.85rem;
            font-weight: 700;
        }

        .pgpt-eval-provider-warning,
        .pgpt-eval-answer-provider {
            background: #FFFBEB;
            border: 1px solid #FDE68A;
            border-left: 4px solid #D97706;
            border-radius: 14px;
            padding: 1rem 1.1rem;
            margin: 0.8rem 0 1rem;
        }

        .pgpt-eval-empty,
        .pgpt-eval-invalid {
            background: #FFFFFF;
            border: 1px dashed #CBD5E1;
            border-radius: 16px;
            padding: 1.35rem;
            margin: 1rem 0;
        }

        .pgpt-eval-invalid { border-left: 4px solid #B91C1C; }

        .pgpt-eval-path {
            color: #64748B;
            font-family: monospace;
            font-size: 0.78rem;
            margin-top: 0.6rem;
            overflow-wrap: anywhere;
        }

        .pgpt-eval-answer {
            background: #FFFFFF;
            border: 1px solid var(--pgpt-border);
            border-left: 4px solid var(--pgpt-teal);
            border-radius: 14px;
            padding: 1rem 1.1rem;
            margin: 0.8rem 0 1rem;
        }

        .pgpt-eval-answer-unsupported {
            background: #F8FAFC;
            border-left-color: #64748B;
        }

        .pgpt-eval-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 0.38rem;
            margin: 0.3rem 0 0.9rem;
        }

        @media (max-width: 760px) {
            .pgpt-eval-gate { align-items: flex-start; flex-direction: column; }
            .pgpt-eval-gate-result { justify-content: flex-start; min-width: 0; }
            .pgpt-eval-metric { min-height: 0; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
