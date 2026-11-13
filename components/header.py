"""
NIRF Insight — Header Component
Provides reusable page-header rendering.
"""

import streamlit as st


def render_page_header(title: str, subtitle: str = ""):
    """Render a styled page header with title and optional subtitle."""
    st.markdown(
        f"""
        <div class="page-header">
            <div class="page-title">{title}</div>
            <div class="page-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, icon: str = ""):
    """Render a smaller section heading."""
    st.markdown(f"### {icon} {title}")
