"""
NIRF Insight — Data Preprocessing Module
========================================
Comprehensive preprocessing pipeline, value standardization, type casting,
missingness handling, and filtering/aggregation utilities.
"""

from typing import Any
import pandas as pd
import numpy as np

from core.data_validation import NO_SCORE_CATEGORIES

# ---------------------------------------------------------------------------
# Standardization Dictionaries
# ---------------------------------------------------------------------------

STATE_STANDARDIZATION_MAP = {
    "jammu and kashmir": "Jammu and Kashmir",
    "jammu & kashmir": "Jammu and Kashmir",
    "pondicherry": "Puducherry",
    "puducherry": "Puducherry",
    "delhi": "Delhi",
    "nct of delhi": "Delhi",
    "orissa": "Odisha",
    "odisha": "Odisha",
}

CATEGORY_STANDARDIZATION_MAP = {
    "STATEPUBLICUNIVERSITY": "State Public University",
    "OPENUNIVERSITY": "Open University",
    "SKILLUNIVERSITY": "Skill University",
    "SDGInstitutions": "SDG Institutions",
    "State Public University": "State Public University",
    "Open University": "Open University",
    "Skill University": "Skill University",
    "SDG Institutions": "SDG Institutions",
}

NUMERIC_COLUMNS = ["Score", "Rank", "TLR", "RPC", "GO", "OI", "Perception"]


# ---------------------------------------------------------------------------
# Atomic Cleaning Helpers
# ---------------------------------------------------------------------------

def clean_string_value(val: Any) -> str:
    """Trim whitespace and collapse internal duplicate spaces."""
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    if val_str.lower() in ("nan", "none", "null", "n/a", "-"):
        return ""
    # Collapse multiple spaces
    return " ".join(val_str.split())


def standardize_state_name(state: Any) -> str:
    """Standardize state name casing and known historical variations."""
    cleaned = clean_string_value(state)
    if not cleaned:
        return "Unknown"
    lower = cleaned.lower()
    return STATE_STANDARDIZATION_MAP.get(lower, cleaned)


def standardize_category_name(cat: Any) -> str:
    """Standardize category naming (e.g. STATEPUBLICUNIVERSITY -> State Public University)."""
    cleaned = clean_string_value(cat)
    if not cleaned:
        return "Unknown"
    return CATEGORY_STANDARDIZATION_MAP.get(cleaned, cleaned)


def parse_rank_value(rank_val: Any) -> tuple[int | None, bool, bool]:
    """Parse rank value into (clean_numeric_rank, is_tied_rank, is_withdrawn).

    Examples:
        '1' -> (1, False, False)
        '21A' -> (21, True, False)
        'Rank Withdrawn' -> (None, False, True)
    """
    if pd.isna(rank_val):
        return None, False, False

    rank_str = str(rank_val).strip()
    if "withdrawn" in rank_str.lower():
        return None, False, True

    # Check for letter suffixes like 21A, 26A
    is_tied = False
    digits = ""
    for char in rank_str:
        if char.isdigit():
            digits += char
        elif char.isalpha():
            is_tied = True

    if digits:
        try:
            return int(digits), is_tied, False
        except ValueError:
            return None, is_tied, False

    return None, False, False


def parse_score_value(score_val: Any) -> tuple[float | None, bool]:
    """Parse score value into (clean_numeric_score, is_withdrawn)."""
    if pd.isna(score_val):
        return None, False

    score_str = str(score_val).strip()
    if "withdrawn" in score_str.lower():
        return None, True

    try:
        val = float(score_str)
        return val, False
    except ValueError:
        return None, False


# ---------------------------------------------------------------------------
# Complete Preprocessing Pipeline
# ---------------------------------------------------------------------------

