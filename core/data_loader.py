"""
NIRF Insight — Data Loading Module
==================================
Handles loading, caching, validation, preprocessing pipeline execution,
and data quality auditing for the NIRF dataset.
"""

from typing import Any
import os
import pandas as pd
import streamlit as st

from core.data_validation import generate_data_quality_report, validate_schema
from core.preprocessing import run_preprocessing_pipeline

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CLEAN_DATA_PATH = os.path.join(DATA_DIR, "nirf_2017_2025_clean.csv")
RAW_DATA_PATH = os.path.join(DATA_DIR, "nirf_2017_2025_raw.csv")

NUMERIC_COLS = ["Score", "Rank", "TLR", "RPC", "GO", "OI", "Perception"]

EXPECTED_COLS = [
    "Year", "Category", "Institute_ID", "Name", "City", "State",
    "Score", "Rank", "TLR", "RPC", "GO", "OI", "Perception",
]


# ---------------------------------------------------------------------------
# Data Loading & Pipeline Integration
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner="Loading & Validating NIRF dataset …")
def load_data(force_reprocess: bool = False) -> pd.DataFrame | None:
    """Load the NIRF dataset. If not already processed, runs the full

    data validation and preprocessing pipeline, saves the clean CSV,
    and returns the processed DataFrame.
    """
    # 1. Determine Source Path
    source_path = None
    if os.path.exists(CLEAN_DATA_PATH) and not force_reprocess:
        source_path = CLEAN_DATA_PATH
    elif os.path.exists(RAW_DATA_PATH):
        source_path = RAW_DATA_PATH
    elif os.path.exists(CLEAN_DATA_PATH):
        source_path = CLEAN_DATA_PATH
    else:
        return None

    try:
        df = pd.read_csv(source_path)

        # Check if already processed by examining Phase 2 enrichment columns
        is_already_processed = "Data_Availability" in df.columns and "Category_Raw" in df.columns

        if not is_already_processed or force_reprocess:
            # Run complete cleaning & validation pipeline
            clean_df, audit = run_preprocessing_pipeline(df)

            # Save clean dataset
            try:
                os.makedirs(DATA_DIR, exist_ok=True)
                clean_df.to_csv(CLEAN_DATA_PATH, index=False)
            except Exception:
                pass  # Ignore file write errors if read-only

            return clean_df

        # If already processed, ensure numeric types are maintained
        for col in NUMERIC_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "Year" in df.columns:
            df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")

        return df

    except Exception as exc:
        st.error(f"Error loading dataset: {exc}")
        return None


# ---------------------------------------------------------------------------
# Summaries & Data Quality Reporting
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def get_data_quality_audit(df: pd.DataFrame | None = None) -> dict[str, Any]:
    """Return a comprehensive data quality audit report."""
    if df is None:
        df = load_data()
    if df is None or df.empty:
        return {"error": "Dataset unavailable"}
    return generate_data_quality_report(df)


def get_data_summary(df: pd.DataFrame) -> dict:
    """Return high-level summary statistics of the dataset."""
    if df is None or df.empty:
        return {}

    return {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "years": sorted([int(y) for y in df["Year"].dropna().unique()]) if "Year" in df.columns else [],
        "categories": sorted(df["Category"].dropna().unique().tolist()) if "Category" in df.columns else [],
        "states": sorted(df["State"].dropna().unique().tolist()) if "State" in df.columns else [],
        "n_institutions": df["Name"].nunique() if "Name" in df.columns else 0,
        "missing_values": df.isnull().sum().to_dict(),
        "dtypes": df.dtypes.astype(str).to_dict(),
    }


def validate_dataset(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Check dataset health; returns (is_valid, warnings)."""
    if df is None:
        return False, ["Dataset file not found at expected path."]
    if df.empty:
        return False, ["Dataset is empty."]

    schema_check = validate_schema(df)
    warnings: list[str] = []

    if not schema_check["is_valid"]:
        warnings.append(f"Missing expected columns: {', '.join(schema_check['missing_columns'])}")

    if len(df) < 100:
        warnings.append(f"Dataset contains only {len(df)} rows — unusually small.")

    return schema_check["is_valid"], warnings
