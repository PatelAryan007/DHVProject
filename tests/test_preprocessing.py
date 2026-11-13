"""
Tests for core.preprocessing
============================
Covers string cleaning, state standardization, category normalization,
rank and score parsing, and data availability classification.
"""

import pytest
import pandas as pd
import numpy as np

from core.preprocessing import (
    clean_string_value,
    standardize_state_name,
    standardize_category_name,
    parse_rank_value,
    parse_score_value,
    run_preprocessing_pipeline,
    filter_data,
)


def test_clean_string_value():
    assert clean_string_value("  Indian Institute   of Technology  ") == "Indian Institute of Technology"
    assert clean_string_value("NaN") == ""
    assert clean_string_value(" - ") == ""
    assert clean_string_value(None) == ""


def test_standardize_state_name():
    assert standardize_state_name("Jammu And Kashmir") == "Jammu and Kashmir"
    assert standardize_state_name("jammu and kashmir") == "Jammu and Kashmir"
    assert standardize_state_name("Pondicherry") == "Puducherry"
    assert standardize_state_name("Delhi") == "Delhi"


def test_standardize_category_name():
    assert standardize_category_name("STATEPUBLICUNIVERSITY") == "State Public University"
    assert standardize_category_name("OPENUNIVERSITY") == "Open University"
    assert standardize_category_name("SKILLUNIVERSITY") == "Skill University"
    assert standardize_category_name("Engineering") == "Engineering"


def test_parse_rank_value():
    # Normal rank
    val, tied, withdrawn = parse_rank_value("1")
    assert val == 1 and not tied and not withdrawn

    # Tied rank
    val, tied, withdrawn = parse_rank_value("21A")
    assert val == 21 and tied and not withdrawn

    # Withdrawn rank
    val, tied, withdrawn = parse_rank_value("Rank Withdrawn")
    assert val is None and withdrawn


def test_parse_score_value():
    val, withdrawn = parse_score_value("85.50")
    assert val == 85.50 and not withdrawn

    val, withdrawn = parse_score_value("Rank Withdrawn*")
    assert val is None and withdrawn


def test_run_preprocessing_pipeline():
    raw_df = pd.DataFrame({
        "Year": ["2022", "2023"],
        "Category": ["STATEPUBLICUNIVERSITY", "Innovation"],
        "Institute_ID": ["IR-01", "IR-02"],
        "Name": [" Anna University ", "IIT Madras"],
        "City": ["Chennai ", "Chennai"],
        "State": ["Jammu And Kashmir", "Tamil Nadu"],
        "Score": ["65.40", None],
        "Rank": ["21A", "1"],
        "TLR": ["70.0", None],
        "RPC": ["50.0", None],
        "GO": ["60.0", None],
        "OI": ["55.0", None],
        "Perception": ["40.0", None],
    })

    clean_df, audit = run_preprocessing_pipeline(raw_df)

    assert clean_df["Category"].iloc[0] == "State Public University"
    assert clean_df["Category_Raw"].iloc[0] == "STATEPUBLICUNIVERSITY"
    assert clean_df["State"].iloc[0] == "Jammu and Kashmir"
    assert clean_df["Rank"].iloc[0] == 21
    assert bool(clean_df["Is_Tied_Rank"].iloc[0]) is True
    assert clean_df["Data_Availability"].iloc[0] == "Full Parameters"
    assert clean_df["Data_Availability"].iloc[1] == "Rank Only (No Published Parameters)"
    assert audit["status"] == "Success"


def test_filter_data_empty():
    res = filter_data(pd.DataFrame(), year=2020)
    assert res.empty
