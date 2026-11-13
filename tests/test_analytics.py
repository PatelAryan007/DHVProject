"""
Tests for core.analytics
========================
Covers descriptive statistics, five-number summary, time-series trends,
correlations, outlier detection (IQR, Z-Score), and parameter profiles.
"""

import pytest
import pandas as pd
import numpy as np

from core.analytics import (
    get_dataset_kpis,
    get_five_number_summary,
    get_top_institutions,
    get_yearly_trend,
    calculate_correlation,
    get_correlation_matrix,
    detect_outliers_iqr,
    detect_outliers_zscore,
    get_rank_mobility,
    get_consistent_top_performers,
    get_parameter_correlations_with_score,
)


@pytest.fixture
def sample_analytics_df():
    data = []
    # Generate 5 institutions over 3 years
    for yr in [2021, 2022, 2023]:
        for i, name in enumerate(["IIT A", "IIT B", "IIT C", "Univ D", "Univ E"]):
            data.append({
                "Year": yr,
                "Category": "Overall",
                "Institute_ID": f"ID-{i}",
                "Name": name,
                "State": "State X" if i < 3 else "State Y",
                "Score": 90.0 - i * 10.0 + (yr - 2021),
                "Rank": i + 1,
                "TLR": 85.0 - i * 5.0,
                "RPC": 80.0 - i * 8.0,
                "GO": 75.0 - i * 4.0,
                "OI": 70.0 - i * 3.0,
                "Perception": 65.0 - i * 6.0,
            })
    return pd.DataFrame(data)


def test_get_dataset_kpis(sample_analytics_df):
    kpis = get_dataset_kpis(sample_analytics_df)
    assert kpis["total_records"] == 15
    assert kpis["unique_institutions"] == 5
    assert kpis["avg_score"] is not None


def test_get_five_number_summary(sample_analytics_df):
    summary = get_five_number_summary(sample_analytics_df, "Score")
    assert summary["count"] == 15
    assert summary["min"] < summary["max"]
    assert summary["median"] is not None
    assert summary["iqr"] >= 0


def test_get_top_institutions(sample_analytics_df):
    top = get_top_institutions(sample_analytics_df, n=3, by="Score", year=2023)
    assert len(top) == 3
    assert top.iloc[0]["Name"] == "IIT A"


def test_get_yearly_trend(sample_analytics_df):
    trend = get_yearly_trend(sample_analytics_df, metric="Score")
    assert len(trend) == 3
    assert "Year" in trend.columns and "Score" in trend.columns


def test_calculate_correlation(sample_analytics_df):
    corr, n, desc = calculate_correlation(sample_analytics_df, "Score", "RPC")
    assert corr is not None
    assert corr > 0.8  # Strong positive
    assert n == 15
    assert "Strong" in desc


def test_get_correlation_matrix(sample_analytics_df):
    matrix = get_correlation_matrix(sample_analytics_df, ["Score", "TLR", "RPC"])
    assert matrix.shape == (3, 3)
    assert matrix.loc["Score", "Score"] == 1.0


def test_detect_outliers_iqr():
    # Synthetic series with 1 extreme outlier
    df = pd.DataFrame({"Score": [50.0, 51.0, 52.0, 49.0, 50.5, 48.5, 51.5, 99.0]})
    outliers, diag = detect_outliers_iqr(df, "Score", factor=1.5)
    assert diag["outlier_count"] == 1
    assert outliers.iloc[0]["Score"] == 99.0


def test_detect_outliers_zscore():
    # Synthetic series with 1 extreme outlier
    df = pd.DataFrame({"Score": [50.0] * 30 + [120.0]})
    outliers, diag = detect_outliers_zscore(df, "Score", threshold=3.0)
    assert diag["outlier_count"] >= 1


def test_get_rank_mobility(sample_analytics_df):
    mobility = get_rank_mobility(sample_analytics_df, category="Overall", min_years=2)
    assert len(mobility) == 5
    assert "rank_volatility" in mobility.columns


def test_get_consistent_top_performers(sample_analytics_df):
    perf = get_consistent_top_performers(sample_analytics_df, top_n=2, category="Overall")
    assert len(perf) == 2
    assert all(perf["is_always_top_n"])


def test_get_parameter_correlations_with_score(sample_analytics_df):
    param_corr = get_parameter_correlations_with_score(sample_analytics_df)
    assert len(param_corr) == 5
    assert "Pearson_r" in param_corr.columns
