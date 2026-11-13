"""
NIRF Insight — Question Explorer
================================
Interactive exploration of all 40 predefined NIRF analytical questions across 8 domains.
Provides dynamic context-sensitive filter controls, instant computation, publication-quality
visualizations, detailed grounded insights, and complete CSV export capabilities.
"""

import streamlit as st
import pandas as pd

from core.data_loader import load_data
from components.header import render_page_header, render_section_header
from components.charts import render_chart
from questions.question_config import (
    QUESTION_DOMAINS,
    get_domain_names,
    get_domain_icon,
    get_all_questions,
)
from questions.question_engine import execute_question

# ---------------------------------------------------------------------------
# Page Header
# ---------------------------------------------------------------------------

render_page_header(
    "Question Explorer",
    "Explore analytical answers, visualizations, and statistical tables for all 40 "
    "predefined questions across eight higher education domains.",
)

df = load_data()
if df is None:
    st.error("⚠️ Dataset not found. Place `nirf_2017_2025_clean.csv` in `data/`.")
    st.stop()

# ---------------------------------------------------------------------------
# Domain & Question Selection
# ---------------------------------------------------------------------------

domain_names = get_domain_names()

col_dom, col_q = st.columns([1, 2])

with col_dom:
    sel_domain = st.selectbox(
        "📁 Analytical Domain",
        domain_names,
        format_func=lambda d: f"{get_domain_icon(d)}  {d}",
        key="qe_domain",
    )

domain_data = QUESTION_DOMAINS[sel_domain]
questions_in_domain = domain_data["questions"]

question_options = [f"{q['id']}: {q['title']}" for q in questions_in_domain]

with col_q:
    sel_q_idx = st.selectbox(
        "❓ Select Question",
        range(len(question_options)),
        format_func=lambda i: question_options[i],
        key="qe_question_idx",
    )

question = questions_in_domain[sel_q_idx]

# ---------------------------------------------------------------------------
# Question Metadata Card
# ---------------------------------------------------------------------------

rules_html = ""
if question.get("analytical_rules"):
    rule_items = "".join([f"<li>{r}</li>" for r in question["analytical_rules"]])
    rules_html = f"""
    <div style="margin-top:0.75rem; font-size:0.85rem; color:#4A574E; line-height:1.5;">
        <strong>Analytical Rules & Methodology:</strong>
        <ul style="margin-top:0.3rem; padding-left:1.2rem;">{rule_items}</ul>
    </div>
    """

