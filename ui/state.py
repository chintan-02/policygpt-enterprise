import streamlit as st


DEMO_QUESTIONS = [
    "What is the remote work equipment allowance?",
    "Can employees paste confidential data into public AI tools?",
    "How many days in advance should employees request planned vacation?",
    "What should employees do if they see harassment or retaliation?",
    "What does the policy say about expense receipts?",
    "What is the CEO home address?",
]


def initialize_session_state() -> None:
    defaults = {
        "question_text": DEMO_QUESTIONS[0],
        "evidence_query": DEMO_QUESTIONS[0],
        "last_answer": None,
        "last_answer_latency_ms": None,
        "last_evidence": None,
        "last_evidence_latency_ms": None,
        "last_upload": None,
        "last_upload_latency_ms": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value