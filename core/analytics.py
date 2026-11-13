"""
NIRF Insight — Central Analytics Engine
=======================================
Comprehensive, reusable analytics functions covering descriptive statistics,
time-series trends, rank mobility, category comparisons, geospatial summaries,
parameter analysis, outlier detection, and statistical correlation.
"""

from typing import Any
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PARAMETER_COLS = ["TLR", "RPC", "GO", "OI", "Perception"]
NUMERIC_COLS = ["Score", "Rank"] + PARAMETER_COLS


# ---------------------------------------------------------------------------
# A. Descriptive & Summary Analytics
# ---------------------------------------------------------------------------

def get_dataset_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """Compute high-level descriptive KPIs for a given filtered slice."""
    if df is None or df.empty:
        return {
            "total_records": 0,
            "unique_institutions": 0,
            "categories_count": 0,
            "states_count": 0,
            "avg_score": None,
            "median_score": None,
            "min_score": None,
            "max_score": None,
        }

    score_series = df["Score"].dropna() if "Score" in df.columns else pd.Series(dtype=float)

    return {
        "total_records": len(df),
        "unique_institutions": df["Name"].nunique() if "Name" in df.columns else 0,
        "categories_count": df["Category"].nunique() if "Category" in df.columns else 0,
        "states_count": df["State"].nunique() if "State" in df.columns else 0,
        "avg_score": round(float(score_series.mean()), 2) if not score_series.empty else None,
        "median_score": round(float(score_series.median()), 2) if not score_series.empty else None,
        "min_score": round(float(score_series.min()), 2) if not score_series.empty else None,
        "max_score": round(float(score_series.max()), 2) if not score_series.empty else None,
    }


def get_five_number_summary(df: pd.DataFrame, column: str = "Score") -> dict[str, Any]:
    """Calculate the five-number summary plus Mean, Std, Variance, and IQR for a column."""
    if df is None or df.empty or column not in df.columns:
        return {}

    series = pd.to_numeric(df[column], errors="coerce").dropna()
    if series.empty:
        return {}

    q1 = float(series.quantile(0.25))
    median = float(series.quantile(0.50))
    q3 = float(series.quantile(0.75))
    iqr = q3 - q1

    return {
        "column": column,
        "count": len(series),
        "min": float(series.min()),
        "q1": round(q1, 2),
        "median": round(median, 2),
        "q3": round(q3, 2),
        "max": float(series.max()),
        "iqr": round(iqr, 2),
        "mean": round(float(series.mean()), 2),
        "std": round(float(series.std()), 2),
        "variance": round(float(series.var()), 2),
    }


def get_top_institutions(
    df: pd.DataFrame,
    n: int = 10,
    by: str = "Score",
    ascending: bool = False,
    category: str | None = None,
    year: int | None = None,
) -> pd.DataFrame:
    """Return top *n* institutions filtered by category/year, sorted by *by*."""
    if df is None or df.empty or by not in df.columns:
        return pd.DataFrame()

    filtered = df.copy()
    if category and str(category) != "All":
        filtered = filtered[filtered["Category"] == category]
    if year and str(year) != "All":
        filtered = filtered[filtered["Year"] == int(year)]

    valid = filtered.dropna(subset=[by])
    return valid.sort_values(by, ascending=ascending).head(n)


# ---------------------------------------------------------------------------
# B. Time-Series Analytics
# ---------------------------------------------------------------------------

def get_yearly_trend(
    df: pd.DataFrame,
    metric: str = "Score",
    group_by: str | None = None,
    agg: str = "mean",
) -> pd.DataFrame:
    """Compute yearly trend of a metric, optionally segmented by a categorical group."""
    if df is None or df.empty or metric not in df.columns or "Year" not in df.columns:
        return pd.DataFrame()

    clean_df = df.dropna(subset=[metric, "Year"])
    if clean_df.empty:
        return pd.DataFrame()

    if group_by and group_by in clean_df.columns:
        trend = clean_df.groupby(["Year", group_by])[metric].agg(agg).reset_index()
        trend.columns = ["Year", group_by, metric]
        return trend.sort_values("Year")

    trend = clean_df.groupby("Year")[metric].agg(agg).reset_index()
    trend.columns = ["Year", metric]
    return trend.sort_values("Year")


