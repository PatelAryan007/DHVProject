"""
NIRF Insight — Dynamic Graph Builder
=====================================
A fully functional interactive workspace allowing users to explore the NIRF dataset,
select variables, apply multi-dimensional filters, choose from 18 chart types,
customize appearance, inspect aggregated tables, save configurations, and export assets.
"""

import streamlit as st
import pandas as pd
import json

from core.data_loader import load_data
from core.preprocessing import get_unique_values
from components.header import render_page_header, render_section_header
from components.charts import render_chart, COLORS
from core.analytics import calculate_correlation
from core.dynamic_chart_engine import (
    ALL_18_CHART_TYPES,
    AGGREGATION_METHODS,
    PALETTES,
    get_column_types,
    generate_dynamic_chart,
)

# ---------------------------------------------------------------------------
# Page Header
# ---------------------------------------------------------------------------

render_page_header(
    "Dynamic Graph Builder",
    "Design and generate customized, interactive visualizations from the NIRF dataset "
    "with flexible axes, statistical aggregations, and advanced cohort filters.",
)

df = load_data()
if df is None:
    st.error("⚠️ Dataset not found. Please verify `nirf_2017_2025_clean.csv` is present in `data/`.")
    st.stop()

num_cols, cat_cols = get_column_types(df)

# Initialize Session State for Saved Presets
if "saved_charts" not in st.session_state:
    st.session_state.saved_charts = {}

# ---------------------------------------------------------------------------
# Section A: Dataset Overview & Saved Presets
# ---------------------------------------------------------------------------

render_section_header("Dataset Overview & Presets", "📂")

kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
with kpi_c1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Available Records</div>
            <div class="kpi-value">{len(df):,}</div>
            <div class="kpi-subtext">NIRF 2017–2025 Cleaned</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with kpi_c2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Columns</div>
            <div class="kpi-value">{len(df.columns)}</div>
            <div class="kpi-subtext">{len(num_cols)} Numeric · {len(cat_cols)} Categorical</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with kpi_c3:
    years_avail = sorted(df["Year"].dropna().unique().astype(int).tolist())
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Year Span</div>
            <div class="kpi-value">{years_avail[0]}–{years_avail[-1]}</div>
            <div class="kpi-subtext">{len(years_avail)} Annual Editions</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with kpi_c4:
    cats_avail = df["Category"].dropna().unique().tolist()
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Disciplines</div>
            <div class="kpi-value">{len(cats_avail)}</div>
            <div class="kpi-subtext">Academic Categories</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Saved Presets Management
if st.session_state.saved_charts:
    with st.expander("💾 Saved Chart Configurations", expanded=False):
        preset_names = list(st.session_state.saved_charts.keys())
        p_col1, p_col2 = st.columns([3, 1])
        with p_col1:
            sel_preset = st.selectbox("Select Saved Preset to Load", preset_names, key="gb_preset_sel")
        with p_col2:
            st.write("")
            st.write("")
            if st.button("🗑️ Delete Preset", use_container_width=True):
                del st.session_state.saved_charts[sel_preset]
                st.rerun()

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Section B: Chart Type & Variable Configuration
# ---------------------------------------------------------------------------

render_section_header("Chart Type & Axes Configuration", "📊")

cfg_col1, cfg_col2, cfg_col3 = st.columns(3)

with cfg_col1:
    chart_type = st.selectbox(
        "Chart Type",
        ALL_18_CHART_TYPES,
        index=0,
        key="dgb_chart_type",
    )

all_vars = cat_cols + num_cols

with cfg_col2:
    # Intelligent default X-axis based on chart type
    if chart_type in ("Pie Chart", "Donut Chart", "Treemap", "Sunburst Chart", "Bar Chart"):
        default_x_idx = all_vars.index("Category") if "Category" in all_vars else 0
    elif chart_type in ("Line Chart", "Area Chart"):
        default_x_idx = all_vars.index("Year") if "Year" in all_vars else 0
    elif chart_type in ("Histogram", "Box Plot", "Violin Plot"):
        default_x_idx = all_vars.index("Score") if "Score" in all_vars else 0
    elif chart_type in ("Scatter Plot", "Bubble Chart"):
        default_x_idx = all_vars.index("RPC") if "RPC" in all_vars else 0
    else:
        default_x_idx = 0

    x_axis = st.selectbox("X-Axis Variable", all_vars, index=default_x_idx, key="dgb_x_axis")

