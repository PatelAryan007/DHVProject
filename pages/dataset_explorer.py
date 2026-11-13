"""
NIRF Insight — Dataset Explorer
===============================
Interactive dataset browser, multi-dimensional filtering, statistical profiling,
and comprehensive Data Quality & Preprocessing Audit Report.
"""

import json
import streamlit as st
import pandas as pd

from core.data_loader import load_data, get_data_quality_audit, get_data_summary
from core.preprocessing import filter_data, get_missing_value_stats
from components.header import render_page_header, render_section_header
from components.kpi_cards import render_kpi_cards
from components.filters import render_filters, render_institution_search

# ---------------------------------------------------------------------------
# Page Header
# ---------------------------------------------------------------------------

render_page_header(
    "Dataset Explorer",
    "Explore, search, filter, and audit the standardized NIRF (2017–2025) dataset. "
    "Inspect data quality diagnostics and download verified analytical records.",
)

df = load_data()

if df is None:
    st.error(
        "⚠️ Dataset not found. Please ensure `nirf_2017_2025_clean.csv` or `nirf_2017_2025_raw.csv` "
        "is placed in the `data/` folder and reload."
    )
    st.stop()

# ── Summary KPIs ────────────────────────────────---------------------------
summary = get_data_summary(df)
audit_rep = get_data_quality_audit(df)

health_score = audit_rep.get("quality_score", 100)

render_kpi_cards([
    {"label": "Total Records", "value": f"{summary.get('total_rows', 0):,}", "icon": "📄"},
    {"label": "Columns", "value": str(summary.get("total_columns", 0)), "icon": "📐"},
    {"label": "Institutions", "value": f"{summary.get('n_institutions', 0):,}", "icon": "🏫"},
    {"label": "Categories", "value": str(len(summary.get("categories", []))), "icon": "📁"},
    {"label": "Quality Score", "value": f"{health_score}/100", "icon": "🛡️"},
])

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ── Primary Exploration & Data Quality Tabs ────────────────────────────────
main_tab1, main_tab2 = st.tabs(["📋 Interactive Data Explorer", "🛡️ Data Quality & Audit Report"])

# ===========================================================================
# TAB 1: INTERACTIVE DATA EXPLORER
# ===========================================================================
with main_tab1:
    render_section_header("Cohort Filters", "🎛️")

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    with c1:
        years = ["All"] + [str(int(y)) for y in sorted(df["Year"].dropna().unique())]
        sel_year = st.selectbox("📅 Year", years, key="exp_year")
    with c2:
        cats = ["All"] + sorted(df["Category"].dropna().unique().tolist())
        sel_cat = st.selectbox("📁 Category", cats, key="exp_cat")
    with c3:
        states = ["All"] + sorted(df["State"].dropna().unique().tolist())
        sel_state = st.selectbox("📍 State", states, key="exp_state")
    with c4:
        avail_opts = ["All"] + sorted(df["Data_Availability"].dropna().unique().tolist()) if "Data_Availability" in df.columns else ["All"]
        sel_avail = st.selectbox("📊 Availability", avail_opts, key="exp_avail")

    search_term = render_institution_search(key_prefix="explorer")

    year_val = "All" if sel_year == "All" else int(sel_year)
    filtered = filter_data(
        df,
        year=year_val,
        category=sel_cat,
        state=sel_state,
        name_search=search_term,
        data_availability=sel_avail,
    )

    st.markdown(
        f"""
        <div class="highlight-box">
            Displaying <strong>{len(filtered):,}</strong> of <strong>{len(df):,}</strong> records
            &nbsp;·&nbsp; <strong>{filtered['Name'].nunique() if 'Name' in filtered.columns else 0}</strong> unique institutions
            &nbsp;·&nbsp; <strong>{filtered['Category'].nunique() if 'Category' in filtered.columns else 0}</strong> categories
        </div>
        """,
        unsafe_allow_html=True,
    )

    if filtered.empty:
        st.warning("No records match the current filter criteria.")
    else:
        # Display Table
        st.dataframe(
            filtered.reset_index(drop=True),
            use_container_width=True,
            height=460,
            hide_index=True,
        )

        # Download Buttons
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            csv_filtered = filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Filtered Records (CSV)",
                data=csv_filtered,
                file_name="nirf_filtered_records.csv",
                mime="text/csv",
                key="dl_filtered_csv",
            )
        with col_d2:
            csv_full = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📦 Download Complete Preprocessed Dataset (CSV)",
                data=csv_full,
                file_name="nirf_2017_2025_preprocessed.csv",
                mime="text/csv",
                key="dl_full_clean_csv",
            )

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    # Statistical Profiles of Filtered Data
    render_section_header("Column Profiles & Types", "📐")
    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🔢 Numerical Summary", "❓ Missingness Stats", "🔤 Data Types"])

    with sub_tab1:
        numeric_cols = filtered.select_dtypes(include="number")
        if not numeric_cols.empty:
            st.dataframe(numeric_cols.describe().round(2).T, use_container_width=True)
        else:
            st.info("No numerical fields available in filtered slice.")

    with sub_tab2:
        miss_stats = get_missing_value_stats(filtered)
        if not miss_stats.empty:
            st.dataframe(miss_stats, use_container_width=True, hide_index=True)

    with sub_tab3:
        dtypes_df = pd.DataFrame({
            "Column": filtered.columns,
            "Clean Data Type": filtered.dtypes.astype(str).values,
            "Valid Count": filtered.notna().sum().values,
            "Sample Record": [
                str(filtered[c].dropna().iloc[0]) if filtered[c].notna().any() else "—"
                for c in filtered.columns
            ],
        })
        st.dataframe(dtypes_df, use_container_width=True, hide_index=True)