def get_institution_trajectory(
    df: pd.DataFrame,
    institution_name: str,
    category: str | None = None,
) -> pd.DataFrame:
    """Track the historical score and rank trajectory of a specific institution across years."""
    if df is None or df.empty or "Name" not in df.columns or "Year" not in df.columns:
        return pd.DataFrame()

    inst_df = df[df["Name"].str.lower() == institution_name.lower().strip()]
    if category and str(category) != "All":
        inst_df = inst_df[inst_df["Category"] == category]

    cols = ["Year", "Category", "Rank", "Score"] + [p for p in PARAMETER_COLS if p in inst_df.columns]
    present_cols = [c for c in cols if c in inst_df.columns]
    return inst_df[present_cols].sort_values("Year").reset_index(drop=True)


def get_rank_mobility(
    df: pd.DataFrame,
    category: str = "Overall",
    min_years: int = 3,
) -> pd.DataFrame:
    """Analyze institutional rank mobility over time within a category.

    Calculates rank volatility (std of rank), net rank change, and best rank.
    """
    if df is None or df.empty or "Rank" not in df.columns:
        return pd.DataFrame()

    sub = df[df["Category"] == category].dropna(subset=["Rank", "Year", "Name"])
    if sub.empty:
        return pd.DataFrame()

    mobility = (
        sub.groupby("Name")
        .agg(
            years_count=("Year", "nunique"),
            best_rank=("Rank", "min"),
            worst_rank=("Rank", "max"),
            avg_rank=("Rank", "mean"),
            rank_volatility=("Rank", "std"),
        )
        .reset_index()
    )

    # Filter by minimum participation years
    mobility = mobility[mobility["years_count"] >= min_years]
    mobility["rank_range"] = mobility["worst_rank"] - mobility["best_rank"]
    mobility["rank_volatility"] = mobility["rank_volatility"].round(2)
    mobility["avg_rank"] = mobility["avg_rank"].round(1)

    return mobility.sort_values("rank_volatility", ascending=False)


def get_consistent_top_performers(
    df: pd.DataFrame,
    top_n: int = 10,
    category: str = "Overall",
) -> pd.DataFrame:
    """Identify institutions that have consistently achieved Rank <= top_n across every year."""
    if df is None or df.empty:
        return pd.DataFrame()

    sub = df[df["Category"] == category].dropna(subset=["Rank", "Year", "Name"])
    if sub.empty:
        return pd.DataFrame()

    total_years = sub["Year"].nunique()
    top_records = sub[sub["Rank"] <= top_n]

    perf = (
        top_records.groupby("Name")
        .agg(
            appearances=("Year", "nunique"),
            avg_rank=("Rank", "mean"),
            best_rank=("Rank", "min"),
            worst_rank=("Rank", "max"),
        )
        .reset_index()
    )

    perf["is_always_top_n"] = perf["appearances"] == total_years
    perf["avg_rank"] = perf["avg_rank"].round(2)
    return perf.sort_values(["appearances", "avg_rank"], ascending=[False, True])


# ---------------------------------------------------------------------------
# C. Category & State Analytics
# ---------------------------------------------------------------------------

def get_category_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Count of institutions per category."""
    if df is None or df.empty or "Category" not in df.columns:
        return pd.DataFrame()
    dist = df["Category"].value_counts().reset_index()
    dist.columns = ["Category", "Count"]
    return dist


def get_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Detailed summary statistics by Category (Counts, Mean Score, Parameter Averages)."""
    if df is None or df.empty or "Category" not in df.columns:
        return pd.DataFrame()

    agg_dict: dict[str, tuple[str, str]] = {
        "Institutions": ("Name", "count"),
        "Unique_Institutes": ("Name", "nunique"),
    }

    if "Score" in df.columns:
        agg_dict["Avg_Score"] = ("Score", "mean")
        agg_dict["Median_Score"] = ("Score", "median")
        agg_dict["Min_Score"] = ("Score", "min")
        agg_dict["Max_Score"] = ("Score", "max")

    for p in PARAMETER_COLS:
        if p in df.columns:
            agg_dict[f"Avg_{p}"] = (p, "mean")

    summary = df.groupby("Category").agg(**agg_dict).reset_index()
    numeric_result_cols = [c for c in summary.columns if c != "Category"]
    summary[numeric_result_cols] = summary[numeric_result_cols].round(2)
    return summary.sort_values("Institutions", ascending=False)


def get_state_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Count of institutions per state."""
    if df is None or df.empty or "State" not in df.columns:
        return pd.DataFrame()
    dist = df["State"].value_counts().reset_index()
    dist.columns = ["State", "Count"]
    return dist


def get_state_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Detailed per-state metrics: institution counts, average scores, and top institute."""
    if df is None or df.empty or "State" not in df.columns:
        return pd.DataFrame()

    agg_dict = {
        "Institutions": ("Name", "count"),
        "Unique_Institutions": ("Name", "nunique"),
    }

    if "Score" in df.columns:
        agg_dict["Avg_Score"] = ("Score", "mean")
        agg_dict["Max_Score"] = ("Score", "max")
        agg_dict["Min_Score"] = ("Score", "min")

    summary = df.groupby("State").agg(**agg_dict).reset_index()

    if "Score" in df.columns:
        summary["Avg_Score"] = summary["Avg_Score"].round(2)
        summary["Max_Score"] = summary["Max_Score"].round(2)
        summary["Min_Score"] = summary["Min_Score"].round(2)

    return summary.sort_values("Institutions", ascending=False)