with cfg_col3:
    # Intelligent default Y-axis
    if chart_type in ("Histogram", "Pie Chart", "Donut Chart", "Treemap", "Sunburst Chart"):
        y_options = ["None (Count)"] + num_cols
        y_axis_choice = st.selectbox("Value / Y-Axis Variable", y_options, index=0, key="dgb_y_axis")
        y_axis = None if y_axis_choice.startswith("None") else y_axis_choice
    else:
        default_y_idx = num_cols.index("Score") if "Score" in num_cols else 0
        y_axis = st.selectbox("Y-Axis Variable", num_cols, index=default_y_idx, key="dgb_y_axis")

# Secondary Grouping, Color & Aggregation Row
grp_col1, grp_col2, grp_col3, grp_col4 = st.columns(4)

with grp_col1:
    color_options = ["None"] + cat_cols + num_cols
    color_choice = st.selectbox("Color By (Optional)", color_options, index=0, key="dgb_color")
    color_var = None if color_choice == "None" else color_choice

with grp_col2:
    group_options = ["None"] + cat_cols
    group_choice = st.selectbox("Sub-Group / Stack By", group_options, index=0, key="dgb_group")
    group_var = None if group_choice == "None" else group_choice

with grp_col3:
    if chart_type == "Bubble Chart":
        size_options = num_cols
        default_size = num_cols.index("Score") if "Score" in num_cols else 0
        size_var = st.selectbox("Bubble Size Variable*", size_options, index=default_size, key="dgb_size")
    else:
        size_var = None
        st.selectbox("Bubble Size Variable", ["Disabled for this chart"], disabled=True, key="dgb_size_dis")

with grp_col4:
    agg_method = st.selectbox("Aggregation Method", AGGREGATION_METHODS, index=0, key="dgb_agg")

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Section C: Multi-Dimensional Filter System
# ---------------------------------------------------------------------------

render_section_header("Cohort & Field Filters", "🎛️")

with st.expander("🔍 Click to Expand Active Filter Controls", expanded=True):
    f_c1, f_c2, f_c3 = st.columns(3)

    with f_c1:
        sel_years = st.multiselect(
            "Filter by Year(s)",
            years_avail,
            default=years_avail,
            key="dgb_flt_years",
        )

    with f_c2:
        sel_cats = st.multiselect(
            "Filter by Category",
            cats_avail,
            default=cats_avail,
            key="dgb_flt_cats",
        )

    with f_c3:
        all_states = sorted(df["State"].dropna().unique().tolist())
        sel_states = st.multiselect(
            "Filter by State(s)",
            all_states,
            default=[],
            placeholder="All States (Optional filter)",
            key="dgb_flt_states",
        )

    f_c4, f_c5 = st.columns(2)

    with f_c4:
        inst_query = st.text_input(
            "Institution Search",
            placeholder="Search by institution name (e.g., IIT, University, Delhi)…",
            key="dgb_inst_query",
        )

    with f_c5:
        # Score Range Slider
        min_sc = float(df["Score"].min()) if pd.notna(df["Score"].min()) else 0.0
        max_sc = float(df["Score"].max()) if pd.notna(df["Score"].max()) else 100.0
        score_range = st.slider(
            "NIRF Score Range",
            min_value=round(min_sc, 1),
            max_value=round(max_sc, 1),
            value=(round(min_sc, 1), round(max_sc, 1)),
            key="dgb_score_range",
        )

    # Rank Range Slider
    r_c1, r_c2 = st.columns(2)
    with r_c1:
        rank_range = st.slider(
            "Rank Range",
            min_value=1,
            max_value=int(df["Rank"].max()) if pd.notna(df["Rank"].max()) else 300,
            value=(1, int(df["Rank"].max()) if pd.notna(df["Rank"].max()) else 300),
            key="dgb_rank_range",
        )

    with r_c2:
        top_n_limit = st.slider(
            "Limit Records Rendered (for performance)",
            min_value=20,
            max_value=2000,
            value=300,
            step=20,
            key="dgb_top_n",
        )

# Apply Filter Cascade
filtered_df = df.copy()

if sel_years:
    filtered_df = filtered_df[filtered_df["Year"].isin(sel_years)]

if sel_cats:
    filtered_df = filtered_df[filtered_df["Category"].isin(sel_cats)]

if sel_states:
    filtered_df = filtered_df[filtered_df["State"].isin(sel_states)]

