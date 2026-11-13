"""
NIRF Insight — Dynamic Chart Engine Automated Test Suite
=========================================================
Tests all 18 chart types, aggregation routines, input validation,
customization options, and export readiness using the live NIRF dataset.
"""

import pytest
import pandas as pd
import plotly.graph_objects as go

from core.data_loader import load_data
from core.dynamic_chart_engine import (
    ALL_18_CHART_TYPES,
    AGGREGATION_METHODS,
    get_column_types,
    validate_chart_inputs,
    aggregate_chart_data,
    generate_dynamic_chart,
)


@pytest.fixture(scope="module")
def nirf_df():
    """Load dataset for test execution."""
    df = load_data()
    assert df is not None and not df.empty, "Dataset must load successfully."
    return df


def test_column_types_detection(nirf_df):
    """Verify numeric and categorical column separation."""
    nums, cats = get_column_types(nirf_df)
    assert "Score" in nums
    assert "Rank" in nums
    assert "TLR" in nums
    assert "Category" in cats
    assert "State" in cats
    assert "Name" in cats


def test_all_18_chart_types_defined():
    """Verify exact count of supported chart types is 18."""
    assert len(ALL_18_CHART_TYPES) == 18


# ---------------------------------------------------------------------------
# Test Every Single Chart Type Generation (18 Chart Types)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("chart_type", ALL_18_CHART_TYPES)
def test_generate_each_chart_type(nirf_df, chart_type):
    """Verify that every one of the 18 chart types generates a valid Plotly Figure."""
    sub_df = nirf_df.head(100).copy()

    # Provide appropriate parameters based on chart type requirements
    x_var = "Category"
    y_var = "Score"
    size_var = None
    color_var = None

    if chart_type in ("Scatter Plot", "Bubble Chart"):
        x_var = "RPC"
        y_var = "Score"
        color_var = "Category"
        if chart_type == "Bubble Chart":
            size_var = "TLR"

    elif chart_type in ("Line Chart", "Area Chart"):
        x_var = "Year"
        y_var = "Score"
        color_var = "Category"

    elif chart_type in ("Histogram", "Box Plot", "Violin Plot"):
        x_var = "Category"
        y_var = "Score"

    elif chart_type in ("Pie Chart", "Donut Chart"):
        x_var = "Category"
        y_var = "Score"

    elif chart_type in ("Treemap", "Sunburst Chart"):
        x_var = "Category"
        y_var = "Score"
        color_var = "State"

    fig, out_df, err = generate_dynamic_chart(
        df=sub_df,
        chart_type=chart_type,
        x_var=x_var,
        y_var=y_var,
        size_var=size_var,
        color_var=color_var,
        customization={"title": f"Test {chart_type}", "palette": "Forest & Sage (Default)"},
    )

    assert err is None, f"{chart_type} failed with error: {err}"
    assert fig is not None, f"{chart_type} returned None figure"
    assert isinstance(fig, go.Figure), f"{chart_type} must return a plotly Figure"
    assert isinstance(out_df, pd.DataFrame), f"{chart_type} must return a pandas DataFrame"


# ---------------------------------------------------------------------------
# Test Aggregation Methods
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("agg", ["mean", "median", "sum", "count", "min", "max", "std"])
def test_aggregation_methods(nirf_df, agg):
    """Verify all statistical aggregation methods compute valid output."""
    agg_res = aggregate_chart_data(nirf_df, x_var="Category", y_var="Score", agg_method=agg)
    assert not agg_res.empty
    assert "Category" in agg_res.columns
    val_col = "Count" if agg == "count" else "Score"
    assert val_col in agg_res.columns


def test_incompatible_chart_input_handling(nirf_df):
    """Verify validation flags incompatible chart selections cleanly without raising exceptions."""
    # Bubble chart missing size_var
    valid, err = validate_chart_inputs(nirf_df, "Bubble Chart", x_var="RPC", y_var="Score", size_var=None)
    assert not valid
    assert "size" in err.lower()

    # Empty dataframe
    valid_empty, err_empty = validate_chart_inputs(pd.DataFrame(), "Bar Chart", x_var="Category", y_var="Score")
    assert not valid_empty
    assert "empty" in err_empty.lower()


def test_html_and_csv_export_readiness(nirf_df):
    """Verify that generated figures can be exported to HTML and data to CSV."""
    fig, out_df, err = generate_dynamic_chart(
        df=nirf_df.head(50),
        chart_type="Bar Chart",
        x_var="Category",
        y_var="Score",
        agg_method="mean",
    )
    assert err is None
    assert fig is not None

    # Test HTML export
    html_str = fig.to_html(include_plotlyjs="cdn")
    assert "<html" in html_str.lower() or "plotly" in html_str.lower()

    # Test CSV export
    csv_bytes = out_df.to_csv(index=False).encode("utf-8")
    assert len(csv_bytes) > 0
