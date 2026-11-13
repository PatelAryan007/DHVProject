"""
NIRF Insight — Dynamic Chart Generation Engine
================================================
Decoupled, modular chart generator supporting 18 publication-quality Plotly chart types,
statistical aggregations, multi-dimensional grouping, trendlines, and theme customization.
"""

from typing import Any
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from components.charts import (
    COLORS,
    _apply_layout,
)

# ---------------------------------------------------------------------------
# Supported Constants
# ---------------------------------------------------------------------------

ALL_18_CHART_TYPES = [
    "Bar Chart",
    "Horizontal Bar Chart",
    "Grouped Bar Chart",
    "Stacked Bar Chart",
    "Line Chart",
    "Area Chart",
    "Scatter Plot",
    "Bubble Chart",
    "Histogram",
    "Box Plot",
    "Violin Plot",
    "Pie Chart",
    "Donut Chart",
    "Heatmap",
    "Correlation Heatmap",
    "Radar Chart",
    "Treemap",
    "Sunburst Chart",
]

AGGREGATION_METHODS = ["None", "mean", "median", "sum", "count", "min", "max", "std"]

PALETTES = {
    "Forest & Sage (Default)": [
        "#476B52", "#78947A", "#C6A56B", "#5A8A6A", "#A3B89A",
        "#D4B87A", "#3D5C46", "#8FA88F", "#B8956A", "#6B9E7A",
    ],
    "Emerald": ["#005F4B", "#0E8A68", "#33B88A", "#6EDCAE", "#A7F3D0", "#064E3B"],
    "Warm Amber": ["#B89248", "#C6A56B", "#D4A373", "#E9B872", "#906B33", "#FAEDCD"],
    "Earth & Slate": ["#4F5D53", "#748679", "#9BAAA0", "#C1CBC4", "#8D6B53", "#BA9B85"],
    "Viridis": px.colors.sequential.Viridis,
    "Classic": px.colors.qualitative.Plotly,
}


# ---------------------------------------------------------------------------
# Compatibility & Validation
# ---------------------------------------------------------------------------