# ===========================================================================
# TAB 2: DATA QUALITY & AUDIT REPORT
# ===========================================================================
with main_tab2:
    render_section_header("Data Quality Executive Summary", "🛡️")

    q_col1, q_col2, q_col3, q_col4 = st.columns(4)
    with q_col1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-icon">✅</div>
                <div class="kpi-value">{audit_rep.get('quality_score', 100)}%</div>
                <div class="kpi-label">Health Score</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with q_col2:
        exact_dup = audit_rep.get("duplicates", {}).get("exact_duplicates", 0)
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-icon">🔍</div>
                <div class="kpi-value">{exact_dup}</div>
                <div class="kpi-label">Exact Duplicates</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with q_col3:
        id_col = audit_rep.get("duplicates", {}).get("id_collisions", 0)
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-icon">🔑</div>
                <div class="kpi-value">{id_col}</div>
                <div class="kpi-label">Key Collisions</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with q_col4:
        expected_no_score = audit_rep.get("missingness", {}).get("expected_no_score_categories", 0)
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-icon">📋</div>
                <div class="kpi-value">{expected_no_score}</div>
                <div class="kpi-label">Rank-Only Records</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    # Preprocessing Actions Applied
    render_section_header("Audited Preprocessing Actions", "⚙️")

    audit_cards_col1, audit_cards_col2 = st.columns(2)
    with audit_cards_col1:
        st.markdown(
            """
            <div class="section-card">
                <div style="font-weight:700; color:#1F2D24; margin-bottom:0.6rem;">🔧 Standardization & Transformations</div>
                <div class="stat-row"><span class="stat-label">Source Dataset Preserved</span><span class="stat-value">✅ data/nirf_2017_2025_raw.csv</span></div>
                <div class="stat-row"><span class="stat-label">State Normalization</span><span class="stat-value">✅ Fixed casing (Jammu and Kashmir)</span></div>
                <div class="stat-row"><span class="stat-label">Category Standardization</span><span class="stat-value">✅ Fixed labels (State Public / Open / Skill)</span></div>
                <div class="stat-row"><span class="stat-label">Tied Ranks Handling</span><span class="stat-value">✅ Parsed (e.g. 21A -> 21, Is_Tied=True)</span></div>
                <div class="stat-row"><span class="stat-label">Withdrawn Ranks & Scores</span><span class="stat-value">✅ Converted to NaN, flagged Is_Withdrawn</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with audit_cards_col2:
        st.markdown(
            """
            <div class="section-card">
                <div style="font-weight:700; color:#1F2D24; margin-bottom:0.6rem;">🔬 Missingness Classification</div>
                <div class="stat-row"><span class="stat-label">Total Missing Scores</span><span class="stat-value">43 records (0.6%)</span></div>
                <div class="stat-row"><span class="stat-label">Innovation (2024–2025)</span><span class="stat-value">20 records (NIRF publishes Rank only)</span></div>
                <div class="stat-row"><span class="stat-label">SDG Institutions (2025)</span><span class="stat-value">10 records (NIRF publishes Rank only)</span></div>
                <div class="stat-row"><span class="stat-label">Open / Skill Universities</span><span class="stat-value">12 records (NIRF publishes Rank only)</span></div>
                <div class="stat-row"><span class="stat-label">Rank Withdrawn Records</span><span class="stat-value">1 Dental (2025) + 1 College (2018)</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    # Data Availability Distribution
    if "Data_Availability" in df.columns:
        render_section_header("Data Availability Breakdown", "📊")
        avail_counts = df["Data_Availability"].value_counts().reset_index()
        avail_counts.columns = ["Data Availability Tier", "Record Count"]
        avail_counts["Percentage"] = (avail_counts["Record Count"] / len(df) * 100).round(2)
        st.dataframe(avail_counts, use_container_width=True, hide_index=True)

    # Export Quality Audit Report as JSON
    json_rep = json.dumps(audit_rep, indent=2, default=str).encode("utf-8")
    st.download_button(
        label="⬇️ Download Full Data Quality Audit Report (JSON)",
        data=json_rep,
        file_name="nirf_data_quality_report.json",
        mime="application/json",
        key="dl_audit_json",
    )
