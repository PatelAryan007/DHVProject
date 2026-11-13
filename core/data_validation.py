"""
NIRF Insight — Data Validation Module
=====================================
Comprehensive data validation, schema enforcement, range checks,
duplicate detection, and data integrity diagnostics for the NIRF dataset.
"""

from typing import Any
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Constants & Constraints
# ---------------------------------------------------------------------------

EXPECTED_COLUMNS = [
    "Year",
    "Category",
    "Institute_ID",
    "Name",
    "City",
    "State",
    "Score",
    "Rank",
    "TLR",
    "RPC",
    "GO",
    "OI",
    "Perception",
]

NUMERIC_PARAMETER_COLUMNS = ["TLR", "RPC", "GO", "OI", "Perception"]

VALID_YEAR_RANGE = (2017, 2025)
VALID_SCORE_RANGE = (0.0, 100.0)
VALID_PARAM_RANGE = (0.0, 100.0)

# Categories where NIRF intentionally publishes ranks without score parameters
NO_SCORE_CATEGORIES = [
    "Innovation",
    "SDGInstitutions",
    "SDG Institutions",
    "OPENUNIVERSITY",
    "Open University",
    "SKILLUNIVERSITY",
    "Skill University",
]


# ---------------------------------------------------------------------------
# Validation Functions
# ---------------------------------------------------------------------------

def validate_schema(df: pd.DataFrame) -> dict[str, Any]:
    """Validate that all expected columns exist in the DataFrame.

    Returns a dict with status, missing_columns, extra_columns, and total_columns.
    """
    if df is None or df.empty:
        return {
            "is_valid": False,
            "error": "Dataset is empty or None.",
            "missing_columns": EXPECTED_COLUMNS,
            "extra_columns": [],
            "present_columns": [],
        }

    present = df.columns.tolist()
    missing = [c for c in EXPECTED_COLUMNS if c not in present]
    extra = [c for c in present if c not in EXPECTED_COLUMNS and not c.endswith("_Raw") and not c.endswith("_Clean")]

    return {
        "is_valid": len(missing) == 0,
        "missing_columns": missing,
        "extra_columns": extra,
        "present_columns": present,
        "total_columns": len(present),
    }


def validate_ranges(df: pd.DataFrame) -> dict[str, Any]:
    """Check range integrity of numeric columns (Year, Score, Rank, Parameters)."""
    issues = []
    summary: dict[str, Any] = {}

    # Year validation
    if "Year" in df.columns:
        year_num = pd.to_numeric(df["Year"], errors="coerce")
        invalid_years = df[
            (year_num < VALID_YEAR_RANGE[0]) | (year_num > VALID_YEAR_RANGE[1])
        ]
        summary["years_found"] = sorted(year_num.dropna().unique().astype(int).tolist())
        summary["invalid_year_count"] = len(invalid_years)
        if len(invalid_years) > 0:
            issues.append(f"Found {len(invalid_years)} records with Year outside {VALID_YEAR_RANGE}.")

    # Score validation
    score_col = "Score_Clean" if "Score_Clean" in df.columns else "Score"
    if score_col in df.columns:
        score_num = pd.to_numeric(df[score_col], errors="coerce")
        out_of_range_score = df[(score_num < VALID_SCORE_RANGE[0]) | (score_num > VALID_SCORE_RANGE[1])]
        summary["score_min"] = float(score_num.min()) if score_num.notna().any() else None
        summary["score_max"] = float(score_num.max()) if score_num.notna().any() else None
        summary["out_of_range_scores"] = len(out_of_range_score)
        if len(out_of_range_score) > 0:
            issues.append(f"Found {len(out_of_range_score)} scores outside [0, 100].")

    # Rank validation
    rank_col = "Rank_Clean" if "Rank_Clean" in df.columns else "Rank"
    if rank_col in df.columns:
        rank_num = pd.to_numeric(df[rank_col], errors="coerce")
        non_positive_ranks = df[rank_num <= 0]
        summary["rank_min"] = int(rank_num.min()) if rank_num.notna().any() else None
        summary["rank_max"] = int(rank_num.max()) if rank_num.notna().any() else None
        summary["non_positive_ranks"] = len(non_positive_ranks)
        if len(non_positive_ranks) > 0:
            issues.append(f"Found {len(non_positive_ranks)} ranks <= 0.")

    # Parameters validation
    param_issues = {}
    for p in NUMERIC_PARAMETER_COLUMNS:
        col = f"{p}_Clean" if f"{p}_Clean" in df.columns else p
        if col in df.columns:
            p_num = pd.to_numeric(df[col], errors="coerce")
            invalid = df[(p_num < VALID_PARAM_RANGE[0]) | (p_num > VALID_PARAM_RANGE[1])]
            param_issues[p] = {
                "min": float(p_num.min()) if p_num.notna().any() else None,
                "max": float(p_num.max()) if p_num.notna().any() else None,
                "out_of_range": len(invalid),
            }
            if len(invalid) > 0:
                issues.append(f"Parameter {p} has {len(invalid)} values outside [0, 100].")
    summary["parameters"] = param_issues

    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "summary": summary,
    }


