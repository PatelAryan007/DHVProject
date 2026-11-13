"""
NIRF Insight — Correlation & Advanced Analytics
Scatter plots, correlation matrices, and advanced statistical views.
"""

import streamlit as st
import pandas as pd

from core.data_loader import load_data, NUMERIC_COLS
from core.preprocessing import filter_data
from core.analytics import calculate_correlation, get_correlation_matrix
from components.header import render_page_header, render_section_header
from components.filters import render_filters
from components.charts import (
    create_scatter_chart,
    create_heatmap,
    render_chart,
    COLORS,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ANALYSIS_VARS = ["Score", "TLR", "RPC", "GO", "OI", "Perception"]

# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

render_page_header(
    "Correlation & Advanced Analytics",
    "Explore relationships between NIRF parameters with scatter plots, "
    "correlation coefficients, and matrix views.",
)

df = load_data()
if df is None:
    st.error("⚠️ Dataset not found. Place `nirf_2017_2025_clean.csv` in `data/`.")
    st.stop()

# ── Filters ────────────────────────────────────────────────────────────────
render_section_header("Filters", "🎛️")
year, category, state = render_filters(df, key_prefix="adv")

filtered = filter_data(df, year=year, category=category, state=state)

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()

available_vars = [v for v in ANALYSIS_VARS if v in filtered.columns]

if len(available_vars) < 2:
    st.warning("Not enough numeric variables available for correlation analysis.")
    st.stop()

# ── Variable Selection ─────────────────────────────────────────────────────
render_section_header("Bivariate Correlation", "🔗")

v_col1, v_col2, v_col3 = st.columns([1, 1, 1])

with v_col1:
    var1 = st.selectbox("Variable 1", available_vars, index=0, key="adv_var1")

with v_col2:
    default2 = min(1, len(available_vars) - 1)
    var2 = st.selectbox("Variable 2", available_vars, index=default2, key="adv_var2")

with v_col3:
    show_trendline = st.checkbox("Show trend line", value=True, key="adv_trend")

if var1 == var2:
    st.info("Please select two different variables.")
else:
    # Scatter plot
    fig = create_scatter_chart(
        filtered, x=var1, y=var2,
        title=f"{var1} vs {var2}",
        hover_name="Name" if "Name" in filtered.columns else None,
        trendline="ols" if show_trendline else None,
    )
    render_chart(fig, key="adv_scatter")

    # Correlation coefficient
    res = calculate_correlation(filtered, var1, var2)
    corr = res[0]
    n = res[1]
    desc = res[2] if len(res) > 2 else ""

    if corr is not None:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon">📐</div>
                    <div class="kpi-value">{corr}</div>
                    <div class="kpi-label">Pearson r</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon">📊</div>
                    <div class="kpi-value">{desc or 'Correlation'}</div>
                    <div class="kpi-label">Strength & Direction</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon">📄</div>
                    <div class="kpi-value">{n:,}</div>
                    <div class="kpi-label">Valid Observations</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("Unable to compute correlation — insufficient data.")

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ── Correlation Matrix ─────────────────────────────────────────────────────
render_section_header("Correlation Matrix", "🔬")

selected_matrix_vars = st.multiselect(
    "Select variables for the matrix",
    available_vars,
    default=available_vars,
    key="adv_matrix_vars",
)

if len(selected_matrix_vars) >= 2:
    corr_matrix = get_correlation_matrix(filtered, selected_matrix_vars)
    if not corr_matrix.empty:
        fig = create_heatmap(corr_matrix, title="Parameter Correlation Matrix")
        render_chart(fig, key="adv_heatmap")

        with st.expander("View correlation values", expanded=False):
            st.dataframe(corr_matrix, use_container_width=True)
    else:
        st.info("Could not compute correlation matrix with the available data.")
else:
    st.info("Select at least 2 variables to generate the correlation matrix.")

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ── Future Sections ────────────────────────────────────────────────────────
render_section_header("Multivariate Analysis", "🔬")

st.markdown(
    """
    <div class="placeholder-box">
        <div class="placeholder-icon">📊</div>
        <div class="placeholder-title">Multivariate Analysis — Coming Soon</div>
        <div class="placeholder-text">
            PCA, clustering, and multi-parameter comparisons will be
            integrated in Phase 2.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

render_section_header("Outlier Detection & Anomalies", "🎯")

outlier_col1, outlier_col2 = st.columns([1, 1])
with outlier_col1:
    target_var = st.selectbox("Select variable for outlier analysis", available_vars, index=0, key="adv_outlier_var")
with outlier_col2:
    method = st.radio("Detection Method", ["1.5 × IQR Rule", "Z-Score (|Z| ≥ 3.0)"], horizontal=True, key="adv_outlier_method")

from core.analytics import detect_outliers_iqr, detect_outliers_zscore
from components.charts import create_box_plot

if "IQR" in method:
    outliers_df, diag = detect_outliers_iqr(filtered, column=target_var, factor=1.5)
else:
    outliers_df, diag = detect_outliers_zscore(filtered, column=target_var, threshold=3.0)

if diag and not diag.get("error"):
    o1, o2, o3 = st.columns(3)
    with o1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-icon">🎯</div>
                <div class="kpi-value">{diag.get('outlier_count', 0)}</div>
                <div class="kpi-label">Outliers Detected</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with o2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-icon">📊</div>
                <div class="kpi-value">{diag.get('outlier_percentage', 0)}%</div>
                <div class="kpi-label">Outlier Percentage</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with o3:
        bound_text = f"[{diag.get('lower_bound', 0)}, {diag.get('upper_bound', 0)}]" if "IQR" in method else f"|Z| ≥ {diag.get('threshold', 3)}"
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-icon">📐</div>
                <div class="kpi-value">{bound_text}</div>
                <div class="kpi-label">Normal Bounds</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Box Plot
    fig_box = create_box_plot(filtered, x="Category" if "Category" in filtered.columns else None, y=target_var, title=f"{target_var} Distribution & Outlier Points")
    render_chart(fig_box, key="adv_outlier_chart")

    if not outliers_df.empty:
        with st.expander(f"View Outlier Records ({len(outliers_df)} institutions)", expanded=False):
            disp_cols = ["Name", "Category", "Year", "State", target_var, "Rank"]
            present_disp = [c for c in disp_cols if c in outliers_df.columns]
            st.dataframe(outliers_df[present_disp].reset_index(drop=True), use_container_width=True, hide_index=True)
else:
    st.info("Insufficient records or variability to run outlier detection.")
