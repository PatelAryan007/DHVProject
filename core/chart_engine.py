"""
NIRF Insight — Chart Engine Module
==================================
High-level Plotly visualization engine connecting analytics outputs
to beautifully styled, consistent visual charts.
"""

from typing import Any
import pandas as pd
import numpy as np
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
    create_heatmap,
    create_radar_chart,
    create_multi_radar_chart,
    render_chart,
)
from core.analytics import (
    get_top_institutions,
    get_category_distribution,
    get_state_distribution,
    get_yearly_trend,
    get_correlation_matrix,
    detect_outliers_iqr,
)


def plot_top_institutions(
    df: pd.DataFrame,
    n: int = 10,
    by: str = "Score",
    category: str | None = None,
    year: int | None = None,
):
    """Generate horizontal bar chart of top institutions."""
    top_df = get_top_institutions(df, n=n, by=by, category=category, year=year)
    if top_df.empty:
        return None

    top_sorted = top_df.sort_values(by, ascending=True)
    title = f"Top {len(top_sorted)} Institutions by {by}"
    if category and str(category) != "All":
        title += f" ({category})"
    if year and str(year) != "All":
        title += f" · {year}"

    return create_bar_chart(
        top_sorted,
        x="Name",
        y=by,
        title=title,
        horizontal=True,
        color=COLORS["primary"],
    )


def plot_category_distribution(df: pd.DataFrame):
    """Generate bar chart for category distribution."""
    dist = get_category_distribution(df)
    if dist.empty:
        return None
    return create_bar_chart(
        dist,
        x="Category",
        y="Count",
        title="Institution Distribution by Category",
        color=COLORS["secondary"],
    )


def plot_state_distribution(df: pd.DataFrame, top_n: int = 15):
    """Generate horizontal bar chart for top states by institution count."""
    dist = get_state_distribution(df)
    if dist.empty:
        return None
    top_states = dist.head(top_n).sort_values("Count", ascending=True)
    return create_bar_chart(
        top_states,
        x="State",
        y="Count",
        title=f"Top {len(top_states)} States by Institution Count",
        horizontal=True,
        color=COLORS["accent"],
    )


def plot_score_trend(df: pd.DataFrame, group_by: str | None = None):
    """Generate yearly trend line chart for average score."""
    trend = get_yearly_trend(df, metric="Score", group_by=group_by)
    if trend.empty:
        return None
    return create_line_chart(
        trend,
        x="Year",
        y="Score",
        color=group_by,
        title="Average NIRF Score Trend (2017–2025)",
    )


def plot_score_histogram(df: pd.DataFrame, nbins: int = 30):
    """Generate score distribution histogram."""
    if "Score" not in df.columns or df["Score"].dropna().empty:
        return None
    return create_histogram(
        df,
        x="Score",
        title="Overall Distribution of NIRF Scores",
        nbins=nbins,
    )


def plot_parameter_radar(df: pd.DataFrame, institution_name: str, year: int | None = None):
    """Generate radar profile for a specific institution across the 5 NIRF parameters."""
    from core.analytics import get_parameter_profile

    profile = get_parameter_profile(df, institution_name, year=year)
    if not profile:
        return None

    params = ["TLR", "RPC", "GO", "OI", "Perception"]
    values = [profile.get(p) for p in params]
    if any(v is None for v in values):
        return None

    yr_str = f" ({profile.get('Year')})" if profile.get("Year") else ""
    return create_radar_chart(
        categories=params,
        values=values,
        title=f"Parameter Profile: {institution_name}{yr_str}",
        name=institution_name,
    )


def plot_outlier_detection(df: pd.DataFrame, column: str = "Score", factor: float = 1.5):
    """Generate box plot and scatter visualization highlighting statistical outliers."""
    outliers_df, diag = detect_outliers_iqr(df, column=column, factor=factor)
    if not diag:
        return None

    fig = px.box(
        df,
        y=column,
        points="all",
        title=f"{column} Outlier Analysis (IQR Factor: {factor} · {diag.get('outlier_count', 0)} Outliers Detected)",
        color_discrete_sequence=[COLORS["primary"]],
    )
    return _apply_layout(fig, height=450)