def validate_duplicates(df: pd.DataFrame) -> dict[str, Any]:
    """Detect exact duplicates and composite key collisions.

    Key composite: (Year, Category, Institute_ID) should uniquely identify a record.
    Secondary check: (Year, Category, Name) - multiple campuses or institute names.
    """
    if df is None or df.empty:
        return {"exact_duplicates": 0, "id_collisions": 0, "name_collisions": 0}

    exact_dup = int(df.duplicated().sum())

    id_collisions = 0
    if all(c in df.columns for c in ["Year", "Category", "Institute_ID"]):
        id_collisions = int(df.duplicated(subset=["Year", "Category", "Institute_ID"]).sum())

    name_collisions = 0
    if all(c in df.columns for c in ["Year", "Category", "Name"]):
        name_collisions = int(df.duplicated(subset=["Year", "Category", "Name"]).sum())

    return {
        "exact_duplicates": exact_dup,
        "id_collisions": id_collisions,
        "name_collisions": name_collisions,
        "has_collisions": id_collisions > 0,
    }


def validate_missingness(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze missing values and distinguish between genuine missingness

    and NIRF No-Score Categories (e.g. Innovation, SDG, Skill, Open University).
    """
    if df is None or df.empty:
        return {}

    missing_counts = df.isnull().sum().to_dict()
    total = len(df)

    # Classify missingness
    cat_col = "Category" if "Category" in df.columns else "Category_Clean"
    expected_missing = 0
    withdrawn_missing = 0

    if cat_col in df.columns:
        expected_mask = df[cat_col].isin(NO_SCORE_CATEGORIES)
        expected_missing = int(expected_mask.sum())

    if "Score" in df.columns:
        withdrawn_mask = df["Score"].astype(str).str.contains("withdrawn", case=False, na=False)
        withdrawn_missing = int(withdrawn_mask.sum())

    return {
        "missing_counts": missing_counts,
        "missing_percentages": {k: round(v / total * 100, 2) for k, v in missing_counts.items()},
        "expected_no_score_categories": expected_missing,
        "withdrawn_records": withdrawn_missing,
        "total_records": total,
    }


def generate_data_quality_report(df: pd.DataFrame) -> dict[str, Any]:
    """Generate a comprehensive audit and data quality report for the dataset."""
    if df is None or df.empty:
        return {"error": "Dataset is unavailable"}

    schema_rep = validate_schema(df)
    range_rep = validate_ranges(df)
    dup_rep = validate_duplicates(df)
    missing_rep = validate_missingness(df)

    # Dimensional coverage
    years = sorted(df["Year"].dropna().unique().astype(int).tolist()) if "Year" in df.columns else []
    categories = sorted(df["Category"].dropna().unique().tolist()) if "Category" in df.columns else []
    states = sorted(df["State"].dropna().unique().tolist()) if "State" in df.columns else []
    n_institutions = df["Name"].nunique() if "Name" in df.columns else 0
    n_institute_ids = df["Institute_ID"].nunique() if "Institute_ID" in df.columns else 0

    # Overall health score (out of 100)
    deductions = 0
    if not schema_rep["is_valid"]:
        deductions += 30
    if dup_rep["id_collisions"] > 0:
        deductions += 20
    if range_rep["summary"].get("out_of_range_scores", 0) > 0:
        deductions += 15
    if len(range_rep["issues"]) > 0:
        deductions += 10

    quality_score = max(0, 100 - deductions)

    return {
        "quality_score": quality_score,
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "schema": schema_rep,
        "ranges": range_rep,
        "duplicates": dup_rep,
        "missingness": missing_rep,
        "dimensions": {
            "years_count": len(years),
            "years": years,
            "categories_count": len(categories),
            "categories": categories,
            "states_count": len(states),
            "states": states,
            "unique_institutions": n_institutions,
            "unique_institute_ids": n_institute_ids,
        },
    }
