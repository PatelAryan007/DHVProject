"""
NIRF Insight — Question Chart Mapping Engine
=============================================
Maps question outputs to customized, theme-grounded Plotly visualizations.
Handles axis inversion for rankings, color sequences, multi-traces, and radar profiles.
"""

from typing import Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from components.charts import (
    COLORS,
    COLOR_SEQUENCE,
    _apply_layout,
    create_bar_chart,
    create_line_chart,
    create_scatter_chart,
    create_histogram,
    create_box_plot,
    create_pie_chart,
    create_multi_radar_chart,
)

PARAMETER_COLS = ["TLR", "RPC", "GO", "OI", "Perception"]


def build_question_chart(
    question_id: str,
    data: pd.DataFrame,
    title: str = "",
    extra_params: dict[str, Any] | None = None,
) -> Any:
    """Build grounded, publication-ready Plotly chart for a given question ID."""
    if data is None or data.empty:
        return None

    qid = question_id.upper().strip()
    extra_params = extra_params or {}

    # =========================================================================
    # DOMAIN 1: TIME-SERIES AND TREND ANALYSIS (Q1 - Q5)
    # =========================================================================
    if qid == "Q1":
        # Institutional Rank Trajectory (Inverted Y-axis so Rank #1 is at top)
        fig = create_line_chart(data, x="Year", y="Rank", title=title, markers=True)
        if fig:
            fig.update_yaxes(autorange="reversed", title="NIRF Rank (Lower = Better)")
            fig.update_traces(line=dict(color=COLORS["primary"], width=3), marker=dict(size=9, color=COLORS["accent"]))
        return fig

    elif qid == "Q2":
        # Greatest Rank Improvement (Horizontal Bar)
        df_sort = data.sort_values("Rank_Climb", ascending=True)
        return create_bar_chart(
            df_sort, x="Name", y="Rank_Climb", title=title, horizontal=True, color=COLORS["primary"]
        )

    elif qid == "Q3":
        # Largest Rank Decline (Horizontal Bar)
        df_sort = data.sort_values("Rank_Decline", ascending=True)
        return create_bar_chart(
            df_sort, x="Name", y="Rank_Decline", title=title, horizontal=True, color="#A04040"
        )

    elif qid == "Q4":
        # Average NIRF Score Trend Over Time
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data["Year"], y=data["Mean_Score"],
            mode="lines+markers", name="Mean Score",
            line=dict(color=COLORS["primary"], width=3),
            marker=dict(size=8),
        ))
        fig.add_trace(go.Scatter(
            x=data["Year"], y=data["Median_Score"],
            mode="lines+markers", name="Median Score",
            line=dict(color=COLORS["accent"], width=2, dash="dash"),
            marker=dict(size=7),
        ))
        return _apply_layout(fig, title)

    elif qid == "Q5":
        # Persistent Top 10 Institutions (Horizontal Bar)
        df_sort = data.sort_values("Top_10_Appearances", ascending=True).tail(15)
        return create_bar_chart(
            df_sort, x="Name", y="Top_10_Appearances", title=title, horizontal=True, color=COLORS["primary"]
        )

    # =========================================================================
    # DOMAIN 2: GEOSPATIAL AND REGIONAL ANALYSIS (Q6 - Q10)
    # =========================================================================
    elif qid == "Q6":
        # States with Highest Top 100 Count
        df_sort = data.sort_values("Top_100_Count", ascending=True).tail(15)
        return create_bar_chart(
            df_sort, x="State", y="Top_100_Count", title=title, horizontal=True, color=COLORS["primary"]
        )

    elif qid == "Q7":
        # Geographic Distribution Change (Grouped Bar or Multi-Line)
        return create_line_chart(data, x="Year", y="Top_100_Count", color="State", title=title)

    elif qid == "Q8":
        # States Improving Top 100 Representation (Diverging Bar)
        df_sort = data.sort_values("Net_Improvement", ascending=True).tail(15)
        colors = [COLORS["primary"] if v >= 0 else "#A04040" for v in df_sort["Net_Improvement"]]
        fig = px.bar(df_sort, x="Net_Improvement", y="State", orientation="h", title=title)
        fig.update_traces(marker_color=colors)
        return _apply_layout(fig, title)

    elif qid == "Q9":
        # Karnataka vs Tamil Nadu (Side-by-side Box Plot)
        return create_box_plot(data, x="State", y="Score", title=title, color="State")

    elif qid == "Q10":
        # States with Largest New Entrants (Bar Chart)
        df_sort = data.sort_values("New_Entrants_Count", ascending=True).tail(15)
        return create_bar_chart(
            df_sort, x="State", y="New_Entrants_Count", title=title, horizontal=True, color=COLORS["secondary"]
        )

    # =========================================================================
    # DOMAIN 3: UNIVARIATE ANALYSIS (Q11 - Q15)
    # =========================================================================
    elif qid == "Q11":
        # NIRF Score Distribution (Histogram)
        return create_histogram(data, x="Score", title=title, nbins=30)

    elif qid == "Q12":
        # Overall Rank Distribution (Rank Bands Bar Chart)
        return create_bar_chart(data, x="Rank_Band", y="Institution_Count", title=title, color=COLORS["primary"])

    elif qid == "Q13":
        # Score Summary Statistics (Box Plot)
        return create_box_plot(data, x="Category" if "Category" in data.columns else None, y="Score" if "Score" in data.columns else "Value", title=title)

    elif qid == "Q14":
        # Score Quartile Percentage (Donut/Pie Chart)
        return create_pie_chart(data, names="Quartile", values="Institution_Count", title=title)

    elif qid == "Q15":
        # Score Distribution Across Categories (Box Plot)
        return create_box_plot(data, x="Category", y="Score", title=title)

    # =========================================================================
    # DOMAIN 4: BIVARIATE AND CORRELATION ANALYSIS (Q16 - Q20)
    # =========================================================================
    elif qid == "Q16":
        # RPC vs Score (Scatter Plot with Trendline)
        return create_scatter_chart(data, x="RPC", y="Score", title=title, hover_name="Name", trendline="ols")

    elif qid == "Q17":
        # Perception vs Score (Scatter Plot with Trendline)
        return create_scatter_chart(data, x="Perception", y="Score", title=title, hover_name="Name", trendline="ols")

    elif qid == "Q18":
        # Parameter with Strongest Score Correlation (Bar Chart)
        df_sort = data.sort_values("Pearson_r", ascending=True)
        return create_bar_chart(df_sort, x="Parameter", y="Pearson_r", title=title, horizontal=True, color=COLORS["primary"])

    elif qid == "Q19":
        # TLR vs RPC Relationship (Scatter Plot)
        return create_scatter_chart(data, x="TLR", y="RPC", title=title, hover_name="Name", trendline="ols")

    elif qid == "Q20":
        # Research Correlation Evolution (Line Chart)
        fig = create_line_chart(data, x="Year", y="Pearson_r", title=title)
        if fig:
            fig.update_yaxes(range=[0, 1.0], title="Pearson Correlation (r)")
        return fig

    # =========================================================================
    # DOMAIN 5: MULTIVARIATE ANALYSIS (Q21 - Q25)
    # =========================================================================
    elif qid == "Q21":
        # Top 5 All Parameters (Comparative Multi-Radar Chart)
        traces = []
        for _, row in data.head(5).iterrows():
            vals = [float(row[p]) for p in PARAMETER_COLS]
            traces.append({"name": row["Name"], "values": vals})
        return create_multi_radar_chart(PARAMETER_COLS, traces, title=title)

    elif qid == "Q22":
        # High RPC Low TLR (Horizontal Bar)
        df_sort = data.sort_values("RPC_minus_TLR", ascending=True).tail(10)
        return create_bar_chart(df_sort, x="Name", y="RPC_minus_TLR", title=title, horizontal=True, color=COLORS["accent"])

    elif qid == "Q23":
        # High TLR Low Perception (Horizontal Bar)
        df_sort = data.sort_values("TLR_minus_Perception", ascending=True).tail(10)
        return create_bar_chart(df_sort, x="Name", y="TLR_minus_Perception", title=title, horizontal=True, color=COLORS["secondary"])

    elif qid == "Q24":
        # Improved Score Despite Parameter Decline (Bar Chart)
        df_sort = data.sort_values("Score_Improvement", ascending=True).tail(10)
        return create_bar_chart(df_sort, x="Name", y="Score_Improvement", title=title, horizontal=True, color=COLORS["primary"])

    elif qid == "Q25":
        # Largest Parameter Gap (Horizontal Bar)
        df_sort = data.sort_values("Parameter_Gap", ascending=True).tail(12)
        return create_bar_chart(df_sort, x="Name", y="Parameter_Gap", title=title, horizontal=True, color="#B89248")

    # =========================================================================
    # DOMAIN 6: DISTRIBUTION AND STATISTICAL ANALYSIS (Q26 - Q30)
    # =========================================================================
    elif qid == "Q26":
        # Top 10 vs Remaining (Comparative Box Plot)
        return create_box_plot(data, x="Cohort", y="Score", title=title, color="Cohort")

    elif qid == "Q27":
        # Score Dispersion Two Years (Box Plot by Year)
        data_copy = data.copy()
        data_copy["Year"] = data_copy["Year"].astype(str)
        return create_box_plot(data_copy, x="Year", y="Score", title=title, color="Year")

    elif qid == "Q28":
        # Parameter with Greatest Variability (Bar Chart)
        return create_bar_chart(data, x="Parameter", y="Std_Dev", title=title, color=COLORS["primary"])

    elif qid == "Q29":
        # Median and IQR Over Time (Multi-Line Chart)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data["Year"], y=data["Median_Score"],
            mode="lines+markers", name="Median Score",
            line=dict(color=COLORS["primary"], width=3),
        ))
        fig.add_trace(go.Scatter(
            x=data["Year"], y=data["IQR"],
            mode="lines+markers", name="IQR (Spread)",
            line=dict(color=COLORS["accent"], width=2, dash="dash"),
        ))
        return _apply_layout(fig, title)

    elif qid == "Q30":
        # Score Distribution Across States (Box Plot)
        return create_box_plot(data, x="State", y="Score", title=title)

    # =========================================================================
    # DOMAIN 7: RANKING TRANSITIONS AND MOBILITY (Q31 - Q35)
    # =========================================================================
    elif qid == "Q31":
        # Transition from 51-100 to Top 50 (Bar Chart)
        if "Rank_Improvement" in data.columns and not data.empty:
            df_sort = data.sort_values("Rank_Improvement", ascending=True).tail(12)
            return create_bar_chart(df_sort, x="Name", y="Rank_Improvement", title=title, horizontal=True, color=COLORS["primary"])
        return None

    elif qid == "Q32":
        # Top 10 Entrants and Exits (Grouped Bar)
        if not data.empty and "Status" in data.columns:
            return create_bar_chart(data, x="Name", y="Status", title=title, color_col="Status")
        return None

    elif qid == "Q33":
        # Same Rank Band Percentage (Pie Chart)
        return create_pie_chart(data, names="Mobility_Status", values="Count", title=title)

    elif qid == "Q34":
        # Largest Rank Movements (Diverging Bar)
        df_sort = data.sort_values("Rank_Movement", ascending=True)
        colors = [COLORS["primary"] if v >= 0 else "#A04040" for v in df_sort["Rank_Movement"]]
        fig = px.bar(df_sort, x="Rank_Movement", y="Name", orientation="h", title=title)
        fig.update_traces(marker_color=colors)
        return _apply_layout(fig, title)

    elif qid == "Q35":
        # Annual Rank Movement Summary (Grouped Bar Chart)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=data["Transition"], y=data["Improved_Count"], name="Improved Rank", marker_color=COLORS["primary"]))
        fig.add_trace(go.Bar(x=data["Transition"], y=data["Declined_Count"], name="Declined Rank", marker_color="#A04040"))
        fig.add_trace(go.Bar(x=data["Transition"], y=data["Retained_Count"], name="Retained Rank", marker_color=COLORS["accent"]))
        fig.update_layout(barmode="group")
        return _apply_layout(fig, title)

    # =========================================================================
    # DOMAIN 8: OUTLIER AND PERFORMANCE GAP ANALYSIS (Q36 - Q40)
    # =========================================================================
    elif qid == "Q36":
        # High RPC Relative to Score (Scatter with Outlier Color)
        return create_scatter_chart(data, x="Score", y="RPC", color="Is_Outlier", title=title, hover_name="Name")

    elif qid == "Q37":
        # Substantially Better Research Than Teaching (Horizontal Bar)
        df_sort = data.sort_values("Research_Teaching_Gap", ascending=True).tail(12)
        return create_bar_chart(df_sort, x="Name", y="Research_Teaching_Gap", title=title, horizontal=True, color=COLORS["primary"])

    elif qid == "Q38":
        # Unusual YoY Score Changes (Scatter or Bar)
        df_sort = data.sort_values("Abs_Score_Change", ascending=True).tail(12)
        return create_bar_chart(df_sort, x="Name", y="Abs_Score_Change", title=title, horizontal=True, color=COLORS["accent"])

    elif qid == "Q39":
        # Strong Parameters But Poor Rank (Bar Chart of Strong Parameter Count)
        df_sort = data.sort_values("Rank", ascending=False).tail(15)
        return create_bar_chart(df_sort, x="Name", y="Rank", title=title, horizontal=True, color=COLORS["secondary"])

    elif qid == "Q40":
        # High Ranking Volatility Outliers (Horizontal Bar)
        df_sort = data.sort_values("Rank_Std", ascending=True).tail(12)
        return create_bar_chart(df_sort, x="Name", y="Rank_Std", title=title, horizontal=True, color="#B89248")

    # Generic Fallback
    return None