def get_column_types(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Identify numeric and categorical columns from the dataset."""
    if df is None or df.empty:
        return [], []
    numeric_cols = []
    categorical_cols = []
    for c in df.columns:
        if c.endswith("_Raw") or c in ("Is_Tied_Rank", "Is_Withdrawn"):
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            numeric_cols.append(c)
        else:
            categorical_cols.append(c)
    return numeric_cols, categorical_cols


def validate_chart_inputs(
    df: pd.DataFrame,
    chart_type: str,
    x_var: str | None = None,
    y_var: str | None = None,
    size_var: str | None = None,
    color_var: str | None = None,
) -> tuple[bool, str | None]:
    """Check if the user selections are compatible with the requested chart type."""
    if df is None or df.empty:
        return False, "Dataset is empty after filtering. Adjust your filters."

    if chart_type not in ALL_18_CHART_TYPES:
        return False, f"Unknown chart type: {chart_type}"

    num_cols, cat_cols = get_column_types(df)

    if chart_type in ("Bar Chart", "Horizontal Bar Chart", "Grouped Bar Chart", "Stacked Bar Chart", "Line Chart", "Area Chart"):
        if not x_var:
            return False, f"{chart_type} requires an X-axis variable."
        if not y_var and chart_type not in ("Bar Chart", "Histogram"):
            return False, f"{chart_type} requires a Y-axis variable."

    elif chart_type == "Scatter Plot":
        if not x_var or not y_var:
            return False, "Scatter Plot requires both an X-axis and a Y-axis variable."

    elif chart_type == "Bubble Chart":
        if not x_var or not y_var:
            return False, "Bubble Chart requires both an X-axis and a Y-axis variable."
        if not size_var or size_var not in num_cols:
            return False, "Bubble Chart requires a numeric Size variable to determine bubble radius."

    elif chart_type == "Histogram":
        if not x_var:
            return False, "Histogram requires an X-axis variable."

    elif chart_type in ("Box Plot", "Violin Plot"):
        if not y_var and not x_var:
            return False, f"{chart_type} requires at least one variable."

    elif chart_type in ("Pie Chart", "Donut Chart"):
        if not x_var:
            return False, f"{chart_type} requires a Category/Name variable for segments."

    elif chart_type == "Correlation Heatmap":
        if len(num_cols) < 2:
            return False, "Correlation Heatmap requires at least two numeric columns."

    elif chart_type in ("Treemap", "Sunburst Chart"):
        if not x_var:
            return False, f"{chart_type} requires at least one categorical field for hierarchy."

    return True, None


# ---------------------------------------------------------------------------
# Aggregation Handler
# ---------------------------------------------------------------------------

def aggregate_chart_data(
    df: pd.DataFrame,
    x_var: str,
    y_var: str | None = None,
    group_var: str | None = None,
    agg_method: str = "mean",
) -> pd.DataFrame:
    """Aggregate dataframe by x_var and optional group_var using agg_method."""
    if df is None or df.empty or not x_var or x_var not in df.columns:
        return df

    if agg_method == "None" or not y_var or y_var not in df.columns:
        return df

    if not pd.api.types.is_numeric_dtype(df[y_var]) and agg_method not in ("count",):
        return df

    group_cols = [x_var]
    if group_var and group_var in df.columns and group_var != x_var:
        group_cols.append(group_var)

    try:
        if agg_method == "count":
            agg_df = df.groupby(group_cols).size().reset_index(name="Count")
            return agg_df

        agg_dict = {y_var: agg_method}
        agg_df = df.groupby(group_cols).agg(agg_dict).reset_index()
        # Round numeric result
        if y_var in agg_df.columns and pd.api.types.is_numeric_dtype(agg_df[y_var]):
            agg_df[y_var] = agg_df[y_var].round(2)
        return agg_df
    except Exception:
        return df


# ---------------------------------------------------------------------------
# Dynamic Chart Dispatcher
# ---------------------------------------------------------------------------

def generate_dynamic_chart(
    df: pd.DataFrame,
    chart_type: str,
    x_var: str | None = None,
    y_var: str | None = None,
    color_var: str | None = None,
    group_var: str | None = None,
    size_var: str | None = None,
    facet_var: str | None = None,
    agg_method: str = "None",
    customization: dict[str, Any] | None = None,
) -> tuple[go.Figure | None, pd.DataFrame, str | None]:
    """Generate dynamic Plotly chart based on user parameters.

    Returns:
        (plotly_figure, aggregated_or_source_df, error_message)
    """
    custom = customization or {}
    title = custom.get("title", f"{chart_type}")
    height = custom.get("height", 480)
    palette_name = custom.get("palette", "Forest & Sage (Default)")
    palette = PALETTES.get(palette_name, PALETTES["Forest & Sage (Default)"])
    show_legend = custom.get("show_legend", True)
    marker_size = custom.get("marker_size", 8)
    opacity = custom.get("opacity", 0.8)
    line_width = custom.get("line_width", 2)
    show_trendline = custom.get("show_trendline", False)
    show_labels = custom.get("show_labels", False)

    # 1. Validation
    valid, err_msg = validate_chart_inputs(df, chart_type, x_var, y_var, size_var, color_var)
    if not valid:
        return None, pd.DataFrame(), err_msg

    plot_df = df.copy()

    # 2. Aggregation if requested
    if agg_method != "None" and x_var and chart_type in (
        "Bar Chart", "Horizontal Bar Chart", "Grouped Bar Chart", "Stacked Bar Chart",
        "Line Chart", "Area Chart", "Pie Chart", "Donut Chart", "Treemap", "Sunburst Chart"
    ):
        plot_df = aggregate_chart_data(plot_df, x_var, y_var, group_var or color_var, agg_method)

    fig = None

    try:
        # ---------------------------------------------------------------------
        # 1. Bar Chart (Vertical)
        # ---------------------------------------------------------------------
        if chart_type == "Bar Chart":
            actual_y = "Count" if agg_method == "count" else y_var
            fig = px.bar(
                plot_df, x=x_var, y=actual_y, color=color_var,
                color_discrete_sequence=palette,
                title=title, text_auto=show_labels,
                opacity=opacity,
            )

        # ---------------------------------------------------------------------
        # 2. Horizontal Bar Chart
        # ---------------------------------------------------------------------
        elif chart_type == "Horizontal Bar Chart":
            actual_val = "Count" if agg_method == "count" else y_var
            fig = px.bar(
                plot_df, x=actual_val, y=x_var, orientation="h",
                color=color_var, color_discrete_sequence=palette,
                title=title, text_auto=show_labels,
                opacity=opacity,
            )

        # ---------------------------------------------------------------------
        # 3. Grouped Bar Chart
        # ---------------------------------------------------------------------
        elif chart_type == "Grouped Bar Chart":
            actual_y = "Count" if agg_method == "count" else y_var
            c_col = color_var or group_var
            fig = px.bar(
                plot_df, x=x_var, y=actual_y, color=c_col,
                barmode="group", color_discrete_sequence=palette,
                title=title, text_auto=show_labels,
                opacity=opacity,
            )

        # ---------------------------------------------------------------------
        # 4. Stacked Bar Chart
        # ---------------------------------------------------------------------
        elif chart_type == "Stacked Bar Chart":
            actual_y = "Count" if agg_method == "count" else y_var
            c_col = color_var or group_var
            fig = px.bar(
                plot_df, x=x_var, y=actual_y, color=c_col,
                barmode="stack", color_discrete_sequence=palette,
                title=title, text_auto=show_labels,
                opacity=opacity,
            )

        # ---------------------------------------------------------------------
        # 5. Line Chart
        # ---------------------------------------------------------------------
        elif chart_type == "Line Chart":
            actual_y = "Count" if agg_method == "count" else y_var
            plot_df = plot_df.sort_values(x_var)
            fig = px.line(
                plot_df, x=x_var, y=actual_y, color=color_var,
                color_discrete_sequence=palette,
                markers=True, title=title,
            )
            fig.update_traces(line=dict(width=line_width))

        # ---------------------------------------------------------------------
        # 6. Area Chart
        # ---------------------------------------------------------------------
        elif chart_type == "Area Chart":
            actual_y = "Count" if agg_method == "count" else y_var
            plot_df = plot_df.sort_values(x_var)
            fig = px.area(
                plot_df, x=x_var, y=actual_y, color=color_var,
                color_discrete_sequence=palette,
                title=title,
            )

        # ---------------------------------------------------------------------
        # 7. Scatter Plot
        # ---------------------------------------------------------------------
        elif chart_type == "Scatter Plot":
            hover = ["Name"] if "Name" in plot_df.columns else None
            trend = "ols" if show_trendline else None
            # Check statsmodels for trendline
            has_sm = False
            if trend:
                try:
                    import statsmodels  # noqa: F401
                    has_sm = True
                except ImportError:
                    has_sm = False

            fig = px.scatter(
                plot_df, x=x_var, y=y_var, color=color_var,
                color_discrete_sequence=palette,
                hover_name="Name" if "Name" in plot_df.columns else None,
                hover_data=hover, opacity=opacity,
                trendline=trend if has_sm else None,
                title=title,
            )
            fig.update_traces(marker=dict(size=marker_size))

            # Numpy trendline fallback if requested but statsmodels is absent
            if show_trendline and not has_sm and x_var and y_var:
                clean_xy = plot_df[[x_var, y_var]].dropna()
                if len(clean_xy) >= 2 and pd.api.types.is_numeric_dtype(clean_xy[x_var]) and pd.api.types.is_numeric_dtype(clean_xy[y_var]):
                    try:
                        m, b = np.polyfit(clean_xy[x_var], clean_xy[y_var], 1)
                        x_line = np.array([clean_xy[x_var].min(), clean_xy[x_var].max()])
                        y_line = m * x_line + b
                        fig.add_trace(go.Scatter(
                            x=x_line, y=y_line, mode="lines",
                            name="Linear Fit",
                            line=dict(color="#B89248", dash="dash", width=2),
                        ))
                    except Exception:
                        pass

        # ---------------------------------------------------------------------
        # 8. Bubble Chart
        # ---------------------------------------------------------------------
        elif chart_type == "Bubble Chart":
            hover = ["Name"] if "Name" in plot_df.columns else None
            fig = px.scatter(
                plot_df, x=x_var, y=y_var, size=size_var, color=color_var,
                color_discrete_sequence=palette,
                hover_name="Name" if "Name" in plot_df.columns else None,
                hover_data=hover, opacity=opacity,
                size_max=35, title=title,
            )

        # ---------------------------------------------------------------------
        # 9. Histogram
        # ---------------------------------------------------------------------
        elif chart_type == "Histogram":
            nbins = custom.get("nbins", 30)
            fig = px.histogram(
                plot_df, x=x_var, color=color_var,
                nbins=nbins, color_discrete_sequence=palette,
                opacity=opacity, title=title,
            )
            fig.update_traces(marker_line_color=COLORS["card"], marker_line_width=1)

        # ---------------------------------------------------------------------
        # 10. Box Plot
        # ---------------------------------------------------------------------
        elif chart_type == "Box Plot":
            fig = px.box(
                plot_df, x=x_var, y=y_var, color=color_var,
                color_discrete_sequence=palette, title=title,
            )

        # ---------------------------------------------------------------------
        # 11. Violin Plot
        # ---------------------------------------------------------------------
        elif chart_type == "Violin Plot":
            fig = px.violin(
                plot_df, x=x_var, y=y_var, color=color_var,
                box=True, points="outliers",
                color_discrete_sequence=palette, title=title,
            )

        # ---------------------------------------------------------------------
        # 12. Pie Chart
        # ---------------------------------------------------------------------
        elif chart_type == "Pie Chart":
            val_col = "Count" if "Count" in plot_df.columns else y_var
            if not val_col:
                pie_counts = plot_df[x_var].value_counts().reset_index()
                pie_counts.columns = [x_var, "Count"]
                plot_df = pie_counts.head(15)
                val_col = "Count"
            fig = px.pie(
                plot_df, names=x_var, values=val_col,
                color_discrete_sequence=palette, title=title,
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")

        # ---------------------------------------------------------------------
        # 13. Donut Chart
        # ---------------------------------------------------------------------
        elif chart_type == "Donut Chart":
            val_col = "Count" if "Count" in plot_df.columns else y_var
            if not val_col:
                pie_counts = plot_df[x_var].value_counts().reset_index()
                pie_counts.columns = [x_var, "Count"]
                plot_df = pie_counts.head(15)
                val_col = "Count"
            fig = px.pie(
                plot_df, names=x_var, values=val_col, hole=0.45,
                color_discrete_sequence=palette, title=title,
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")

        # ---------------------------------------------------------------------
        # 14. Heatmap (2D Density or Pivot)
        # ---------------------------------------------------------------------
        elif chart_type == "Heatmap":
            if x_var and y_var:
                if pd.api.types.is_numeric_dtype(plot_df[x_var]) and pd.api.types.is_numeric_dtype(plot_df[y_var]):
                    fig = px.density_heatmap(
                        plot_df, x=x_var, y=y_var, nbinsx=25, nbinsy=25,
                        color_continuous_scale=[[0, "#F7F8F4"], [0.5, "#78947A"], [1, "#476B52"]],
                        title=title,
                    )
                else:
                    # Categorical 2D pivot
                    crosstab = pd.crosstab(plot_df[x_var], plot_df[y_var])
                    fig = go.Figure(data=go.Heatmap(
                        z=crosstab.values,
                        x=crosstab.columns.tolist(),
                        y=crosstab.index.tolist(),
                        colorscale=[[0, "#F7F8F4"], [0.5, "#78947A"], [1, "#476B52"]],
                    ))

        # ---------------------------------------------------------------------
        # 15. Correlation Heatmap
        # ---------------------------------------------------------------------
        elif chart_type == "Correlation Heatmap":
            num_cols, _ = get_column_types(plot_df)
            selected_nums = [c for c in ["Score", "Rank", "TLR", "RPC", "GO", "OI", "Perception"] if c in num_cols]
            if len(selected_nums) < 2:
                selected_nums = num_cols[:8]
            corr = plot_df[selected_nums].corr(method="pearson").round(2)
            fig = go.Figure(data=go.Heatmap(
                z=corr.values,
                x=corr.columns.tolist(),
                y=corr.index.tolist(),
                colorscale=[[0, "#E8D5A8"], [0.5, "#F7F8F4"], [1, "#476B52"]],
                text=corr.values,
                texttemplate="%{text}",
                textfont=dict(size=11),
            ))
            plot_df = corr

        # ---------------------------------------------------------------------
        # 16. Radar Chart
        # ---------------------------------------------------------------------
        elif chart_type == "Radar Chart":
            pillars = [p for p in ["TLR", "RPC", "GO", "OI", "Perception"] if p in plot_df.columns]
            if not pillars:
                num_cols, _ = get_column_types(plot_df)
                pillars = num_cols[:5]

            means = [float(plot_df[p].mean()) for p in pillars]
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=means + [means[0]],
                theta=pillars + [pillars[0]],
                fill="toself",
                fillcolor="rgba(71, 107, 82, 0.2)",
                line=dict(color=COLORS["primary"], width=2),
                name="Average Profile",
            ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, gridcolor="#EBF0E6"),
                    angularaxis=dict(gridcolor="#EBF0E6"),
                    bgcolor="rgba(0,0,0,0)",
                ),
            )
            plot_df = pd.DataFrame({"Parameter": pillars, "Average_Score": means})

        # ---------------------------------------------------------------------
        # 17. Treemap
        # ---------------------------------------------------------------------
        elif chart_type == "Treemap":
            path_cols = [x_var]
            if group_var and group_var != x_var and group_var in plot_df.columns:
                path_cols.append(group_var)
            elif color_var and color_var != x_var and color_var in plot_df.columns:
                path_cols.append(color_var)

            val_col = "Count" if "Count" in plot_df.columns else y_var
            fig = px.treemap(
                plot_df, path=path_cols, values=val_col,
                color=val_col if val_col and pd.api.types.is_numeric_dtype(plot_df[val_col]) else None,
                color_continuous_scale=[[0, "#EFF2EA"], [1, "#476B52"]],
                title=title,
            )

        # ---------------------------------------------------------------------
        # 18. Sunburst Chart
        # ---------------------------------------------------------------------
        elif chart_type == "Sunburst Chart":
            path_cols = [x_var]
            if group_var and group_var != x_var and group_var in plot_df.columns:
                path_cols.append(group_var)
            elif color_var and color_var != x_var and color_var in plot_df.columns:
                path_cols.append(color_var)

            val_col = "Count" if "Count" in plot_df.columns else y_var
            fig = px.sunburst(
                plot_df, path=path_cols, values=val_col,
                color=val_col if val_col and pd.api.types.is_numeric_dtype(plot_df[val_col]) else None,
                color_continuous_scale=[[0, "#EFF2EA"], [1, "#476B52"]],
                title=title,
            )

    except Exception as e:
        return None, plot_df, f"Error generating {chart_type}: {str(e)}"

    if fig:
        fig = _apply_layout(fig, title=title, height=height)
        if not show_legend:
            fig.update_layout(showlegend=False)

        # Custom Axis Titles
        x_title = custom.get("x_title")
        y_title = custom.get("y_title")
        if x_title:
            fig.update_xaxes(title=x_title)
        if y_title:
            fig.update_yaxes(title=y_title)

    return fig, plot_df, None
