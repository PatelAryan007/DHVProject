"""
NIRF Insight — Geospatial Analysis
State-wise and regional analysis of NIRF data with map placeholder.
"""

import streamlit as st
import pandas as pd

from core.data_loader import load_data
from core.preprocessing import filter_data
from core.analytics import get_state_distribution, get_state_summary
from components.header import render_page_header, render_section_header
from components.kpi_cards import render_kpi_cards
from components.filters import render_filters
from components.charts import (
    create_bar_chart,
    create_scatter_chart,
    render_chart,
    COLORS,
)

# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

render_page_header(
    "Geospatial Analysis",
    "Explore geographical patterns, state-wise distributions, and regional "
    "performance in NIRF rankings.",
)

df = load_data()
if df is None:
    st.error("⚠️ Dataset not found. Place `nirf_2017_2025_clean.csv` in `data/`.")
    st.stop()

# ── Filters ────────────────────────────────────────────────────────────────
render_section_header("Filters", "🎛️")
year, category, state = render_filters(df, key_prefix="geo")

filtered = filter_data(df, year=year, category=category, state=state)

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()

# ── KPIs ───────────────────────────────────────────────────────────────────
n_states = filtered["State"].nunique() if "State" in filtered.columns else 0
n_cities = filtered["City"].nunique() if "City" in filtered.columns else 0
top_state = (
    filtered["State"].value_counts().index[0]
    if "State" in filtered.columns and not filtered["State"].value_counts().empty
    else "—"
)

render_kpi_cards([
    {"label": "States / UTs", "value": str(n_states), "icon": "📍"},
    {"label": "Cities", "value": str(n_cities), "icon": "🏙️"},
    {"label": "Most Institutions", "value": top_state, "icon": "🏆"},
    {"label": "Records", "value": f"{len(filtered):,}", "icon": "📄"},
])

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ── State-wise Institution Distribution ────────────────────────────────────
render_section_header("State-wise Institution Distribution", "📊")

state_dist = get_state_distribution(filtered)
if not state_dist.empty:
    top_states_df = state_dist.head(20).sort_values("Count", ascending=True)
    fig = create_bar_chart(
        top_states_df, x="State", y="Count",
        title="Top 20 States by Number of Institutions",
        horizontal=True, color=COLORS["primary"],
    )
    render_chart(fig, key="geo_state_count")

# ── State-wise Average Score ───────────────────────────────────────────────
render_section_header("State-wise Average Score", "📈")

if "Score" in filtered.columns and "State" in filtered.columns:
    avg_score = (
        filtered.groupby("State")["Score"].mean()
        .reset_index()
        .sort_values("Score", ascending=True)
        .round(2)
        .tail(20)
    )
    avg_score.columns = ["State", "Avg Score"]
    fig = create_bar_chart(
        avg_score, x="State", y="Avg Score",
        title="Top 20 States by Average NIRF Score",
        horizontal=True, color=COLORS["accent"],
    )
    render_chart(fig, key="geo_avg_score")

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ── India Map Placeholder ──────────────────────────────────────────────────
render_section_header("India Choropleth Map", "🗺️")

st.markdown(
    """
    <div class="placeholder-box">
        <div class="placeholder-icon">🗺️</div>
        <div class="placeholder-title">Interactive India Map — Coming Soon</div>
        <div class="placeholder-text">
            A state-level choropleth map will be integrated in a later phase
            using verified GeoJSON boundaries. The chart-based views above
            provide equivalent analytical insights.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ── Detailed State Summary Table ───────────────────────────────────────────
render_section_header("State Summary", "📋")

summary = get_state_summary(filtered)
if not summary.empty:
    st.dataframe(summary.reset_index(drop=True), use_container_width=True, hide_index=True)
else:
    st.info("No state-level summary available.")

# ── City Insights ──────────────────────────────────────────────────────────
render_section_header("Top Cities", "🏙️")

if "City" in filtered.columns:
    city_counts = (
        filtered["City"].value_counts()
        .reset_index()
        .head(15)
    )
    city_counts.columns = ["City", "Count"]
    city_counts_sorted = city_counts.sort_values("Count", ascending=True)
    fig = create_bar_chart(
        city_counts_sorted, x="City", y="Count",
        title="Top 15 Cities by Institution Count",
        horizontal=True, color=COLORS["secondary"],
    )
    render_chart(fig, key="geo_city_count")
