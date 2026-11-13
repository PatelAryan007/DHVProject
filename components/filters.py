"""
NIRF Insight — Filter Components
Reusable filter widgets for year, category, state, and institution search.
"""

import streamlit as st
from core.preprocessing import (
    get_available_years,
    get_available_categories,
    get_available_states,
)


def render_year_filter(df, key_prefix: str = "default"):
    """Year selectbox; returns ``'All'`` or an integer year."""
    years = get_available_years(df)
    options = ["All"] + [str(int(y)) for y in years]
    selected = st.selectbox("📅 Year", options, key=f"{key_prefix}_year")
    return "All" if selected == "All" else int(selected)


def render_category_filter(df, key_prefix: str = "default"):
    """Category selectbox."""
    cats = get_available_categories(df)
    return st.selectbox("📁 Category", ["All"] + cats, key=f"{key_prefix}_cat")


def render_state_filter(df, key_prefix: str = "default"):
    """State selectbox."""
    states = get_available_states(df)
    return st.selectbox("📍 State", ["All"] + states, key=f"{key_prefix}_state")


def render_filters(
    df,
    key_prefix: str = "default",
    show_year: bool = True,
    show_category: bool = True,
    show_state: bool = True,
) -> tuple:
    """Render a row of filters and return *(year, category, state)*."""
    active = []
    if show_year:
        active.append("year")
    if show_category:
        active.append("category")
    if show_state:
        active.append("state")

    if not active:
        return "All", "All", "All"

    cols = st.columns(len(active))
    year = category = state = "All"
    idx = 0

    if show_year:
        with cols[idx]:
            year = render_year_filter(df, key_prefix)
        idx += 1
    if show_category:
        with cols[idx]:
            category = render_category_filter(df, key_prefix)
        idx += 1
    if show_state:
        with cols[idx]:
            state = render_state_filter(df, key_prefix)

    return year, category, state


def render_institution_search(key_prefix: str = "default") -> str:
    """Text input for searching institutions by name."""
    return st.text_input(
        "🔍 Search Institution",
        placeholder="Type institution name…",
        key=f"{key_prefix}_search",
    )
