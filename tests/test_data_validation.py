"""
Tests for core.data_validation
==============================
Covers schema validation, range checks, duplicate detection, and missingness classification.
"""

import pytest
import pandas as pd
import numpy as np

from core.data_validation import (
    validate_schema,
    validate_ranges,
    validate_duplicates,
    validate_missingness,
    generate_data_quality_report,
    EXPECTED_COLUMNS,
)


@pytest.fixture
def sample_valid_df():
    return pd.DataFrame({
        "Year": [2021, 2022, 2023],
        "Category": ["Overall", "Engineering", "University"],
        "Institute_ID": ["IR-01", "IR-02", "IR-03"],
        "Name": ["IIT Madras", "IIT Bombay", "IISc Bangalore"],
        "City": ["Chennai", "Mumbai", "Bengaluru"],
        "State": ["Tamil Nadu", "Maharashtra", "Karnataka"],
        "Score": [89.5, 87.2, 85.0],
        "Rank": [1, 2, 3],
        "TLR": [90.0, 88.0, 86.0],
        "RPC": [92.0, 89.0, 87.0],
        "GO": [85.0, 84.0, 83.0],
        "OI": [75.0, 72.0, 70.0],
        "Perception": [95.0, 90.0, 88.0],
    })


def test_validate_schema_valid(sample_valid_df):
    res = validate_schema(sample_valid_df)
    assert res["is_valid"] is True
    assert len(res["missing_columns"]) == 0


def test_validate_schema_missing_column(sample_valid_df):
    dropped = sample_valid_df.drop(columns=["TLR"])
    res = validate_schema(dropped)
    assert res["is_valid"] is False
    assert "TLR" in res["missing_columns"]


def test_validate_schema_empty():
    res = validate_schema(pd.DataFrame())
    assert res["is_valid"] is False


def test_validate_ranges(sample_valid_df):
    res = validate_ranges(sample_valid_df)
    assert res["is_valid"] is True
    assert res["summary"]["score_min"] == 85.0
    assert res["summary"]["score_max"] == 89.5


def test_validate_ranges_out_of_bounds():
    df = pd.DataFrame({
        "Year": [1990],  # Out of range
        "Score": [150.0],  # Out of range
        "Rank": [-5],  # Out of range
        "TLR": [110.0],  # Out of range
    })
    res = validate_ranges(df)
    assert res["is_valid"] is False
    assert len(res["issues"]) >= 3


def test_validate_duplicates(sample_valid_df):
    res = validate_duplicates(sample_valid_df)
    assert res["exact_duplicates"] == 0
    assert res["id_collisions"] == 0
    assert res["has_collisions"] is False


def test_validate_duplicates_with_collisions(sample_valid_df):
    dup_df = pd.concat([sample_valid_df, sample_valid_df.iloc[[0]]], ignore_index=True)
    res = validate_duplicates(dup_df)
    assert res["exact_duplicates"] == 1
    assert res["id_collisions"] == 1
    assert res["has_collisions"] is True


def test_generate_data_quality_report(sample_valid_df):
    rep = generate_data_quality_report(sample_valid_df)
    assert rep["quality_score"] == 100
    assert rep["total_rows"] == 3
    assert rep["dimensions"]["years_count"] == 3