if inst_query.strip():
    filtered_df = filtered_df[filtered_df["Name"].str.contains(inst_query.strip(), case=False, na=False)]

if "Score" in filtered_df.columns:
    filtered_df = filtered_df[
        (filtered_df["Score"].isna()) |
        ((filtered_df["Score"] >= score_range[0]) & (filtered_df["Score"] <= score_range[1]))
    ]

if "Rank" in filtered_df.columns:
    filtered_df = filtered_df[
        (filtered_df["Rank"].isna()) |
        ((filtered_df["Rank"] >= rank_range[0]) & (filtered_df["Rank"] <= rank_range[1]))
    ]

# Summary of Filtered Slices
filter_badges = [
    f"Years: {len(sel_years)} selected" if len(sel_years) < len(years_avail) else "All Years",
    f"Categories: {len(sel_cats)} selected" if len(sel_cats) < len(cats_avail) else "All Categories",
    f"States: {len(sel_states)} selected" if sel_states else "All States",
    f"Score: [{score_range[0]} – {score_range[1]}]",
    f"Rank: [{rank_range[0]} – {rank_range[1]}]",
]
if inst_query.strip():
    filter_badges.append(f"Name Match: '{inst_query.strip()}'")

st.markdown(
    f"""
    <div class="highlight-box">
        <strong>Active Cohort:</strong> {len(filtered_df):,} records matching filters ({' · '.join(filter_badges)})
    </div>
    """,
    unsafe_allow_html=True,
)

if filtered_df.empty:
    st.warning("⚠️ No records match your selected filter criteria. Please broaden your filters above.")
    st.stop()

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Section D: Chart Customization Panel
# ---------------------------------------------------------------------------

render_section_header("Visual Styling & Customization", "🎨")

with st.expander("🛠️ Customize Appearance, Dimensions & Statistical Overlays", expanded=False):
    cust_col1, cust_col2, cust_col3 = st.columns(3)

    with cust_col1:
        custom_title = st.text_input(
            "Chart Title",
            value=f"{chart_type}: {y_axis or 'Count'} vs {x_axis}",
            key="dgb_cust_title",
        )
        x_custom_title = st.text_input("Custom X-Axis Label (Optional)", value="", key="dgb_x_title")
        y_custom_title = st.text_input("Custom Y-Axis Label (Optional)", value="", key="dgb_y_title")

    with cust_col2:
        selected_palette = st.selectbox("Color Palette", list(PALETTES.keys()), index=0, key="dgb_palette")
        chart_height = st.slider("Chart Height (px)", min_value=350, max_value=800, value=500, step=25, key="dgb_height")
        show_legend = st.checkbox("Show Legend", value=True, key="dgb_show_legend")

    with cust_col3:
        marker_size = st.slider("Marker Size (Scatter / Bubble)", 4, 25, 8, key="dgb_marker_size")
        opacity = st.slider("Opacity", 0.2, 1.0, 0.85, 0.05, key="dgb_opacity")
        show_trendline = st.checkbox("Show Trendline (Scatter)", value=(chart_type == "Scatter Plot"), key="dgb_trendline")
        show_labels = st.checkbox("Show Data Labels (Bars)", value=False, key="dgb_labels")

customization_dict = {
    "title": custom_title,
    "x_title": x_custom_title or None,
    "y_title": y_custom_title or None,
    "height": chart_height,
    "palette": selected_palette,
    "show_legend": show_legend,
    "marker_size": marker_size,
    "opacity": opacity,
    "show_trendline": show_trendline,
    "show_labels": show_labels,
}

# Action Buttons
btn_col1, btn_col2, btn_col3 = st.columns([1.5, 1.5, 3])

with btn_col1:
    generate_btn = st.button("🚀 Generate Chart", type="primary", use_container_width=True)

with btn_col2:
    if st.button("↺ Reset Selections", use_container_width=True):
        st.rerun()

with btn_col3:
    save_preset_name = st.text_input("Preset Name", placeholder="e.g. My Score Trend", label_visibility="collapsed")
    if st.button("💾 Save Configuration Preset", use_container_width=False):
        if save_preset_name.strip():
            st.session_state.saved_charts[save_preset_name.strip()] = {
                "chart_type": chart_type,
                "x_axis": x_axis,
                "y_axis": y_axis,
                "color_var": color_var,
                "group_var": group_var,
                "size_var": size_var,
                "agg_method": agg_method,
                "customization": customization_dict,
            }
            st.success(f"Preset '{save_preset_name.strip()}' saved to current session!")
        else:
            st.warning("Enter a preset name to save.")

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Section E: Visualization & Multidimensional Results
# ---------------------------------------------------------------------------