st.markdown(
    f"""
    <div class="question-card" style="margin-bottom:1.5rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
            <div class="q-id" style="font-weight:700; color:#3D6247;">{question['id']} · {sel_domain}</div>
            <span class="badge" style="background:#3D6247; color:#FFFFFF; padding:0.25rem 0.6rem; border-radius:12px; font-size:0.75rem;">Verified Analytics</span>
        </div>
        <div class="q-title" style="font-size:1.15rem; font-weight:600; color:#1F2D24; margin-bottom:0.35rem;">
            {question['title']}
        </div>
        <div class="q-desc" style="font-size:0.95rem; color:#27352C; font-style:italic; margin-bottom:0.2rem;">
            "{question['question']}"
        </div>
        {rules_html}
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Dynamic Context-Sensitive Filter Controls
# ---------------------------------------------------------------------------

supported_filters = question.get("supported_filters", [])
render_section_header("Filters & Cohort Parameters", "🎛️")

# Filter defaults
all_years = sorted(df["Year"].dropna().unique().astype(int).tolist())
all_categories = sorted(df["Category"].dropna().unique().tolist())

# Categorize filters into columns
filter_cols = st.columns(4)
col_idx = 0

sel_category = "Overall"
sel_year = 2025
sel_institution = "Indian Institute of Technology Madras"
sel_y1, sel_y2 = 2024, 2025

# 1. Category Filter
if "category" in supported_filters:
    with filter_cols[col_idx % 4]:
        default_cat_idx = all_categories.index("Overall") if "Overall" in all_categories else 0
        sel_category = st.selectbox(
            "Category",
            all_categories,
            index=default_cat_idx,
            key=f"flt_cat_{question['id']}",
        )
    col_idx += 1

# 2. Year Filter
if "year" in supported_filters:
    with filter_cols[col_idx % 4]:
        default_yr_idx = all_years.index(2025) if 2025 in all_years else len(all_years) - 1
        sel_year = st.selectbox(
            "Ranking Year",
            all_years,
            index=default_yr_idx,
            key=f"flt_yr_{question['id']}",
        )
    col_idx += 1

# 3. Comparison Years Filter
if "comparison_years" in supported_filters:
    with filter_cols[col_idx % 4]:
        default_y1_idx = all_years.index(2024) if 2024 in all_years else 0
        sel_y1 = st.selectbox(
            "Base Year (Year 1)",
            all_years,
            index=default_y1_idx,
            key=f"flt_y1_{question['id']}",
        )
    col_idx += 1

    with filter_cols[col_idx % 4]:
        default_y2_idx = all_years.index(2025) if 2025 in all_years else len(all_years) - 1
        sel_y2 = st.selectbox(
            "Target Year (Year 2)",
            all_years,
            index=default_y2_idx,
            key=f"flt_y2_{question['id']}",
        )
    col_idx += 1

# 4. Institution Filter
if "institution" in supported_filters:
    # Get institutions for the selected category
    inst_pool = df[df["Category"] == sel_category]["Name"].dropna().unique().tolist()
    if not inst_pool:
        inst_pool = sorted(df["Name"].dropna().unique().tolist())
    else:
        inst_pool = sorted(inst_pool)

    default_inst_idx = 0
    if "Indian Institute of Technology Madras" in inst_pool:
        default_inst_idx = inst_pool.index("Indian Institute of Technology Madras")

    sel_institution = st.selectbox(
        "Select Institution to Track",
        inst_pool,
        index=default_inst_idx,
        key=f"flt_inst_{question['id']}",
    )

# Action Buttons
btn_col1, btn_col2, _ = st.columns([1, 1, 3])
with btn_col1:
    run_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)
with btn_col2:
    if st.button("↺ Reset Filters", use_container_width=True):
        st.rerun()

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Analytics Execution
# ---------------------------------------------------------------------------

fig, insights, table, err = execute_question(
    question_or_id=question,
    df=df,
    year=sel_year,
    category=sel_category,
    institution=sel_institution,
    comparison_years=(sel_y1, sel_y2),
)

if err:
    st.error(f"Execution Error: {err}")
    st.stop()

# ---------------------------------------------------------------------------
# Visualization Section
# ---------------------------------------------------------------------------

render_section_header("Interactive Visualization", "📊")

if fig is not None:
    render_chart(fig, key=f"chart_{question['id']}")
else:
    st.info("ℹ️ No chart available for the current filter parameters or analytical slice.")

# ---------------------------------------------------------------------------
# Key Analytical Insights
# ---------------------------------------------------------------------------

if insights:
    render_section_header("Analytical Findings & Inferences", "💡")
    for ins in insights:
        st.markdown(f'<div class="highlight-box">{ins}</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Supporting Data Table & CSV Download
# ---------------------------------------------------------------------------

render_section_header("Supporting Data Table", "📋")

if table is not None and not table.empty:
    with st.expander(f"View Supporting Records ({len(table):,} rows)", expanded=True):
        st.dataframe(table, use_container_width=True, hide_index=True)
        csv_bytes = table.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"⬇️ Download {question['id']} Results (CSV)",
            data=csv_bytes,
            file_name=f"nirf_{question['id'].lower()}_results.csv",
            mime="text/csv",
            key=f"dl_btn_{question['id']}",
        )
else:
    st.info("No numerical records available for tabular display.")

# ---------------------------------------------------------------------------
# All Questions in Domain Reference
# ---------------------------------------------------------------------------

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
with st.expander(f"📚 All Questions in {sel_domain} ({len(questions_in_domain)})", expanded=False):
    for q in questions_in_domain:
        is_current = q["id"] == question["id"]
        border_col = "#3D6247" if is_current else "#E4E9E0"
        bg_col = "#F4F7F2" if is_current else "#FFFFFF"
        st.markdown(
            f"""
            <div style="border-left:4px solid {border_col}; background:{bg_col}; padding:0.6rem 0.9rem; margin-bottom:0.5rem; border-radius:4px;">
                <strong>{q['id']} — {q['title']}</strong><br/>
                <span style="font-size:0.85rem; color:#4A574E;">{q['question']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
