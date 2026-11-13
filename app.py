"""
NIRF Insight — Interactive Higher Education Analytics & Visualization Platform
==============================================================================
Main application entry point.
Run with:  streamlit run app.py
"""

import streamlit as st
import os

# ---------------------------------------------------------------------------
# Page Configuration (must be the first Streamlit command)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="NIRF Insight",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Load Custom CSS
# ---------------------------------------------------------------------------

_CSS_PATH = os.path.join(os.path.dirname(__file__), "assets", "styles.css")

if os.path.exists(_CSS_PATH):
    with open(_CSS_PATH, encoding="utf-8") as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar Branding
# ---------------------------------------------------------------------------

from components.sidebar import render_sidebar_branding, render_sidebar_footer  # noqa: E402

render_sidebar_branding()

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

pages = {
    "Dashboard": [
        st.Page("pages/overview.py", title="Overview", icon="📊", default=True),
        st.Page("pages/dataset_explorer.py", title="Dataset Explorer", icon="🔍"),
    ],
    "Analytics": [
        st.Page("pages/graph_builder.py", title="Dynamic Graph Builder", icon="📈"),
        st.Page("pages/question_explorer.py", title="Question Explorer", icon="❓"),
        st.Page("pages/geospatial.py", title="Geospatial Analysis", icon="🗺️"),
        st.Page("pages/advanced_analytics.py", title="Correlation & Analytics", icon="🔬"),
    ],
    "AI": [
        st.Page("pages/chatbot.py", title="AI Chatbot", icon="🤖"),
    ],
}

pg = st.navigation(pages)

# ---------------------------------------------------------------------------
# Sidebar Footer
# ---------------------------------------------------------------------------

render_sidebar_footer()

# ---------------------------------------------------------------------------
# Run Selected Page
# ---------------------------------------------------------------------------

pg.run()
