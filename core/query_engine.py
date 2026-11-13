"""
NIRF Insight — Query Engine Module
==================================
Reusable multi-parameter query builder, slicing, search,
and comparative analytics queries across institutions and cohorts.
"""

from typing import Any
import pandas as pd
import numpy as np


def apply_multi_filters(
    df: pd.DataFrame,
    year: Any = None,
    category: Any = None,
    state: Any = None,
    city: Any = None,
    name_search: str | None = None,
    score_range: tuple[float, float] | None = None,
    rank_range: tuple[int, int] | None = None,
    exclude_withdrawn: bool = True,
    data_availability: str | None = None,
) -> pd.DataFrame:
    """Filter DataFrame across multiple analytical dimensions with input validation."""
    if df is None or df.empty:
        return pd.DataFrame()

    filtered = df.copy()

    # 1. Year Filter
    if year is not None and str(year) != "All":
        try:
            filtered = filtered[filtered["Year"] == int(year)]
        except ValueError:
            pass

    # 2. Category Filter
    if category is not None and str(category) != "All":
        filtered = filtered[filtered["Category"] == category]

    # 3. State Filter
    if state is not None and str(state) != "All":
        filtered = filtered[filtered["State"] == state]

    # 4. City Filter
    if city is not None and str(city) != "All":
        filtered = filtered[filtered["City"] == city]

    # 5. Name Search
    if name_search and name_search.strip():
        term = name_search.strip().lower()
        filtered = filtered[filtered["Name"].str.lower().str.contains(term, na=False)]

    # 6. Score Range Filter
    if score_range and "Score" in filtered.columns:
        min_s, max_s = score_range
        filtered = filtered[(filtered["Score"] >= min_s) & (filtered["Score"] <= max_s)]

    # 7. Rank Range Filter
    if rank_range and "Rank" in filtered.columns:
        min_r, max_r = rank_range
        filtered = filtered[(filtered["Rank"] >= min_r) & (filtered["Rank"] <= max_r)]

    # 8. Exclude Withdrawn
    if exclude_withdrawn and "Is_Withdrawn" in filtered.columns:
        filtered = filtered[~filtered["Is_Withdrawn"]]

    # 9. Data Availability Flag
    if data_availability and data_availability != "All" and "Data_Availability" in filtered.columns:
        filtered = filtered[filtered["Data_Availability"] == data_availability]

    return filtered


def search_institutions(
    df: pd.DataFrame,
    query: str,
    fields: list[str] | None = None,
    limit: int = 50,
) -> pd.DataFrame:
    """Search for institutions matching query across specified textual fields."""
    if df is None or df.empty or not query.strip():
        return df.head(limit) if df is not None else pd.DataFrame()

    q = query.strip().lower()
    search_fields = fields or ["Name", "Institute_ID", "City", "State"]
    valid_fields = [f for f in search_fields if f in df.columns]

    mask = pd.Series(False, index=df.index)
    for f in valid_fields:
        mask = mask | df[f].astype(str).str.lower().str.contains(q, na=False)

    return df[mask].head(limit)


def compare_institutions(
    df: pd.DataFrame,
    institution_names: list[str],
    year: int | None = None,
    category: str | None = None,
) -> pd.DataFrame:
    """Compare a list of institutions side-by-side across their parameters."""
    if df is None or df.empty or not institution_names:
        return pd.DataFrame()

    lower_names = [n.strip().lower() for n in institution_names]
    sub = df[df["Name"].str.lower().isin(lower_names)].copy()

    if year and str(year) != "All":
        sub = sub[sub["Year"] == int(year)]
    if category and str(category) != "All":
        sub = sub[sub["Category"] == category]

    cols = ["Name", "Year", "Category", "State", "Rank", "Score", "TLR", "RPC", "GO", "OI", "Perception"]
    present = [c for c in cols if c in sub.columns]
    return sub[present].sort_values(["Year", "Rank"], ascending=[False, True]).reset_index(drop=True)
