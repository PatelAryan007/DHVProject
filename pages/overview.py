"""
NIRF Insight — Overview Dashboard
Main landing page with KPIs, charts, and analytical highlights.
"""

import streamlit as st
import pandas as pd

from core.data_loader import load_data
from core.preprocessing import filter_data
from core.analytics import (
    get_top_institutions,
    get_category_distribution,
    get_state_distribution,
    get_yearly_trend,
    get_analytical_highlights,
)
from components.header import render_page_header, render_section_header
from components.kpi_cards import render_kpi_cards
from components.filters import render_filters
from components.charts import (
    create_bar_chart,
    create_line_chart,
    create_histogram,
    render_chart,
    COLORS,
)

# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

render_page_header(
    "NIRF Analytics Overview",
    "Explore institutional rankings, performance indicators, and higher education "
    "trends across India from 2017 to 2025.",
)

df = load_data()

if df is None:
    st.error(
        "⚠️ Dataset not found. Please place `nirf_2017_2025_clean.csv` "
        "in the `data/` folder and reload the page."
    )
    st.stop()

# ── Filters ────────────────────────────────────────────────────────────────
st.markdown("#### 🎛️ Filters")
year, category, state = render_filters(df, key_prefix="overview")

filtered = filter_data(df, year=year, category=category, state=state)

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()

# ── KPI Cards ──────────────────────────────────────────────────────────────
st.markdown("")  # spacer

total_institutions = filtered["Name"].nunique() if "Name" in filtered.columns else len(filtered)
total_categories = filtered["Category"].nunique() if "Category" in filtered.columns else 0
avg_score = filtered["Score"].mean() if "Score" in filtered.columns else None
n_states = filtered["State"].nunique() if "State" in filtered.columns else 0
display_year = str(year) if year != "All" else "All Years"

kpi_metrics = [
    {"label": "Institutions", "value": f"{total_institutions:,}", "icon": "🏫"},
    {"label": "Categories", "value": str(total_categories), "icon": "📁"},
    {
        "label": "Avg NIRF Score",
        "value": f"{avg_score:.2f}" if avg_score and pd.notna(avg_score) else "—",
        "icon": "📊",
    },
    {"label": "States", "value": str(n_states), "icon": "📍"},
    {"label": "Year", "value": display_year, "icon": "📅"},
]

render_kpi_cards(kpi_metrics)

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ── Charts Row 1 ───────────────────────────────────────────────────────────
render_section_header("Top Performers & Distribution", "📊")

col1, col2 = st.columns(2)

with col1:
    top10 = get_top_institutions(filtered, n=10, by="Score")
    if not top10.empty:
        top10_sorted = top10.sort_values("Score", ascending=True)
        fig = create_bar_chart(
            top10_sorted, x="Name", y="Score",
            title="Top 10 Institutions by NIRF Score",
            horizontal=True, color=COLORS["primary"],
        )
        render_chart(fig, key="overview_top10")

with col2:
    cat_dist = get_category_distribution(filtered)
    if not cat_dist.empty:
        fig = create_bar_chart(
            cat_dist, x="Category", y="Count",
            title="Institution Distribution by Category",
            color=COLORS["secondary"],
        )
        render_chart(fig, key="overview_cat_dist")

# ── Charts Row 2 ───────────────────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    state_dist = get_state_distribution(filtered)
    if not state_dist.empty:
        top_states = state_dist.head(15).sort_values("Count", ascending=True)
        fig = create_bar_chart(
            top_states, x="State", y="Count",
            title="Top 15 States by Institution Count",
            horizontal=True, color=COLORS["accent"],
        )
        render_chart(fig, key="overview_state_dist")

with col4:
    if year == "All" and "Year" in filtered.columns:
        trend = get_yearly_trend(filtered, metric="Score", agg="mean")
        if not trend.empty:
            fig = create_line_chart(
                trend, x="Year", y="Score",
                title="Average NIRF Score by Year",
            )
            render_chart(fig, key="overview_yearly")
    else:
        if "Score" in filtered.columns:
            fig = create_histogram(
                filtered, x="Score",
                title="Distribution of NIRF Scores",
                nbins=25,
            )
            render_chart(fig, key="overview_hist_alt")

# ── Score Histogram (always shown when all years) ──────────────────────────
if year == "All" and "Score" in filtered.columns:
    fig = create_histogram(
        filtered, x="Score",
        title="Distribution of NIRF Scores",
        nbins=30,
    )
    render_chart(fig, key="overview_score_hist")

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ── Top-Performing Institutions Table ──────────────────────────────────────
render_section_header("Top-Performing Institutions", "🏆")

display_cols = ["Name", "Category", "State", "Score", "Rank", "Year"]
available_cols = [c for c in display_cols if c in filtered.columns]

top_table = get_top_institutions(filtered, n=15, by="Score")
if not top_table.empty and available_cols:
    st.dataframe(
        top_table[available_cols].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ── Analytical Highlights ──────────────────────────────────────────────────
render_section_header("Analytical Highlights", "💡")

highlights = get_analytical_highlights(filtered)
if highlights:
    cols = st.columns(2)
    for i, h in enumerate(highlights):
        with cols[i % 2]:
            st.markdown(
                f'<div class="highlight-box">{h}</div>',
                unsafe_allow_html=True,
            )
else:
    st.info("No highlights available for the current filter selection.")

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ── Dataset Information ────────────────────────────────────────────────────
render_section_header("Dataset Information", "ℹ️")

info_col1, info_col2, info_col3 = st.columns(3)

with info_col1:
    st.markdown(
        f"""
        <div class="section-card">
            <div style="font-weight:600; margin-bottom:0.5rem;">📄 Data Scope</div>
            <div class="stat-row"><span class="stat-label">Total Records</span>
                <span class="stat-value">{len(df):,}</span></div>
            <div class="stat-row"><span class="stat-label">Filtered Records</span>
                <span class="stat-value">{len(filtered):,}</span></div>
            <div class="stat-row"><span class="stat-label">Columns</span>
                <span class="stat-value">{len(df.columns)}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with info_col2:
    years_list = sorted([int(y) for y in df["Year"].dropna().unique()])
    yr_range = f"{years_list[0]}–{years_list[-1]}" if years_list else "—"
    st.markdown(
        f"""
        <div class="section-card">
            <div style="font-weight:600; margin-bottom:0.5rem;">📅 Temporal Coverage</div>
            <div class="stat-row"><span class="stat-label">Year Range</span>
                <span class="stat-value">{yr_range}</span></div>
            <div class="stat-row"><span class="stat-label">Years Available</span>
                <span class="stat-value">{len(years_list)}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with info_col3:
    cats = df["Category"].nunique() if "Category" in df.columns else 0
    states = df["State"].nunique() if "State" in df.columns else 0
    st.markdown(
        f"""
        <div class="section-card">
            <div style="font-weight:600; margin-bottom:0.5rem;">🏛️ Dimensions</div>
            <div class="stat-row"><span class="stat-label">Categories</span>
                <span class="stat-value">{cats}</span></div>
            <div class="stat-row"><span class="stat-label">States / UTs</span>
                <span class="stat-value">{states}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