# ---------------------------------------------------------------------------
# D. Parameter Analytics
# ---------------------------------------------------------------------------

def get_parameter_profile(
    df: pd.DataFrame,
    institution_name: str,
    year: int | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """Retrieve the 5 NIRF parameter scores for a given institution."""
    if df is None or df.empty:
        return {}

    sub = df[df["Name"].str.lower() == institution_name.lower().strip()]
    if year and str(year) != "All":
        sub = sub[sub["Year"] == int(year)]
    if category and str(category) != "All":
        sub = sub[sub["Category"] == category]

    if sub.empty:
        return {}

    row = sub.iloc[0]
    profile = {p: float(row[p]) if p in row and pd.notna(row[p]) else None for p in PARAMETER_COLS}
    profile["Score"] = float(row["Score"]) if "Score" in row and pd.notna(row["Score"]) else None
    profile["Rank"] = int(row["Rank"]) if "Rank" in row and pd.notna(row["Rank"]) else None
    profile["Year"] = int(row["Year"]) if "Year" in row and pd.notna(row["Year"]) else None
    profile["Name"] = row.get("Name", institution_name)
    return profile


def get_parameter_correlations_with_score(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Pearson and Spearman correlation of each NIRF parameter with overall Score."""
    if df is None or df.empty or "Score" not in df.columns:
        return pd.DataFrame()

    rows = []
    for p in PARAMETER_COLS:
        if p in df.columns:
            valid = df[["Score", p]].dropna()
            n = len(valid)
            if n >= 3:
                pearson = float(valid["Score"].corr(valid[p], method="pearson"))
                # Spearman is Pearson correlation of ranks (no scipy dependency needed)
                spearman = float(valid["Score"].rank().corr(valid[p].rank(), method="pearson"))
                rows.append({
                    "Parameter": p,
                    "Pearson_r": round(pearson, 4),
                    "Spearman_rho": round(spearman, 4),
                    "Valid_Observations": n,
                })

    return pd.DataFrame(rows).sort_values("Pearson_r", ascending=False) if rows else pd.DataFrame()


# ---------------------------------------------------------------------------
# E. Statistical Correlation & Outlier Detection
# ---------------------------------------------------------------------------

def calculate_correlation(
    df: pd.DataFrame,
    col1: str,
    col2: str,
    method: str = "pearson",
) -> tuple[float | None, int, str]:
    """Calculate Pearson or Spearman correlation between two columns.

    Returns (correlation_coefficient, valid_sample_size, strength_interpretation).
    """
    if df is None or df.empty or col1 not in df.columns or col2 not in df.columns:
        return None, 0, "No data"

    valid = df[[col1, col2]].dropna()
    n = len(valid)
    if n < 3:
        return None, n, "Insufficient observations (n < 3)"

    if method.lower() == "spearman":
        corr = float(valid[col1].rank().corr(valid[col2].rank(), method="pearson"))
    else:
        corr = float(valid[col1].corr(valid[col2], method="pearson"))
    if np.isnan(corr):
        return None, n, "Indeterminate"

    corr_rounded = round(corr, 4)
    abs_r = abs(corr)
    if abs_r >= 0.8:
        strength = "Very Strong"
    elif abs_r >= 0.6:
        strength = "Strong"
    elif abs_r >= 0.4:
        strength = "Moderate"
    elif abs_r >= 0.2:
        strength = "Weak"
    else:
        strength = "Very Weak / None"

    direction = "positive" if corr > 0 else "negative"
    return corr_rounded, n, f"{strength} {direction}"


def get_correlation_matrix(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    method: str = "pearson",
) -> pd.DataFrame:
    """Compute correlation matrix for selected numeric columns."""
    if df is None or df.empty:
        return pd.DataFrame()

    default_cols = ["Score"] + PARAMETER_COLS
    columns = columns or default_cols
    available = [c for c in columns if c in df.columns]

    if len(available) < 2:
        return pd.DataFrame()

    return df[available].corr(method=method).round(3)


def detect_outliers_iqr(
    df: pd.DataFrame,
    column: str = "Score",
    factor: float = 1.5,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Detect statistical outliers in a numeric column using the Interquartile Range (IQR) rule.

    Outliers are points < Q1 - factor*IQR or > Q3 + factor*IQR.
    Returns (outliers_df, diagnostic_dict).
    """
    if df is None or df.empty or column not in df.columns:
        return pd.DataFrame(), {}

    series = pd.to_numeric(df[column], errors="coerce").dropna()
    if len(series) < 4:
        return pd.DataFrame(), {"error": "Insufficient data for IQR"}

    q1 = float(series.quantile(0.25))
    q3 = float(series.quantile(0.75))
    iqr = q3 - q1

    lower_bound = round(q1 - factor * iqr, 2)
    upper_bound = round(q3 + factor * iqr, 2)

    outliers_mask = (df[column] < lower_bound) | (df[column] > upper_bound)
    outliers_df = df[outliers_mask].copy()

    diagnostics = {
        "column": column,
        "q1": round(q1, 2),
        "q3": round(q3, 2),
        "iqr": round(iqr, 2),
        "factor": factor,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "total_records": len(series),
        "outlier_count": len(outliers_df),
        "outlier_percentage": round(len(outliers_df) / len(series) * 100, 2),
    }

    return outliers_df, diagnostics


def detect_outliers_zscore(
    df: pd.DataFrame,
    column: str = "Score",
    threshold: float = 3.0,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Detect outliers using standard Z-score (|Z| >= threshold)."""
    if df is None or df.empty or column not in df.columns:
        return pd.DataFrame(), {}

    series = pd.to_numeric(df[column], errors="coerce").dropna()
    if len(series) < 4 or series.std() == 0:
        return pd.DataFrame(), {"error": "Insufficient variation"}

    mean = float(series.mean())
    std = float(series.std())

    z_scores = (df[column] - mean) / std
    outliers_mask = z_scores.abs() >= threshold
    outliers_df = df[outliers_mask].copy()
    outliers_df["Z_Score"] = z_scores[outliers_mask].round(2)

    diagnostics = {
        "column": column,
        "mean": round(mean, 2),
        "std": round(std, 2),
        "threshold": threshold,
        "outlier_count": len(outliers_df),
        "outlier_percentage": round(len(outliers_df) / len(series) * 100, 2),
    }

    return outliers_df, diagnostics


# ---------------------------------------------------------------------------
# F. Analytical Highlights
# ---------------------------------------------------------------------------

def get_analytical_highlights(df: pd.DataFrame) -> list[str]:
    """Generate dynamic analytical insight bullets grounded in the filtered data."""
    if df is None or df.empty:
        return []

    highlights: list[str] = []

    # 1. Top Institution
    if "Score" in df.columns and "Name" in df.columns:
        top = df.dropna(subset=["Score"]).nlargest(1, "Score")
        if not top.empty:
            r = top.iloc[0]
            cat_info = f" ({r['Category']})" if "Category" in r else ""
            highlights.append(
                f"🏆 **Top Performer:** {r['Name']}{cat_info} with a NIRF score of **{r['Score']:.2f}**"
            )

    # 2. Average Score & Median
    if "Score" in df.columns:
        scores = df["Score"].dropna()
        if not scores.empty:
            highlights.append(
                f"📊 **Score Benchmark:** Mean = **{scores.mean():.2f}**, Median = **{scores.median():.2f}** (Score Range: {scores.min():.2f} – {scores.max():.2f})"
            )

    # 3. Top State Representation
    if "State" in df.columns:
        state_counts = df["State"].value_counts()
        if not state_counts.empty:
            top_state = state_counts.index[0]
            count = state_counts.iloc[0]
            pct = count / len(df) * 100
            highlights.append(
                f"📍 **Regional Leader:** **{top_state}** leads with **{count:,}** institutions ({pct:.1f}% of cohort)"
            )

    # 4. Outlier Detection Alert
    if "Score" in df.columns and len(df.dropna(subset=["Score"])) >= 10:
        _, diag = detect_outliers_iqr(df, "Score")
        outliers_n = diag.get("outlier_count", 0)
        if outliers_n > 0:
            highlights.append(
                f"🎯 **Statistical Outliers:** Detected **{outliers_n}** institutions with scores significantly higher than the peer IQR threshold"
            )

    # 5. Parameter Correlation Highlight
    if "Score" in df.columns and "RPC" in df.columns:
        corr, n, desc = calculate_correlation(df, "Score", "RPC")
        if corr is not None:
            highlights.append(
                f"🔬 **Research Impact:** Research (RPC) correlates strongly with overall Score (Pearson $r = {corr}$, {desc})"
            )

    return highlights
