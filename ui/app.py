from pathlib import Path
import sys

import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from ui.styles import load_global_styles  # noqa: E402


BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="PolicyGPT Enterprise",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_global_styles()

pages = [
    st.Page(
        str(BASE_DIR / "pages" / "ask.py"),
        title="Ask PolicyGPT",
    ),
    st.Page(
        str(BASE_DIR / "pages" / "evidence.py"),
        title="Evidence Explorer",
    ),
    st.Page(
        str(BASE_DIR / "pages" / "evaluation_dashboard.py"),
        title="RAG Evaluation",
    ),
    st.Page(
        str(BASE_DIR / "pages" / "architecture.py"),
        title="Architecture",
    ),
]

navigation = st.navigation(pages)
navigation.run()
