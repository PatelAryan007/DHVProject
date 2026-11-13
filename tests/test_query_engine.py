"""
Tests for core.query_engine
===========================
Covers multi-criteria filtering, text searching, and comparative queries.
"""

import pytest
import pandas as pd

from core.query_engine import (
    apply_multi_filters,
    search_institutions,
    compare_institutions,
)


@pytest.fixture
def sample_query_df():
    return pd.DataFrame({
        "Year": [2021, 2022, 2023],
        "Category": ["Overall", "Engineering", "Overall"],
        "Institute_ID": ["IR-01", "IR-02", "IR-03"],
        "Name": ["IIT Madras", "IIT Bombay", "BITS Pilani"],
        "City": ["Chennai", "Mumbai", "Pilani"],
        "State": ["Tamil Nadu", "Maharashtra", "Rajasthan"],
        "Score": [89.5, 87.2, 70.0],
        "Rank": [1, 2, 25],
        "Is_Withdrawn": [False, False, False],
        "Data_Availability": ["Full Parameters", "Full Parameters", "Full Parameters"],
    })


def test_apply_multi_filters(sample_query_df):
    res = apply_multi_filters(sample_query_df, year=2021)
    assert len(res) == 1
    assert res.iloc[0]["Name"] == "IIT Madras"

    res_cat = apply_multi_filters(sample_query_df, category="Overall")
    assert len(res_cat) == 2

    res_score = apply_multi_filters(sample_query_df, score_range=(80.0, 95.0))
    assert len(res_score) == 2


def test_search_institutions(sample_query_df):
    res = search_institutions(sample_query_df, "IIT")
    assert len(res) == 2

    res_city = search_institutions(sample_query_df, "Pilani")
    assert len(res_city) == 1


def test_compare_institutions(sample_query_df):
    res = compare_institutions(sample_query_df, ["IIT Madras", "BITS Pilani"])
    assert len(res) == 2
