"""
NIRF Insight — Chart Components
Reusable Plotly chart builders with a consistent visual theme.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Colour Palette
# ---------------------------------------------------------------------------

COLORS = {
    "primary": "#3D6247",
    "secondary": "#5D7A60",
    "accent": "#B89248",
    "text": "#1F2D24",
    "secondary_text": "#4A574E",
    "bg": "#F7F8F4",
    "card": "#FFFFFF",
    "border": "#D6DED1",
}

COLOR_SEQUENCE = [
    "#476B52", "#78947A", "#C6A56B", "#5A8A6A",
    "#A3B89A", "#D4B87A", "#3D5C46", "#8FA88F",
    "#B8956A", "#6B9E7A", "#C4CFC0", "#E8D5A8",
]


# ---------------------------------------------------------------------------
# Layout Helper
# ---------------------------------------------------------------------------

def _apply_layout(fig, title: str = "", height: int = 450):
    """Apply the NIRF Insight theme to any Plotly figure."""
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color=COLORS["text"], family="Inter, sans-serif"),
            x=0, xanchor="left",
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=COLORS["text"], size=12),
        margin=dict(l=40, r=20, t=60, b=40),
        height=height,
        legend=dict(
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor=COLORS["border"],
            borderwidth=1,
            font=dict(size=11),
        ),
        hoverlabel=dict(
            bgcolor=COLORS["card"],
            font_size=12,
            font_family="Inter, sans-serif",
        ),
    )
    fig.update_xaxes(
        gridcolor="#EBF0E6",
        linecolor=COLORS["border"],
        tickfont=dict(size=11, color=COLORS["secondary_text"]),
        title_font=dict(size=12, color=COLORS["text"]),
    )
    fig.update_yaxes(
        gridcolor="#EBF0E6",
        linecolor=COLORS["border"],
        tickfont=dict(size=11, color=COLORS["secondary_text"]),
        title_font=dict(size=12, color=COLORS["text"]),
    )
    return fig


# ---------------------------------------------------------------------------
# Chart Builders
# ---------------------------------------------------------------------------

def create_bar_chart(df, x, y, title="", horizontal=False, color=None, color_col=None):
    """Vertical or horizontal bar chart."""
    if df is None or df.empty:
        return None
    if horizontal:
        fig = px.bar(df, x=y, y=x, orientation="h", color=color_col,
                     color_discrete_sequence=COLOR_SEQUENCE)
    else:
        fig = px.bar(df, x=x, y=y, color=color_col,
                     color_discrete_sequence=COLOR_SEQUENCE)
    if color and not color_col:
        fig.update_traces(marker_color=color)
    return _apply_layout(fig, title)


def create_line_chart(df, x, y, title="", color=None, markers=True):
    """Line chart with optional markers."""
    if df is None or df.empty:
        return None
    fig = px.line(df, x=x, y=y, color=color,
                  color_discrete_sequence=COLOR_SEQUENCE, markers=markers)
    return _apply_layout(fig, title)


def create_scatter_chart(df, x, y, title="", color=None, size=None,
                         trendline=None, hover_name=None):
    """Scatter plot with optional trendline."""
    if df is None or df.empty:
        return None

    # Check if statsmodels is installed for plotly's built-in OLS
    try:
        import statsmodels  # noqa: F401
        has_statsmodels = True
    except ImportError:
        has_statsmodels = False

    fig = px.scatter(
        df, x=x, y=y, color=color, size=size,
        trendline=trendline if has_statsmodels else None,
        hover_name=hover_name,
        color_discrete_sequence=COLOR_SEQUENCE,
    )

    # Fallback trendline using numpy if statsmodels is not installed
    if trendline and not has_statsmodels and x in df.columns and y in df.columns:
        try:
            clean_sub = df[[x, y]].dropna()
            if (
                len(clean_sub) >= 2
                and pd.api.types.is_numeric_dtype(clean_sub[x])
                and pd.api.types.is_numeric_dtype(clean_sub[y])
            ):
                m, b = np.polyfit(clean_sub[x], clean_sub[y], 1)
                x_vals = np.array([clean_sub[x].min(), clean_sub[x].max()])
                y_vals = m * x_vals + b
                fig.add_trace(
                    go.Scatter(
                        x=x_vals,
                        y=y_vals,
                        mode="lines",
                        name="Trendline",
                        line=dict(color="#C6A56B", dash="dash", width=2),
                    )
                )
        except Exception:
            pass

    return _apply_layout(fig, title)


def create_histogram(df, x, title="", nbins=30, color=None):
    """Histogram."""
    if df is None or df.empty:
        return None
    fig = px.histogram(df, x=x, nbins=nbins, color=color,
                       color_discrete_sequence=COLOR_SEQUENCE)
    fig.update_traces(marker_line_color=COLORS["card"], marker_line_width=1)
    return _apply_layout(fig, title)


def create_pie_chart(df, names, values, title="", hole=0.4):
    """Donut chart."""
    if df is None or df.empty:
        return None
    fig = px.pie(df, names=names, values=values, hole=hole,
                 color_discrete_sequence=COLOR_SEQUENCE)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _apply_layout(fig, title, height=400)


def create_heatmap(corr_matrix, title=""):
    """Heatmap (typically for a correlation matrix)."""
    if corr_matrix is None or corr_matrix.empty:
        return None
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns.tolist(),
        y=corr_matrix.index.tolist(),
        colorscale=[[0, "#F7F8F4"], [0.5, "#78947A"], [1, "#476B52"]],
        text=corr_matrix.values.round(2),
        texttemplate="%{text}",
        textfont=dict(size=12),
        hovertemplate="%{x} vs %{y}: %{z:.3f}<extra></extra>",
    ))
    return _apply_layout(fig, title, height=500)


def create_box_plot(df, x, y, title="", color=None):
    """Box plot."""
    if df is None or df.empty:
        return None
    fig = px.box(df, x=x, y=y, color=color,
                 color_discrete_sequence=COLOR_SEQUENCE)
    return _apply_layout(fig, title)


def create_area_chart(df, x, y, title="", color=None):
    """Area chart."""
    if df is None or df.empty:
        return None
    fig = px.area(df, x=x, y=y, color=color,
                  color_discrete_sequence=COLOR_SEQUENCE)
    return _apply_layout(fig, title)


def create_radar_chart(categories: list[str], values: list[float], title="", name=""):
    """Radar / spider chart."""
    if not categories or not values:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(71, 107, 82, 0.15)",
        line=dict(color=COLORS["primary"], width=2),
        name=name or "Values",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, gridcolor="#F0F0EC"),
            angularaxis=dict(gridcolor="#F0F0EC"),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return _apply_layout(fig, title, height=450)


def create_multi_radar_chart(categories, traces: list[dict], title=""):
    """Radar chart with multiple series.

    Each item in *traces* should be ``{"name": …, "values": [...]}``.
    """
    if not categories or not traces:
        return None
    fills = [
        "rgba(71,107,82,0.12)", "rgba(198,165,107,0.12)",
        "rgba(120,148,122,0.12)", "rgba(90,138,106,0.12)",
    ]
    colors = COLOR_SEQUENCE
    fig = go.Figure()
    for i, t in enumerate(traces):
        vals = t["values"]
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=categories + [categories[0]],
            fill="toself",
            fillcolor=fills[i % len(fills)],
            line=dict(color=colors[i % len(colors)], width=2),
            name=t["name"],
        ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, gridcolor="#F0F0EC"),
            angularaxis=dict(gridcolor="#F0F0EC"),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return _apply_layout(fig, title, height=480)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_chart(fig, key=None):
    """Safely display a Plotly figure; show an info message if *fig* is None."""
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True, key=key)
    else:
        st.info("📭 No data available for this visualization.")