def run_preprocessing_pipeline(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Execute the full data cleaning, normalization, and feature enrichment pipeline.

    Maintains raw columns with '_Raw' suffix, generates clean typed columns,
    and returns a tuple of (clean_df, audit_log).
    """
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(), {"error": "Empty DataFrame provided"}

    df = raw_df.copy()
    audit: dict[str, Any] = {
        "initial_rows": len(df),
        "initial_columns": len(df.columns),
        "modifications": [],
    }

    # 1. Preserve Raw Values
    for col in ["Year", "Category", "Institute_ID", "Name", "City", "State", "Score", "Rank"]:
        if col in df.columns and f"{col}_Raw" not in df.columns:
            df[f"{col}_Raw"] = df[col].copy()

    # 2. String Cleaning
    str_cols = ["Name", "City", "State", "Category", "Institute_ID"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_string_value)

    # 3. Standardization: State & Category
    if "State" in df.columns:
        original_states = df["State"].copy()
        df["State"] = df["State"].apply(standardize_state_name)
        state_changes = (original_states != df["State"]).sum()
        audit["state_names_standardized"] = int(state_changes)
        if state_changes > 0:
            audit["modifications"].append(f"Standardized {state_changes} state names (e.g. Jammu & Kashmir).")

    if "Category" in df.columns:
        original_cats = df["Category"].copy()
        df["Category"] = df["Category"].apply(standardize_category_name)
        cat_changes = (original_cats != df["Category"]).sum()
        audit["category_names_standardized"] = int(cat_changes)
        if cat_changes > 0:
            audit["modifications"].append(f"Standardized {cat_changes} category names (e.g. State Public University).")

    # 4. Year Conversion
    if "Year" in df.columns:
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")

    # 5. Rank Parsing
    if "Rank" in df.columns:
        rank_parsed = df["Rank"].apply(parse_rank_value)
        df["Rank"] = [p[0] for p in rank_parsed]
        df["Is_Tied_Rank"] = [p[1] for p in rank_parsed]
        tied_count = int(df["Is_Tied_Rank"].sum())
        audit["tied_ranks_detected"] = tied_count
        if tied_count > 0:
            audit["modifications"].append(f"Processed {tied_count} tied ranks (e.g. 21A) to numeric rank.")

    # 6. Score & Parameter Parsing
    if "Score" in df.columns:
        score_parsed = df["Score"].apply(parse_score_value)
        df["Score"] = [p[0] for p in score_parsed]
        is_score_withdrawn = [p[1] for p in score_parsed]
    else:
        is_score_withdrawn = [False] * len(df)

    is_rank_withdrawn = [p[2] for p in rank_parsed] if "Rank" in df.columns else [False] * len(df)
    df["Is_Withdrawn"] = [r or s for r, s in zip(is_rank_withdrawn, is_score_withdrawn)]
    withdrawn_count = int(df["Is_Withdrawn"].sum())
    audit["withdrawn_records"] = withdrawn_count

    # Parameter numeric conversion
    for p in ["TLR", "RPC", "GO", "OI", "Perception"]:
        if p in df.columns:
            df[p] = pd.to_numeric(df[p], errors="coerce")

    # 7. Classify Data Availability
    def classify_row(row):
        if row.get("Is_Withdrawn", False):
            return "Withdrawn"
        cat = row.get("Category", "")
        if cat in NO_SCORE_CATEGORIES or cat in CATEGORY_STANDARDIZATION_MAP.values():
            if pd.isna(row.get("Score")):
                return "Rank Only (No Published Parameters)"
        if pd.isna(row.get("Score")) or pd.isna(row.get("TLR")):
            return "Incomplete Parameters"
        return "Full Parameters"

    df["Data_Availability"] = df.apply(classify_row, axis=1)
    availability_dist = df["Data_Availability"].value_counts().to_dict()
    audit["data_availability_breakdown"] = availability_dist

    audit["final_rows"] = len(df)
    audit["final_columns"] = len(df.columns)
    audit["status"] = "Success"

    return df, audit


# ---------------------------------------------------------------------------
# Existing Helpers (Preserved from Phase 1)
# ---------------------------------------------------------------------------

def filter_data(
    df: pd.DataFrame,
    year=None,
    category=None,
    state=None,
    name_search: str | None = None,
    data_availability: str | None = None,
) -> pd.DataFrame:
    """Return a filtered copy of *df*. Pass ``None`` or ``'All'`` to skip a filter."""
    if df is None or df.empty:
        return df

    filtered = df.copy()

    if year is not None and str(year) != "All":
        filtered = filtered[filtered["Year"] == int(year)]

    if category is not None and str(category) != "All":
        filtered = filtered[filtered["Category"] == category]

    if state is not None and str(state) != "All":
        filtered = filtered[filtered["State"] == state]

    if data_availability and data_availability != "All":
        if "Data_Availability" in filtered.columns:
            filtered = filtered[filtered["Data_Availability"] == data_availability]

    if name_search and name_search.strip():
        filtered = filtered[
            filtered["Name"].str.contains(name_search.strip(), case=False, na=False)
        ]

    return filtered


def get_unique_values(df: pd.DataFrame, column: str, sort: bool = True) -> list:
    """Return unique non-null values from *column*."""
    if df is None or column not in df.columns:
        return []
    values = df[column].dropna().unique().tolist()
    if sort:
        try:
            values = sorted(values)
        except TypeError:
            values = sorted(values, key=str)
    return values


def get_available_years(df):
    return get_unique_values(df, "Year")


def get_available_categories(df):
    return get_unique_values(df, "Category")


def get_available_states(df):
    return get_unique_values(df, "State")


def get_available_cities(df):
    return get_unique_values(df, "City")


_AGG_FUNCS = {
    "mean": "mean",
    "median": "median",
    "sum": "sum",
    "count": "count",
    "min": "min",
    "max": "max",
    "std": "std",
}


def aggregate_data(
    df: pd.DataFrame,
    group_by: str | list[str],
    agg_column: str,
    agg_method: str = "mean",
) -> pd.DataFrame:
    """Group *df* by *group_by* and aggregate *agg_column*."""
    if df is None or df.empty or agg_column not in df.columns:
        return pd.DataFrame()

    func = _AGG_FUNCS.get(agg_method, "mean")

    if isinstance(group_by, str):
        group_by = [group_by]

    for g in group_by:
        if g not in df.columns:
            return pd.DataFrame()

    try:
        result = df.groupby(group_by, dropna=False)[agg_column].agg(func).reset_index()
        result.columns = [*group_by, agg_column]
        return result
    except Exception:
        return pd.DataFrame()


def get_missing_value_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Return a detailed table with missing-value counts per column."""
    if df is None or df.empty:
        return pd.DataFrame()

    return pd.DataFrame({
        "Column": df.columns,
        "Missing": df.isnull().sum().values,
        "Total": len(df),
        "Missing %": (df.isnull().sum().values / len(df) * 100).round(2),
        "Data Type": df.dtypes.astype(str).values,
    })