render_section_header("Visualization & Results Workspace", "📈")

# Apply performance slice for chart generation
render_df = filtered_df.head(top_n_limit) if agg_method == "None" else filtered_df

fig, final_plot_df, err = generate_dynamic_chart(
    df=render_df,
    chart_type=chart_type,
    x_var=x_axis,
    y_var=y_axis,
    color_var=color_var,
    group_var=group_var,
    size_var=size_var,
    agg_method=agg_method,
    customization=customization_dict,
)

if err:
    st.error(f"⚠️ {err}")
    st.info("💡 Tip: Try adjusting the X-axis or Y-axis to match the selected chart type requirements.")
    st.stop()

# Statistical Callout for Bivariate Scatter
if chart_type in ("Scatter Plot", "Bubble Chart") and x_axis in num_cols and y_axis in num_cols:
    corr_r, n_obs, desc = calculate_correlation(filtered_df, x_axis, y_axis)
    if corr_r is not None:
        st.markdown(
            f"""
            <div style="background:#FFFFFF; border:1px solid #D6DED1; border-radius:8px; padding:0.6rem 1rem; margin-bottom:1rem; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <strong>Statistical Correlation:</strong> {x_axis} vs {y_axis}
                </div>
                <div>
                    Pearson <em>r</em> = <strong>{corr_r}</strong> ({desc}) · <em>n</em> = {n_obs:,}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# Result Tabs
tab_chart, tab_filtered, tab_agg, tab_cfg = st.tabs([
    "📊 Generated Chart",
    "📋 Filtered Dataset",
    "🔢 Aggregated Data Table",
    "⚙️ Configuration Metadata",
])

with tab_chart:
    if fig is not None:
        render_chart(fig, key="dgb_main_canvas")
    else:
        st.info("No visualization generated.")

    # Export Action Bar
    st.markdown("##### 📥 Export Options")
    exp_col1, exp_col2, exp_col3 = st.columns([1, 1, 1])

    with exp_col1:
        # Interactive HTML Export
        if fig is not None:
            html_bytes = fig.to_html(include_plotlyjs="cdn").encode("utf-8")
            st.download_button(
                label="🌐 Export Interactive Chart (HTML)",
                data=html_bytes,
                file_name="nirf_custom_chart.html",
                mime="text/html",
                use_container_width=True,
            )

    with exp_col2:
        # Aggregated Data CSV
        if not final_plot_df.empty:
            agg_csv = final_plot_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📊 Download Chart Data (CSV)",
                data=agg_csv,
                file_name="nirf_chart_aggregated_data.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with exp_col3:
        # Full Filtered Cohort CSV
        full_csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📁 Download Full Filtered Cohort (CSV)",
            data=full_csv,
            file_name="nirf_filtered_cohort.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.caption("📷 **Image Export (PNG/SVG):** Use the camera icon in the top-right toolbar of the chart canvas above for instant image capture.")

with tab_filtered:
    st.markdown(f"**Showing {min(500, len(filtered_df)):,} of {len(filtered_df):,} matching rows**")
    st.dataframe(filtered_df.head(500).reset_index(drop=True), use_container_width=True, hide_index=True)

with tab_agg:
    st.markdown(f"**Aggregated Data ({len(final_plot_df):,} rows driving visualization)**")
    st.dataframe(final_plot_df.reset_index(drop=True), use_container_width=True, hide_index=True)

with tab_cfg:
    config_summary = {
        "Chart_Type": chart_type,
        "X_Axis": x_axis,
        "Y_Axis": y_axis,
        "Color_Variable": color_var,
        "Group_Variable": group_var,
        "Bubble_Size_Variable": size_var,
        "Aggregation": agg_method,
        "Records_In_Cohort": len(filtered_df),
        "Records_In_Chart": len(final_plot_df),
        "Active_Filters": {
            "Years": sel_years,
            "Categories": sel_cats,
            "States": sel_states if sel_states else "All",
            "Score_Range": score_range,
            "Rank_Range": rank_range,
            "Institution_Query": inst_query if inst_query.strip() else None,
        },
        "Customization": customization_dict,
    }
    st.json(config_summary)
