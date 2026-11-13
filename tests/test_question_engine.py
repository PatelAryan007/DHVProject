"""
NIRF Insight — Question Execution Engine Automated Test Suite
=============================================================
Tests all 40 questions across all 8 analytical domains using both
mock data and the live cleaned NIRF dataset.
"""

import pytest
import pandas as pd
from questions.question_config import (
    QUESTION_DOMAINS,
    get_all_questions,
    get_question_by_id,
    get_domain_names,
)
from questions.question_engine import execute_question
from core.data_loader import load_data


# ---------------------------------------------------------------------------
# 1. Configuration & Registration Tests
# ---------------------------------------------------------------------------

def test_domains_and_questions_count():
    """Verify that there are exactly 8 domains, each with exactly 5 questions (total 40)."""
    assert len(QUESTION_DOMAINS) == 8, f"Expected 8 domains, got {len(QUESTION_DOMAINS)}"

    all_q = get_all_questions()
    assert len(all_q) == 40, f"Expected 40 questions, got {len(all_q)}"

    for domain_name, data in QUESTION_DOMAINS.items():
        assert len(data["questions"]) == 5, f"Domain '{domain_name}' must have exactly 5 questions."


def test_question_ids_unique_and_formatted():
    """Verify question IDs are Q1 to Q40 without duplicates."""
    all_q = get_all_questions()
    q_ids = [q["id"] for q in all_q]
    assert len(q_ids) == len(set(q_ids)), "Duplicate question IDs detected."

    expected_ids = [f"Q{i}" for i in range(1, 41)]
    assert sorted(q_ids, key=lambda x: int(x[1:])) == expected_ids


def test_get_question_by_id():
    """Verify lookup helper works for case-insensitive IDs."""
    q1 = get_question_by_id("q1")
    assert q1 is not None
    assert q1["id"] == "Q1"
    assert q1["domain"] == "Time-Series and Trend Analysis"

    q40 = get_question_by_id("Q40")
    assert q40 is not None
    assert q40["id"] == "Q40"

    assert get_question_by_id("INVALID_ID") is None


# ---------------------------------------------------------------------------
# 2. Execution Tests on Live NIRF Dataset (All 40 Questions)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def nirf_df():
    """Load cleaned dataset once for all tests."""
    df = load_data()
    assert df is not None and not df.empty, "Dataset must load successfully for tests."
    return df


@pytest.mark.parametrize("qid", [f"Q{i}" for i in range(1, 41)])
def test_all_40_questions_execute_successfully(nirf_df, qid):
    """Parametrized test executing every question from Q1 to Q40."""
    q_meta = get_question_by_id(qid)
    assert q_meta is not None, f"Question metadata missing for {qid}"

    fig, insights, table, err = execute_question(
        question_or_id=q_meta,
        df=nirf_df,
        year=2024,
        category="Overall",
        institution="Indian Institute of Technology Madras",
        comparison_years=(2023, 2024),
    )

    # Must complete without unhandled execution errors
    assert err is None, f"Execution failed for {qid}: {err}"

    # Must produce analytical insights
    assert len(insights) > 0, f"{qid} must return at least one analytical insight"

    # Must return a valid pandas DataFrame for supporting table
    assert isinstance(table, pd.DataFrame), f"{qid} must return a pandas DataFrame"


# ---------------------------------------------------------------------------
# 3. Domain-Specific Functional Verification
# ---------------------------------------------------------------------------

def test_domain1_time_series_q1_and_q2(nirf_df):
    """Verify Q1 trajectory and Q2 improvement return valid numerical comparisons."""
    fig1, insights1, table1, err1 = execute_question("Q1", nirf_df, institution="Indian Institute of Technology Madras", category="Overall")
    assert err1 is None
    assert not table1.empty
    assert "Rank" in table1.columns
    assert fig1 is not None

    fig2, insights2, table2, err2 = execute_question("Q2", nirf_df, category="Overall")
    assert err2 is None
    assert not table2.empty
    assert "Rank_Climb" in table2.columns
    assert (table2["Rank_Climb"] > 0).all()


def test_domain2_geospatial_q6_and_q9(nirf_df):
    """Verify Q6 top states count and Q9 TN vs KA comparison."""
    fig6, insights6, table6, err6 = execute_question("Q6", nirf_df, year=2024, category="Overall")
    assert err6 is None
    assert not table6.empty
    assert "Top_100_Count" in table6.columns

    fig9, insights9, table9, err9 = execute_question("Q9", nirf_df, year=2024, category="Overall")
    assert err9 is None
    assert not table9.empty
    assert set(table9["State"].unique()).issubset({"Karnataka", "Tamil Nadu"})


def test_domain4_correlation_q16_and_q18(nirf_df):
    """Verify Q16 RPC vs Score correlation and Q18 parameter ranking."""
    fig16, insights16, table16, err16 = execute_question("Q16", nirf_df, year=2024, category="Overall")
    assert err16 is None
    assert not table16.empty
    assert "RPC" in table16.columns and "Score" in table16.columns

    fig18, insights18, table18, err18 = execute_question("Q18", nirf_df, year=2024, category="Overall")
    assert err18 is None
    assert not table18.empty
    assert "Pearson_r" in table18.columns
    assert len(table18) == 5  # 5 parameters evaluated


def test_domain5_multivariate_q21_composite_ranking(nirf_df):
    """Verify Q21 composite ranking computes valid equal-weight parameter average."""
    fig21, insights21, table21, err21 = execute_question("Q21", nirf_df, year=2024, category="Overall")
    assert err21 is None
    assert len(table21) <= 5
    assert "Composite_5P" in table21.columns
    # Check that Composite_5P is sorted descending
    assert list(table21["Composite_5P"]) == sorted(table21["Composite_5P"], reverse=True)


def test_domain7_mobility_q31_and_q33(nirf_df):
    """Verify Q31 band jump and Q33 same rank band percentage."""
    fig31, insights31, table31, err31 = execute_question("Q31", nirf_df, category="Overall", comparison_years=(2023, 2024))
    assert err31 is None

    fig33, insights33, table33, err33 = execute_question("Q33", nirf_df, category="Overall", comparison_years=(2023, 2024))
    assert err33 is None
    assert not table33.empty
    assert "Percentage" in table33.columns
    assert round(table33["Percentage"].sum()) == 100


def test_domain8_outlier_detection_q36(nirf_df):
    """Verify Q36 RPC/Score outlier detection flags valid outliers."""
    fig36, insights36, table36, err36 = execute_question("Q36", nirf_df, year=2024, category="Overall")
    assert err36 is None
    assert "Is_Outlier" in table36.columns


def test_empty_dataframe_handling():
    """Verify graceful handling when dataset is empty."""
    empty_df = pd.DataFrame()
    fig, insights, table, err = execute_question("Q1", empty_df)
    assert err is not None or "empty" in insights[0].lower()
