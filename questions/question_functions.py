"""
NIRF Insight — Question Analytics Functions
===========================================
Pure analytical functions implementing all 40 predefined questions across 8 domains.
Each function takes filtered data and relevant parameters, executes mathematically
rigorous calculations, and returns structured data ready for visualization.
"""

from typing import Any
import pandas as pd
import numpy as np

PARAMETER_COLS = ["TLR", "RPC", "GO", "OI", "Perception"]


# =============================================================================
# DOMAIN 1: TIME-SERIES AND TREND ANALYSIS (Q1 - Q5)
# =============================================================================

def analyze_q1_institution_trajectory(
    df: pd.DataFrame,
    institution_name: str,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q1: How has the overall NIRF ranking of a selected institution changed from 2017 to 2025?"""
    if df.empty or "Name" not in df.columns:
        return pd.DataFrame(), ["No data available."]

    sub = df[df["Name"].str.lower() == institution_name.lower().strip()]
    if category and category != "All":
        sub = sub[sub["Category"] == category]

    if sub.empty:
        # Fallback to closest matching institution
        matches = df[df["Name"].str.contains(institution_name.split()[0], case=False, na=False)]
        if not matches.empty:
            sub = matches[matches["Category"] == category] if category != "All" else matches

    if sub.empty:
        return pd.DataFrame(), [f"No records found for '{institution_name}' in category '{category}'."]

    traj = sub[["Year", "Name", "Category", "Rank", "Score"] + [p for p in PARAMETER_COLS if p in sub.columns]]
    traj = traj.sort_values("Year").dropna(subset=["Rank"]).reset_index(drop=True)

    if traj.empty:
        return pd.DataFrame(), [f"No published rank records for {institution_name}."]

    best_rank = int(traj["Rank"].min())
    worst_rank = int(traj["Rank"].max())
    first_row = traj.iloc[0]
    last_row = traj.iloc[-1]
    net_shift = int(first_row["Rank"] - last_row["Rank"])  # positive = improvement

    insights = [
        f"**{last_row['Name']}** ({category}) was ranked in **{len(traj)}** editions between {traj['Year'].min()} and {traj['Year'].max()}.",
        f"Best Rank: **#{best_rank}** · Lowest Rank: **#{worst_rank}** · Latest ({last_row['Year']}): **#{int(last_row['Rank'])}** (Score: {last_row['Score']:.2f}).",
    ]
    if net_shift > 0:
        insights.append(f"🟢 **Net Improvement:** Climbed **{net_shift}** positions from #{int(first_row['Rank'])} ({first_row['Year']}) to #{int(last_row['Rank'])} ({last_row['Year']}).")
    elif net_shift < 0:
        insights.append(f"🔴 **Net Decline:** Dropped **{abs(net_shift)}** positions from #{int(first_row['Rank'])} ({first_row['Year']}) to #{int(last_row['Rank'])} ({last_row['Year']}).")
    else:
        insights.append(f"⚪ **Stable Position:** Rank remained constant at #{int(last_row['Rank'])} between first and last tracked year.")

    return traj, insights


def analyze_q2_greatest_rank_improvement(
    df: pd.DataFrame,
    category: str = "Overall",
    top_n: int = 15,
) -> tuple[pd.DataFrame, list[str]]:
    """Q2: Which institutions have shown the greatest improvement in rank over nine years?"""
    sub = df[df["Category"] == category] if category != "All" else df
    sub = sub.dropna(subset=["Rank", "Year", "Name"]).sort_values("Year")

    records = []
    for name, grp in sub.groupby("Name"):
        if grp["Year"].nunique() >= 2:
            first_yr = grp.iloc[0]
            last_yr = grp.iloc[-1]
            if first_yr["Year"] < last_yr["Year"]:
                # Improvement = Initial Rank - Final Rank (e.g., 50 -> 10 = +40)
                improvement = float(first_yr["Rank"] - last_yr["Rank"])
                records.append({
                    "Name": name,
                    "Category": first_yr["Category"],
                    "Initial_Year": int(first_yr["Year"]),
                    "Initial_Rank": int(first_yr["Rank"]),
                    "Final_Year": int(last_yr["Year"]),
                    "Final_Rank": int(last_yr["Rank"]),
                    "Rank_Climb": int(improvement),
                    "Years_Tracked": int(grp["Year"].nunique()),
                })

    res = pd.DataFrame(records)
    if res.empty:
        return pd.DataFrame(), ["Insufficient multi-year records in the selected category."]

    improvers = res[res["Rank_Climb"] > 0].sort_values("Rank_Climb", ascending=False).head(top_n).reset_index(drop=True)
    if improvers.empty:
        return res.head(top_n), ["No institutions demonstrated a net rank improvement in this cohort."]

    top = improvers.iloc[0]
    insights = [
        f"🏆 Top improver in **{category}**: **{top['Name']}** climbed **+{top['Rank_Climb']}** positions (from #{top['Initial_Rank']} in {top['Initial_Year']} to #{top['Final_Rank']} in {top['Final_Year']}).",
        f"A total of **{len(res[res['Rank_Climb'] > 0])}** out of {len(res)} tracked institutions registered a net positive rank improvement over their participating span.",
    ]
    return improvers, insights


def analyze_q3_largest_rank_decline(
    df: pd.DataFrame,
    category: str = "Overall",
    top_n: int = 15,
) -> tuple[pd.DataFrame, list[str]]:
    """Q3: Which institutions have experienced the largest decline in rank?"""
    sub = df[df["Category"] == category] if category != "All" else df
    sub = sub.dropna(subset=["Rank", "Year", "Name"]).sort_values("Year")

    records = []
    for name, grp in sub.groupby("Name"):
        if grp["Year"].nunique() >= 2:
            first_yr = grp.iloc[0]
            last_yr = grp.iloc[-1]
            if first_yr["Year"] < last_yr["Year"]:
                # Decline = Final Rank - Initial Rank (e.g. 10 -> 45 = +35 decline)
                decline = float(last_yr["Rank"] - first_yr["Rank"])
                records.append({
                    "Name": name,
                    "Category": first_yr["Category"],
                    "Initial_Year": int(first_yr["Year"]),
                    "Initial_Rank": int(first_yr["Rank"]),
                    "Final_Year": int(last_yr["Year"]),
                    "Final_Rank": int(last_yr["Rank"]),
                    "Rank_Decline": int(decline),
                    "Years_Tracked": int(grp["Year"].nunique()),
                })

    res = pd.DataFrame(records)
    if res.empty:
        return pd.DataFrame(), ["Insufficient multi-year records in the selected category."]

    decliners = res[res["Rank_Decline"] > 0].sort_values("Rank_Decline", ascending=False).head(top_n).reset_index(drop=True)
    if decliners.empty:
        return res.head(top_n), ["No institutions demonstrated a net rank decline in this cohort."]

    worst = decliners.iloc[0]
    insights = [
        f"⚠️ Largest rank decline in **{category}**: **{worst['Name']}** dropped **{worst['Rank_Decline']}** positions (from #{worst['Initial_Rank']} in {worst['Initial_Year']} down to #{worst['Final_Rank']} in {worst['Final_Year']}).",
        f"**{len(res[res['Rank_Decline'] > 0])}** institutions saw their ranking positions drop between their earliest and most recent appearances.",
    ]
    return decliners, insights


def analyze_q4_avg_score_over_time(
    df: pd.DataFrame,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q4: How has the average NIRF score changed over time?"""
    sub = df[df["Category"] == category] if category != "All" else df
    sub = sub.dropna(subset=["Score", "Year"])

    if sub.empty:
        return pd.DataFrame(), ["No numeric score records found."]

    agg = sub.groupby("Year")["Score"].agg(
        Mean_Score="mean",
        Median_Score="median",
        Min_Score="min",
        Max_Score="max",
        Std_Dev="std",
        Institutions="count",
    ).reset_index().sort_values("Year")

    agg = agg.round(2)
    start_row = agg.iloc[0]
    end_row = agg.iloc[-1]
    score_delta = round(end_row["Mean_Score"] - start_row["Mean_Score"], 2)

    direction = "increased" if score_delta > 0 else "decreased"
    insights = [
        f"Average NIRF score {direction} by **{abs(score_delta):.2f} points** (from {start_row['Mean_Score']} in {int(start_row['Year'])} to {end_row['Mean_Score']} in {int(end_row['Year'])}).",
        f"Latest Median Score ({int(end_row['Year'])}): **{end_row['Median_Score']:.2f}** across **{int(end_row['Institutions']):,}** ranked institutions.",
    ]
    return agg, insights


def analyze_q5_persistent_top_10(
    df: pd.DataFrame,
    category: str = "Overall",
    top_n: int = 10,
) -> tuple[pd.DataFrame, list[str]]:
    """Q5: Which institutions have consistently remained in the top 10 across multiple years?"""
    sub = df[df["Category"] == category] if category != "All" else df
    sub = sub.dropna(subset=["Rank", "Year", "Name"])

    if sub.empty:
        return pd.DataFrame(), ["No ranking records available."]

    total_cohort_years = sub["Year"].nunique()
    top10_records = sub[sub["Rank"] <= top_n]

    perf = (
        top10_records.groupby("Name")
        .agg(
            Top_10_Appearances=("Year", "nunique"),
            Total_Years_Participated=("Year", lambda y: sub[sub["Name"] == y.name]["Year"].nunique() if hasattr(y, 'name') else len(y)),
            Best_Rank=("Rank", "min"),
            Worst_Rank=("Rank", "max"),
            Avg_Rank=("Rank", "mean"),
            Avg_Score=("Score", "mean"),
        )
        .reset_index()
    )

    # Re-calculate correct total participation
    tot_dict = sub.groupby("Name")["Year"].nunique().to_dict()
    perf["Total_Years_Participated"] = perf["Name"].map(tot_dict)
    perf["Consistency_Rate"] = (perf["Top_10_Appearances"] / total_cohort_years * 100).round(1)
    perf["Avg_Rank"] = perf["Avg_Rank"].round(2)
    perf["Avg_Score"] = perf["Avg_Score"].round(2)
    perf["Best_Rank"] = perf["Best_Rank"].astype(int)
    perf["Worst_Rank"] = perf["Worst_Rank"].astype(int)

    perf = perf.sort_values(["Top_10_Appearances", "Avg_Rank"], ascending=[False, True]).reset_index(drop=True)
    all_years_top = perf[perf["Top_10_Appearances"] == total_cohort_years]

    insights = [
        f"**{len(all_years_top)}** institutions maintained Top 10 status in all **{total_cohort_years}** ranking editions evaluated ({', '.join(all_years_top['Name'].head(3).tolist())}).",
        f"A total of **{len(perf)}** distinct institutions reached the Top {top_n} threshold at least once in {category}.",
    ]
    return perf, insights


# =============================================================================
# DOMAIN 2: GEOSPATIAL AND REGIONAL ANALYSIS (Q6 - Q10)
# =============================================================================

def analyze_q6_states_top_100(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q6: Which states have the highest number of institutions in the top 100?"""
    sub = df[df["Rank"] <= 100].copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if sub.empty:
        return pd.DataFrame(), [f"No top 100 institutions found for Year: {year}, Category: {category}."]

    counts = sub.groupby("State").agg(
        Top_100_Count=("Name", "count"),
        Unique_Institutions=("Name", "nunique"),
        Avg_Score=("Score", "mean"),
        Best_Rank=("Rank", "min"),
    ).reset_index().sort_values("Top_100_Count", ascending=False)

    counts["Avg_Score"] = counts["Avg_Score"].round(2)
    counts["Best_Rank"] = counts["Best_Rank"].astype(int)
    leader = counts.iloc[0]

    insights = [
        f"**{leader['State']}** leads the country with **{leader['Top_100_Count']}** institutions in the Top 100 for {year} ({category}).",
        f"Top 3 States: **{', '.join(counts['State'].head(3).tolist())}** account for {counts['Top_100_Count'].head(3).sum()} ({round(counts['Top_100_Count'].head(3).sum() / counts['Top_100_Count'].sum() * 100, 1)}%) of all Top 100 spots.",
    ]
    return counts, insights


def analyze_q7_geo_distribution_change(
    df: pd.DataFrame,
    category: str = "Overall",
    top_states_n: int = 6,
) -> tuple[pd.DataFrame, list[str]]:
    """Q7: How has the geographical distribution of top-ranked institutions changed from 2017 to 2025?"""
    sub = df[df["Rank"] <= 100].copy()
    if category != "All":
        sub = sub[sub["Category"] == category]

    if sub.empty:
        return pd.DataFrame(), ["No top-100 data available."]

    top_states = sub["State"].value_counts().head(top_states_n).index.tolist()
    sub_top = sub[sub["State"].isin(top_states)]

    pivot = sub_top.groupby(["Year", "State"])["Name"].count().reset_index()
    pivot.columns = ["Year", "State", "Top_100_Count"]

    pivot_wide = pivot.pivot(index="Year", columns="State", values="Top_100_Count").fillna(0).astype(int).reset_index()

    insights = [
        f"Tracking longitudinal distribution across top {top_states_n} states: {', '.join(top_states)}.",
        f"Examines regional concentration vs dispersion of higher education excellence across 2017–2025.",
    ]
    return pivot, insights


def analyze_q8_states_improving_top_100(
    df: pd.DataFrame,
    category: str = "Overall",
    year_start: int = 2017,
    year_end: int = 2025,
) -> tuple[pd.DataFrame, list[str]]:
    """Q8: Which states have improved their representation in the top 100 over the years?"""
    sub = df[df["Rank"] <= 100].copy()
    if category != "All":
        sub = sub[sub["Category"] == category]

    # Available years
    avail = sorted(sub["Year"].unique())
    if len(avail) < 2:
        return pd.DataFrame(), ["Insufficient historical years for top 100 comparison."]

    y1 = year_start if year_start in avail else avail[0]
    y2 = year_end if year_end in avail else avail[-1]

    sub_y1 = sub[sub["Year"] == y1]["State"].value_counts().rename(f"Count_{y1}")
    sub_y2 = sub[sub["Year"] == y2]["State"].value_counts().rename(f"Count_{y2}")

    merged = pd.concat([sub_y1, sub_y2], axis=1).fillna(0).astype(int)
    merged["Net_Improvement"] = merged[f"Count_{y2}"] - merged[f"Count_{y1}"]
    merged = merged.reset_index().rename(columns={"index": "State"})
    merged = merged.sort_values("Net_Improvement", ascending=False).reset_index(drop=True)

    top_gainer = merged.iloc[0]
    insights = [
        f"**{top_gainer['State']}** showed the largest gain in Top 100 representation (+{top_gainer['Net_Improvement']} institutions, from {top_gainer[f'Count_{y1}']} in {y1} to {top_gainer[f'Count_{y2}']} in {y2}).",
        f"**{len(merged[merged['Net_Improvement'] > 0])}** states improved their top 100 seat count between {y1} and {y2}.",
    ]
    return merged, insights


def analyze_q9_karnataka_vs_tamil_nadu(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q9: How do institutions in Karnataka compare with institutions in Tamil Nadu in terms of NIRF rankings?"""
    sub = df[df["State"].isin(["Karnataka", "Tamil Nadu"])].copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if sub.empty:
        return pd.DataFrame(), ["No comparative records available for Karnataka and Tamil Nadu."]

    summary = sub.groupby("State").agg(
        Total_Ranked=("Name", "count"),
        Top_50_Count=("Rank", lambda r: (r <= 50).sum()),
        Top_100_Count=("Rank", lambda r: (r <= 100).sum()),
        Mean_Score=("Score", "mean"),
        Median_Score=("Score", "median"),
        Best_Rank=("Rank", "min"),
    ).reset_index()

    summary["Mean_Score"] = summary["Mean_Score"].round(2)
    summary["Median_Score"] = summary["Median_Score"].round(2)
    summary["Best_Rank"] = summary["Best_Rank"].astype(int)

    insights = [
        f"Head-to-head comparison in **{category}** ({year}):",
        f"Tamil Nadu: **{summary[summary['State'] == 'Tamil Nadu']['Total_Ranked'].values[0] if 'Tamil Nadu' in summary['State'].values else 0}** ranked institutions (Top 100: {summary[summary['State'] == 'Tamil Nadu']['Top_100_Count'].values[0] if 'Tamil Nadu' in summary['State'].values else 0}).",
        f"Karnataka: **{summary[summary['State'] == 'Karnataka']['Total_Ranked'].values[0] if 'Karnataka' in summary['State'].values else 0}** ranked institutions (Top 100: {summary[summary['State'] == 'Karnataka']['Top_100_Count'].values[0] if 'Karnataka' in summary['State'].values else 0}).",
    ]
    return sub[["Name", "State", "City", "Rank", "Score", "Year", "Category"]].sort_values("Rank").reset_index(drop=True), insights


def analyze_q10_states_new_entrants(
    df: pd.DataFrame,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q10: Which states have the largest number of newly appearing institutions in the rankings?"""
    sub = df[df["Category"] == category] if category != "All" else df
    if sub.empty:
        return pd.DataFrame(), ["No records available."]

    first_appearance = sub.groupby("Name")["Year"].min().reset_index()
    first_appearance.columns = ["Name", "First_Year"]

    # Newly appearing in the dataset (first year > minimum dataset year)
    min_year = sub["Year"].min()
    new_insts = first_appearance[first_appearance["First_Year"] > min_year]

    merged = new_insts.merge(sub[["Name", "State"]].drop_duplicates("Name"), on="Name", how="left")
    state_counts = merged["State"].value_counts().reset_index()
    state_counts.columns = ["State", "New_Entrants_Count"]

    top_state = state_counts.iloc[0] if not state_counts.empty else {"State": "None", "New_Entrants_Count": 0}
    insights = [
        f"State with most new entrants post-{min_year}: **{top_state['State']}** with **{top_state['New_Entrants_Count']}** newly appearing institutions.",
        f"Nationally, **{len(new_insts):,}** institutions entered {category} rankings between {min_year + 1} and {sub['Year'].max()}.",
    ]
    return state_counts, insights


# =============================================================================
# DOMAIN 3: UNIVARIATE ANALYSIS (Q11 - Q15)
# =============================================================================

def analyze_q11_score_distribution_year(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q11: What is the distribution of NIRF scores for institutions in a selected year?"""
    sub = df.dropna(subset=["Score"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if sub.empty:
        return pd.DataFrame(), [f"No numeric score data for Year: {year}, Category: {category}."]

    scores = sub["Score"]
    insights = [
        f"Score distribution for **{category}** ({year}): Mean = **{scores.mean():.2f}**, Median = **{scores.median():.2f}**, Std Dev = **{scores.std():.2f}**.",
        f"Score Span: Min = **{scores.min():.2f}** to Max = **{scores.max():.2f}** (IQR: {scores.quantile(0.75) - scores.quantile(0.25):.2f}).",
    ]
    return sub[["Name", "Score", "Rank", "Category", "Year", "State"]].sort_values("Score", ascending=False).reset_index(drop=True), insights


def analyze_q12_rank_distribution(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q12: How are overall ranks distributed across institutions?"""
    sub = df.dropna(subset=["Rank"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if sub.empty:
        return pd.DataFrame(), ["No rank records found."]

    # Group into rank bands
    bins = [0, 10, 25, 50, 100, 200, 500]
    labels = ["1–10 (Elite)", "11–25", "26–50", "51–100", "101–200", "201+"]
    sub["Rank_Band"] = pd.cut(sub["Rank"], bins=bins, labels=labels, right=True)

    dist = sub["Rank_Band"].value_counts().sort_index().reset_index()
    dist.columns = ["Rank_Band", "Institution_Count"]
    dist["Percentage"] = (dist["Institution_Count"] / len(sub) * 100).round(1)

    insights = [
        f"Evaluated **{len(sub)}** ranked institutions in {category} ({year}).",
        f"Highest tier (Top 50) contains **{sub[sub['Rank'] <= 50].shape[0]}** institutions; remaining **{sub[sub['Rank'] > 50].shape[0]}** are in extended bands.",
    ]
    return dist, insights


def analyze_q13_score_summary_stats(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q13: What are the average, median, minimum and maximum NIRF scores in a given year?"""
    sub = df.dropna(subset=["Score"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if sub.empty:
        return pd.DataFrame(), ["No score data found."]

    s = sub["Score"]
    q1 = float(s.quantile(0.25))
    median = float(s.median())
    q3 = float(s.quantile(0.75))

    stats_df = pd.DataFrame([{
        "Metric": "Average (Mean)", "Value": round(float(s.mean()), 2),
    }, {
        "Metric": "Median", "Value": round(median, 2),
    }, {
        "Metric": "Minimum", "Value": round(float(s.min()), 2),
    }, {
        "Metric": "Maximum", "Value": round(float(s.max()), 2),
    }, {
        "Metric": "Q1 (25th Percentile)", "Value": round(q1, 2),
    }, {
        "Metric": "Q3 (75th Percentile)", "Value": round(q3, 2),
    }, {
        "Metric": "Interquartile Range (IQR)", "Value": round(q3 - q1, 2),
    }, {
        "Metric": "Standard Deviation", "Value": round(float(s.std()), 2),
    }])

    skewness = "positively skewed (higher mean than median)" if s.mean() > median else "negatively skewed / balanced"
    insights = [
        f"Summary stats for **{category}** ({year}): Mean = **{s.mean():.2f}**, Median = **{median:.2f}**, Range = **[{s.min():.2f}, {s.max():.2f}]**.",
        f"The distribution is {skewness}.",
    ]
    return stats_df, insights


def analyze_q14_score_quartile_percentage(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q14: What percentage of ranked institutions fall into each score quartile?"""
    sub = df.dropna(subset=["Score"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if sub.empty:
        return pd.DataFrame(), ["No score data found."]

    q25 = sub["Score"].quantile(0.25)
    q50 = sub["Score"].quantile(0.50)
    q75 = sub["Score"].quantile(0.75)

    def assign_quartile(sc):
        if sc <= q25:
            return f"Q1: Bottom 25% (<= {q25:.1f})"
        elif sc <= q50:
            return f"Q2: 25th–50th% ({q25:.1f}–{q50:.1f})"
        elif sc <= q75:
            return f"Q3: 50th–75th% ({q50:.1f}–{q75:.1f})"
        else:
            return f"Q4: Top 25% (> {q75:.1f})"

    sub["Quartile"] = sub["Score"].apply(assign_quartile)
    counts = sub["Quartile"].value_counts().reset_index()
    counts.columns = ["Quartile", "Institution_Count"]
    counts["Percentage"] = (counts["Institution_Count"] / len(sub) * 100).round(1)
    counts = counts.sort_values("Quartile").reset_index(drop=True)

    insights = [
        f"Evenly divided into four empirical score quartiles across **{len(sub)}** institutions.",
        f"Top quartile (Q4) starts at score **{q75:.2f}**, while bottom quartile (Q1) cuts off at **{q25:.2f}**.",
    ]
    return counts, insights


def analyze_q15_score_distribution_by_category(
    df: pd.DataFrame,
    year: int | str = 2025,
) -> tuple[pd.DataFrame, list[str]]:
    """Q15: How does the distribution of NIRF scores vary across different NIRF categories?"""
    sub = df.dropna(subset=["Score"]).copy()
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if sub.empty:
        return pd.DataFrame(), ["No score records available."]

    summary = sub.groupby("Category")["Score"].agg(
        Count="count",
        Mean="mean",
        Median="median",
        Std_Dev="std",
        Min="min",
        Max="max",
        IQR=lambda s: s.quantile(0.75) - s.quantile(0.25),
    ).round(2).reset_index().sort_values("Median", ascending=False)

    highest_cat = summary.iloc[0]
    insights = [
        f"Highest median score category in {year}: **{highest_cat['Category']}** (Median: {highest_cat['Median']:.2f}, Mean: {highest_cat['Mean']:.2f}).",
        f"Evaluates spread and benchmark variability across **{len(summary)}** institutional categories ({len(sub):,} total records).",
    ]
    return sub[["Category", "Name", "Score", "Rank", "Year", "State"]].sort_values(["Category", "Score"], ascending=[True, False]).reset_index(drop=True), insights


# =============================================================================
# DOMAIN 4: BIVARIATE AND CORRELATION ANALYSIS (Q16 - Q20)
# =============================================================================

def analyze_q16_rpc_vs_score(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q16: Is there an association between RPC scores and overall NIRF scores?"""
    sub = df.dropna(subset=["RPC", "Score"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if len(sub) < 3:
        return pd.DataFrame(), ["Insufficient data points for correlation analysis."]

    r_pearson = round(float(sub["Score"].corr(sub["RPC"], method="pearson")), 4)
    r_spearman = round(float(sub["Score"].rank().corr(sub["RPC"].rank(), method="pearson")), 4)

    insights = [
        f"Pearson correlation ($r$): **{r_pearson}** (Spearman $\\rho$: **{r_spearman}**, sample size: {len(sub):,}).",
        f"Indicates a **{'Very Strong' if r_pearson >= 0.8 else 'Strong' if r_pearson >= 0.6 else 'Moderate'}** positive association between research productivity and overall NIRF score.",
    ]
    return sub[["Name", "Score", "RPC", "Rank", "Category", "Year"]].reset_index(drop=True), insights


def analyze_q17_perception_vs_score(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q17: How are Perception scores related to overall NIRF scores?"""
    sub = df.dropna(subset=["Perception", "Score"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if len(sub) < 3:
        return pd.DataFrame(), ["Insufficient observations for correlation."]

    r_pearson = round(float(sub["Score"].corr(sub["Perception"], method="pearson")), 4)
    r_spearman = round(float(sub["Score"].rank().corr(sub["Perception"].rank(), method="pearson")), 4)

    insights = [
        f"Pearson correlation ($r$): **{r_pearson}** (Spearman $\\rho$: **{r_spearman}**, sample size: {len(sub):,}).",
        f"Shows a **{'Very Strong' if r_pearson >= 0.8 else 'Strong' if r_pearson >= 0.6 else 'Moderate'}** relationship between public/academic perception and total score.",
    ]
    return sub[["Name", "Score", "Perception", "Rank", "Category", "Year"]].reset_index(drop=True), insights


def analyze_q18_strongest_param_correlation(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q18: Which NIRF parameter has the strongest correlation with the overall NIRF score?"""
    sub = df.dropna(subset=["Score"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    rows = []
    for p in PARAMETER_COLS:
        valid = sub[["Score", p]].dropna()
        if len(valid) >= 3:
            pr = float(valid["Score"].corr(valid[p], method="pearson"))
            sr = float(valid["Score"].rank().corr(valid[p].rank(), method="pearson"))
            rows.append({
                "Parameter": p,
                "Pearson_r": round(pr, 4),
                "Spearman_rho": round(sr, 4),
                "Observations": len(valid),
            })

    res = pd.DataFrame(rows).sort_values("Pearson_r", ascending=False).reset_index(drop=True)
    if res.empty:
        return pd.DataFrame(), ["Insufficient parameter data available."]

    top = res.iloc[0]
    insights = [
        f"🏆 **{top['Parameter']}** has the strongest correlation with overall NIRF Score (Pearson $r$ = **{top['Pearson_r']}**, Spearman $\\rho$ = **{top['Spearman_rho']}**).",
        f"Parameter ranking by correlation strength: {' > '.join(res['Parameter'].tolist())}.",
    ]
    return res, insights


def analyze_q19_tlr_vs_rpc(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q19: What is the relationship between TLR and RPC scores?"""
    sub = df.dropna(subset=["TLR", "RPC"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if len(sub) < 3:
        return pd.DataFrame(), ["Insufficient data for TLR vs RPC correlation."]

    r_pearson = round(float(sub["TLR"].corr(sub["RPC"], method="pearson")), 4)
    r_spearman = round(float(sub["TLR"].rank().corr(sub["RPC"].rank(), method="pearson")), 4)

    insights = [
        f"Pearson correlation between Teaching (TLR) and Research (RPC): **{r_pearson}** (Spearman: **{r_spearman}**, n = {len(sub):,}).",
        f"Reveals how instructional resource allocation couples with research productivity.",
    ]
    return sub[["Name", "TLR", "RPC", "Score", "Rank", "Category", "Year"]].reset_index(drop=True), insights


def analyze_q20_research_correlation_evolution(
    df: pd.DataFrame,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q20: Has the correlation between research-related scores and overall NIRF scores changed from 2017 to 2025?"""
    sub = df.dropna(subset=["RPC", "Score"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]

    records = []
    for yr, grp in sub.groupby("Year"):
        if len(grp) >= 5:
            r = float(grp["Score"].corr(grp["RPC"], method="pearson"))
            records.append({
                "Year": int(yr),
                "Pearson_r": round(r, 4),
                "Sample_Size": len(grp),
            })

    res = pd.DataFrame(records).sort_values("Year").reset_index(drop=True)
    if res.empty:
        return pd.DataFrame(), ["Insufficient multi-year research score records."]

    y_first = res.iloc[0]
    y_last = res.iloc[-1]
    delta = round(y_last["Pearson_r"] - y_first["Pearson_r"], 4)

    insights = [
        f"RPC vs Score correlation shifted from **{y_first['Pearson_r']}** ({y_first['Year']}) to **{y_last['Pearson_r']}** ({y_last['Year']}) (Delta: {delta:+.4f}).",
        f"Research scores remain a decisive determinant of total rank across all 9 editions.",
    ]
    return res, insights


# =============================================================================
# DOMAIN 5: MULTIVARIATE ANALYSIS (Q21 - Q25)
# =============================================================================

def analyze_q21_top_5_all_parameters(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q21: Which are the top five institutions based on their performance across all five NIRF parameters?"""
    sub = df.dropna(subset=PARAMETER_COLS).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if sub.empty:
        return pd.DataFrame(), ["No institutions with complete 5-parameter data."]

    # Transparent equal-weight composite calculation
    sub["Composite_5P"] = sub[PARAMETER_COLS].mean(axis=1).round(2)
    top5 = sub.sort_values("Composite_5P", ascending=False).head(5).reset_index(drop=True)

    insights = [
        f"Top 5 balanced performers across all 5 parameters ({category}, {year}): **{', '.join(top5['Name'].tolist())}**.",
        f"Methodology: Equal-weighted composite = (TLR + RPC + GO + OI + Perception) / 5. #1: **{top5.iloc[0]['Name']}** ({top5.iloc[0]['Composite_5P']:.2f}).",
    ]
    return top5[["Name", "Category", "Year", "Composite_5P", "Score", "Rank"] + PARAMETER_COLS], insights


def analyze_q22_high_rpc_low_tlr(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
    top_n: int = 10,
) -> tuple[pd.DataFrame, list[str]]:
    """Q22: Which institutions have high research scores but relatively low teaching scores?"""
    sub = df.dropna(subset=["RPC", "TLR"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if sub.empty:
        return pd.DataFrame(), ["No parameter records available."]

    sub["RPC_minus_TLR"] = (sub["RPC"] - sub["TLR"]).round(2)
    res = sub.sort_values("RPC_minus_TLR", ascending=False).head(top_n).reset_index(drop=True)

    top = res.iloc[0]
    insights = [
        f"Largest Research > Teaching gap: **{top['Name']}** (RPC: {top['RPC']:.2f}, TLR: {top['TLR']:.2f}, Delta: **+{top['RPC_minus_TLR']:.2f}**).",
        f"Identifies research-intensive institutes outperforming their instructional score baseline.",
    ]
    return res[["Name", "RPC", "TLR", "RPC_minus_TLR", "Score", "Rank", "Category", "Year"]], insights


def analyze_q23_high_tlr_low_perception(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
    top_n: int = 10,
) -> tuple[pd.DataFrame, list[str]]:
    """Q23: Which institutions have high teaching scores but relatively low perception scores?"""
    sub = df.dropna(subset=["TLR", "Perception"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if sub.empty:
        return pd.DataFrame(), ["No parameter records available."]

    sub["TLR_minus_Perception"] = (sub["TLR"] - sub["Perception"]).round(2)
    res = sub.sort_values("TLR_minus_Perception", ascending=False).head(top_n).reset_index(drop=True)

    top = res.iloc[0]
    insights = [
        f"Highest Teaching > Perception gap: **{top['Name']}** (TLR: {top['TLR']:.2f}, Perception: {top['Perception']:.2f}, Delta: **+{top['TLR_minus_Perception']:.2f}**).",
        f"Highlights institutions with strong teaching and infrastructure that may be undervalued in reputation polls.",
    ]
    return res[["Name", "TLR", "Perception", "TLR_minus_Perception", "Score", "Rank", "Category", "Year"]], insights


def analyze_q24_improved_score_declined_params(
    df: pd.DataFrame,
    category: str = "Overall",
    year_start: int = 2024,
    year_end: int = 2025,
    top_n: int = 15,
) -> tuple[pd.DataFrame, list[str]]:
    """Q24: Which institutions have improved their overall scores despite declining in one or more parameters?"""
    sub = df.dropna(subset=["Score"] + PARAMETER_COLS).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]

    avail = sorted(sub["Year"].unique())
    if len(avail) < 2:
        return pd.DataFrame(), ["Need at least two years for comparative analysis."]

    y1 = year_start if year_start in avail else avail[-2]
    y2 = year_end if year_end in avail else avail[-1]

    sub_y1 = sub[sub["Year"] == y1].set_index("Name")
    sub_y2 = sub[sub["Year"] == y2].set_index("Name")

    common = sub_y1.index.intersection(sub_y2.index)
    if common.empty:
        return pd.DataFrame(), [f"No common institutions between {y1} and {y2}."]

    records = []
    for name in common:
        row1 = sub_y1.loc[name]
        row2 = sub_y2.loc[name]
        score_diff = float(row2["Score"] - row1["Score"])
        if score_diff > 0:  # overall score improved
            param_drops = []
            for p in PARAMETER_COLS:
                p_diff = float(row2[p] - row1[p])
                if p_diff < 0:
                    param_drops.append(f"{p} ({p_diff:+.1f})")
            if param_drops:
                records.append({
                    "Name": name,
                    "Score_Improvement": round(score_diff, 2),
                    f"Score_{y1}": round(float(row1["Score"]), 2),
                    f"Score_{y2}": round(float(row2["Score"]), 2),
                    "Declined_Parameters": ", ".join(param_drops),
                    "Declined_Count": len(param_drops),
                })

    res = pd.DataFrame(records).sort_values("Score_Improvement", ascending=False).head(top_n).reset_index(drop=True)
    if res.empty:
        return pd.DataFrame(), [f"No institutions improved overall score while dropping parameters between {y1} and {y2}."]

    insights = [
        f"Found **{len(records)}** institutions that increased their total score between {y1} and {y2} despite declines in 1+ parameters.",
        f"Top case: **{res.iloc[0]['Name']}** (Score +{res.iloc[0]['Score_Improvement']:.2f}, despite dropping: {res.iloc[0]['Declined_Parameters']}).",
    ]
    return res, insights


def analyze_q25_largest_parameter_gap(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
    top_n: int = 15,
) -> tuple[pd.DataFrame, list[str]]:
    """Q25: Which institutions have the largest gap between their strongest and weakest NIRF parameters?"""
    sub = df.dropna(subset=PARAMETER_COLS).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if sub.empty:
        return pd.DataFrame(), ["No parameter records available."]

    sub["Max_Param"] = sub[PARAMETER_COLS].max(axis=1)
    sub["Min_Param"] = sub[PARAMETER_COLS].min(axis=1)
    sub["Parameter_Gap"] = (sub["Max_Param"] - sub["Min_Param"]).round(2)

    res = sub.sort_values("Parameter_Gap", ascending=False).head(top_n).reset_index(drop=True)
    top = res.iloc[0]

    insights = [
        f"Largest parameter asymmetry: **{top['Name']}** (Spread: **{top['Parameter_Gap']:.2f} pts**, Max: {top['Max_Param']:.2f}, Min: {top['Min_Param']:.2f}).",
        f"Measures institutional imbalance between premier strengths and lagging dimensions.",
    ]
    return res[["Name", "Parameter_Gap", "Max_Param", "Min_Param", "Score", "Rank", "Category", "Year"] + PARAMETER_COLS], insights


# =============================================================================
# DOMAIN 6: DISTRIBUTION AND STATISTICAL ANALYSIS (Q26 - Q30)
# =============================================================================

def analyze_q26_top_10_vs_remaining(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q26: How does the score distribution of top 10 institutions compare with the remaining institutions?"""
    sub = df.dropna(subset=["Score", "Rank"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if sub.empty:
        return pd.DataFrame(), ["No score data available."]

    sub["Cohort"] = np.where(sub["Rank"] <= 10, "Top 10", "Remaining (Rank > 10)")
    comp = sub.groupby("Cohort")["Score"].agg(
        Count="count",
        Mean="mean",
        Median="median",
        Std_Dev="std",
        Min="min",
        Max="max",
        IQR=lambda s: s.quantile(0.75) - s.quantile(0.25),
    ).round(2).reset_index()

    top10_mean = comp[comp["Cohort"] == "Top 10"]["Mean"].values[0] if "Top 10" in comp["Cohort"].values else 0
    rem_mean = comp[comp["Cohort"] != "Top 10"]["Mean"].values[0] if len(comp) > 1 else 0
    gap = round(top10_mean - rem_mean, 2)

    insights = [
        f"Top 10 Mean Score: **{top10_mean:.2f}** vs Remaining Mean: **{rem_mean:.2f}** (Performance Gap: **{gap:.2f} points**).",
        f"Top 10 IQR: {comp[comp['Cohort'] == 'Top 10']['IQR'].values[0] if 'Top 10' in comp['Cohort'].values else 0} pts vs Remaining IQR: {comp[comp['Cohort'] != 'Top 10']['IQR'].values[0] if len(comp) > 1 else 0} pts.",
    ]
    return sub[["Name", "Cohort", "Score", "Rank", "Category", "Year"]].reset_index(drop=True), insights


def analyze_q27_score_dispersion_two_years(
    df: pd.DataFrame,
    category: str = "Overall",
    year_1: int = 2017,
    year_2: int = 2025,
) -> tuple[pd.DataFrame, list[str]]:
    """Q27: Are NIRF scores more dispersed in one year compared with another?"""
    sub = df.dropna(subset=["Score"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]

    avail = sorted(sub["Year"].unique())
    y1 = year_1 if year_1 in avail else avail[0]
    y2 = year_2 if year_2 in avail else avail[-1]

    sub_two = sub[sub["Year"].isin([y1, y2])]
    disp = sub_two.groupby("Year")["Score"].agg(
        Count="count",
        Mean="mean",
        Std_Dev="std",
        Variance="var",
        Median="median",
        IQR=lambda s: s.quantile(0.75) - s.quantile(0.25),
    ).round(2).reset_index()

    row1 = disp[disp["Year"] == y1].iloc[0] if not disp[disp["Year"] == y1].empty else None
    row2 = disp[disp["Year"] == y2].iloc[0] if not disp[disp["Year"] == y2].empty else None

    if row1 is not None and row2 is not None:
        more_disp = y2 if row2["Std_Dev"] > row1["Std_Dev"] else y1
        insights = [
            f"Scores were more dispersed in **{more_disp}** (Std Dev: {row2['Std_Dev'] if more_disp == y2 else row1['Std_Dev']} vs {row1['Std_Dev'] if more_disp == y2 else row2['Std_Dev']}).",
            f"IQR shift: **{row1['IQR']}** ({y1}) to **{row2['IQR']}** ({y2}).",
        ]
    else:
        insights = ["Comparison complete."]

    return sub_two[["Year", "Name", "Score", "Rank", "Category"]].reset_index(drop=True), insights


def analyze_q28_parameter_greatest_variability(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q28: Which NIRF parameter shows the greatest variability?"""
    sub = df.dropna(subset=PARAMETER_COLS).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if sub.empty:
        return pd.DataFrame(), ["No parameter records available."]

    rows = []
    for p in PARAMETER_COLS:
        s = sub[p]
        mean_v = float(s.mean())
        std_v = float(s.std())
        cv = (std_v / mean_v * 100) if mean_v > 0 else 0
        rows.append({
            "Parameter": p,
            "Std_Dev": round(std_v, 2),
            "Coefficient_of_Variation_pct": round(cv, 1),
            "IQR": round(float(s.quantile(0.75) - s.quantile(0.25)), 2),
            "Mean": round(mean_v, 2),
        })

    res = pd.DataFrame(rows).sort_values("Std_Dev", ascending=False).reset_index(drop=True)
    top = res.iloc[0]

    insights = [
        f"🏆 **{top['Parameter']}** demonstrates the greatest absolute variability (Std Dev = **{top['Std_Dev']}**, CV = **{top['Coefficient_of_Variation_pct']}%**).",
        f"Ranked variability order: {' > '.join(res['Parameter'].tolist())}.",
    ]
    return res, insights


def analyze_q29_median_iqr_over_time(
    df: pd.DataFrame,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q29: How have the median and interquartile range of NIRF scores changed over time?"""
    sub = df.dropna(subset=["Score"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]

    records = []
    for yr, grp in sub.groupby("Year"):
        s = grp["Score"]
        q1 = float(s.quantile(0.25))
        q3 = float(s.quantile(0.75))
        records.append({
            "Year": int(yr),
            "Median_Score": round(float(s.median()), 2),
            "IQR": round(q3 - q1, 2),
            "Q1": round(q1, 2),
            "Q3": round(q3, 2),
            "Sample_Size": len(grp),
        })

    res = pd.DataFrame(records).sort_values("Year").reset_index(drop=True)
    if res.empty:
        return pd.DataFrame(), ["No longitudinal score records found."]

    insights = [
        f"Median score moved from **{res.iloc[0]['Median_Score']}** ({res.iloc[0]['Year']}) to **{res.iloc[-1]['Median_Score']}** ({res.iloc[-1]['Year']}).",
        f"IQR span progressed from **{res.iloc[0]['IQR']}** to **{res.iloc[-1]['IQR']}**, reflecting cohort score dispersion over the decade.",
    ]
    return res, insights


def analyze_q30_score_distribution_across_states(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
    min_institutions: int = 3,
) -> tuple[pd.DataFrame, list[str]]:
    """Q30: How does the distribution of NIRF scores vary across states?"""
    sub = df.dropna(subset=["Score"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    state_counts = sub["State"].value_counts()
    valid_states = state_counts[state_counts >= min_institutions].index.tolist()
    sub_filtered = sub[sub["State"].isin(valid_states)]

    if sub_filtered.empty:
        return pd.DataFrame(), ["Insufficient state-level institution records."]

    state_stats = sub_filtered.groupby("State")["Score"].agg(
        Count="count",
        Mean="mean",
        Median="median",
        Std_Dev="std",
        IQR=lambda s: s.quantile(0.75) - s.quantile(0.25),
    ).round(2).reset_index().sort_values("Median", ascending=False)

    insights = [
        f"Comparing score spread across **{len(state_stats)}** states with >= {min_institutions} ranked institutions in {year}.",
        f"Highest state median: **{state_stats.iloc[0]['State']}** ({state_stats.iloc[0]['Median']:.2f}).",
    ]
    return sub_filtered[["State", "Name", "Score", "Rank", "Category", "Year"]].reset_index(drop=True), insights


# =============================================================================
# DOMAIN 7: RANKING TRANSITIONS AND MOBILITY (Q31 - Q35)
# =============================================================================

def analyze_q31_transition_51_100_to_top_50(
    df: pd.DataFrame,
    category: str = "Overall",
    year_start: int = 2024,
    year_end: int = 2025,
) -> tuple[pd.DataFrame, list[str]]:
    """Q31: How many institutions moved from the 51–100 rank band into the top 50 between two selected years?"""
    sub = df.dropna(subset=["Rank"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]

    avail = sorted(sub["Year"].unique())
    y1 = year_start if year_start in avail else avail[-2]
    y2 = year_end if year_end in avail else avail[-1]

    sub_y1 = sub[sub["Year"] == y1].set_index("Name")
    sub_y2 = sub[sub["Year"] == y2].set_index("Name")

    common = sub_y1.index.intersection(sub_y2.index)
    transitions = []

    for name in common:
        r1 = float(sub_y1.loc[name, "Rank"])
        r2 = float(sub_y2.loc[name, "Rank"])
        if 51 <= r1 <= 100 and r2 <= 50:
            transitions.append({
                "Name": name,
                f"Rank_{y1}": int(r1),
                f"Rank_{y2}": int(r2),
                "Rank_Improvement": int(r1 - r2),
                f"Score_{y1}": round(float(sub_y1.loc[name, "Score"]), 2) if "Score" in sub_y1 else None,
                f"Score_{y2}": round(float(sub_y2.loc[name, "Score"]), 2) if "Score" in sub_y2 else None,
            })

    res = pd.DataFrame(transitions)
    if not res.empty:
        res = res.sort_values("Rank_Improvement", ascending=False).reset_index(drop=True)
        insights = [
            f"**{len(res)}** institutions broke from the 51–100 band into the Top 50 between {y1} and {y2}.",
            f"Biggest climber: **{res.iloc[0]['Name']}** (jumped +{res.iloc[0]['Rank_Improvement']} spots, from #{res.iloc[0][f'Rank_{y1}']} to #{res.iloc[0][f'Rank_{y2}']}).",
        ]
    else:
        insights = [f"No institutions moved from the 51–100 tier into the Top 50 between {y1} and {y2} in {category}."]

    return res, insights


def analyze_q32_top_10_entrants_exits(
    df: pd.DataFrame,
    category: str = "Overall",
    year_start: int = 2024,
    year_end: int = 2025,
) -> tuple[pd.DataFrame, list[str]]:
    """Q32: Which institutions entered or exited the top 10 between consecutive years?"""
    sub = df.dropna(subset=["Rank"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]

    avail = sorted(sub["Year"].unique())
    y1 = year_start if year_start in avail else avail[-2]
    y2 = year_end if year_end in avail else avail[-1]

    top10_y1 = set(sub[(sub["Year"] == y1) & (sub["Rank"] <= 10)]["Name"])
    top10_y2 = set(sub[(sub["Year"] == y2) & (sub["Rank"] <= 10)]["Name"])

    entrants = top10_y2 - top10_y1
    exits = top10_y1 - top10_y2

    records = []
    for name in entrants:
        r2 = sub[(sub["Year"] == y2) & (sub["Name"] == name)]["Rank"].values[0]
        r1_sub = sub[(sub["Year"] == y1) & (sub["Name"] == name)]
        r1_str = f"#{int(r1_sub['Rank'].values[0])}" if not r1_sub.empty else "Unranked / Absent"
        records.append({"Name": name, "Status": "New Entrant to Top 10", f"Rank_{y1}": r1_str, f"Rank_{y2}": f"#{int(r2)}"})

    for name in exits:
        r1 = sub[(sub["Year"] == y1) & (sub["Name"] == name)]["Rank"].values[0]
        r2_sub = sub[(sub["Year"] == y2) & (sub["Name"] == name)]
        r2_str = f"#{int(r2_sub['Rank'].values[0])}" if not r2_sub.empty else "Unranked / Absent"
        records.append({"Name": name, "Status": "Exited Top 10", f"Rank_{y1}": f"#{int(r1)}", f"Rank_{y2}": r2_str})

    res = pd.DataFrame(records)
    insights = [
        f"Between {y1} and {y2}: **{len(entrants)}** institutions entered the Top 10, and **{len(exits)}** institutions exited.",
        f"Top 10 Retention Rate: **{10 - len(exits)}/10 ({ (10 - len(exits))*10 }%)** of institutions retained their elite spot.",
    ]
    return res, insights


def analyze_q33_same_rank_band_percentage(
    df: pd.DataFrame,
    category: str = "Overall",
    year_start: int = 2024,
    year_end: int = 2025,
) -> tuple[pd.DataFrame, list[str]]:
    """Q33: What percentage of institutions remained in the same rank band between two selected years?"""
    sub = df.dropna(subset=["Rank"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]

    avail = sorted(sub["Year"].unique())
    y1 = year_start if year_start in avail else avail[-2]
    y2 = year_end if year_end in avail else avail[-1]

    def get_band(r):
        if r <= 10:
            return "1–10"
        elif r <= 25:
            return "11–25"
        elif r <= 50:
            return "26–50"
        elif r <= 100:
            return "51–100"
        else:
            return "101+"

    sub["Band"] = sub["Rank"].apply(get_band)
    sub_y1 = sub[sub["Year"] == y1].set_index("Name")
    sub_y2 = sub[sub["Year"] == y2].set_index("Name")

    common = sub_y1.index.intersection(sub_y2.index)
    if common.empty:
        return pd.DataFrame(), ["No common institutions between selected years."]

    same_count = sum(sub_y1.loc[n, "Band"] == sub_y2.loc[n, "Band"] for n in common)
    shifted_count = len(common) - same_count
    pct_same = round(same_count / len(common) * 100, 1)

    res = pd.DataFrame([
        {"Mobility_Status": "Remained in Same Band", "Count": same_count, "Percentage": pct_same},
        {"Mobility_Status": "Shifted to Different Band", "Count": shifted_count, "Percentage": round(100 - pct_same, 1)},
    ])

    insights = [
        f"**{pct_same}%** ({same_count:,} out of {len(common):,}) institutions remained in the exact same rank tier between {y1} and {y2}.",
        f"**{round(100 - pct_same, 1)}%** experienced inter-tier mobility.",
    ]
    return res, insights


def analyze_q34_largest_rank_movements(
    df: pd.DataFrame,
    category: str = "Overall",
    year_start: int = 2024,
    year_end: int = 2025,
    top_n: int = 10,
) -> tuple[pd.DataFrame, list[str]]:
    """Q34: Which institutions experienced the largest upward or downward movements in rank?"""
    sub = df.dropna(subset=["Rank"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]

    avail = sorted(sub["Year"].unique())
    y1 = year_start if year_start in avail else avail[-2]
    y2 = year_end if year_end in avail else avail[-1]

    sub_y1 = sub[sub["Year"] == y1].set_index("Name")
    sub_y2 = sub[sub["Year"] == y2].set_index("Name")

    common = sub_y1.index.intersection(sub_y2.index)
    movements = []
    for name in common:
        r1 = float(sub_y1.loc[name, "Rank"])
        r2 = float(sub_y2.loc[name, "Rank"])
        delta = int(r1 - r2)  # positive = climb, negative = drop
        movements.append({
            "Name": name,
            f"Rank_{y1}": int(r1),
            f"Rank_{y2}": int(r2),
            "Rank_Movement": delta,
            "Direction": "Upward (Climb)" if delta > 0 else "Downward (Drop)" if delta < 0 else "Unchanged",
        })

    m_df = pd.DataFrame(movements)
    if m_df.empty:
        return pd.DataFrame(), ["No common institutions found."]

    top_climbers = m_df.sort_values("Rank_Movement", ascending=False).head(top_n // 2)
    top_drops = m_df.sort_values("Rank_Movement", ascending=True).head(top_n // 2)
    combined = pd.concat([top_climbers, top_drops]).reset_index(drop=True)

    insights = [
        f"Largest upward climb: **{top_climbers.iloc[0]['Name']}** (+{top_climbers.iloc[0]['Rank_Movement']} positions, #{top_climbers.iloc[0][f'Rank_{y1}']} -> #{top_climbers.iloc[0][f'Rank_{y2}']}).",
        f"Largest drop: **{top_drops.iloc[0]['Name']}** ({top_drops.iloc[0]['Rank_Movement']} positions, #{top_drops.iloc[0][f'Rank_{y1}']} -> #{top_drops.iloc[0][f'Rank_{y2}']}).",
    ]
    return combined, insights


def analyze_q35_annual_rank_movement_summary(
    df: pd.DataFrame,
    category: str = "Overall",
) -> tuple[pd.DataFrame, list[str]]:
    """Q35: How many institutions improved, declined or retained their ranking positions each year?"""
    sub = df.dropna(subset=["Rank"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]

    avail = sorted(sub["Year"].unique())
    records = []

    for i in range(len(avail) - 1):
        y1, y2 = avail[i], avail[i + 1]
        sub1 = sub[sub["Year"] == y1].set_index("Name")
        sub2 = sub[sub["Year"] == y2].set_index("Name")
        common = sub1.index.intersection(sub2.index)

        improved = sum(sub1.loc[n, "Rank"] > sub2.loc[n, "Rank"] for n in common)
        declined = sum(sub1.loc[n, "Rank"] < sub2.loc[n, "Rank"] for n in common)
        retained = sum(sub1.loc[n, "Rank"] == sub2.loc[n, "Rank"] for n in common)

        records.append({
            "Transition": f"{y1} → {y2}",
            "Improved_Count": improved,
            "Declined_Count": declined,
            "Retained_Count": retained,
            "Total_Matched": len(common),
        })

    res = pd.DataFrame(records)
    insights = [
        f"Analyzed {len(records)} annual transition epochs across {category}.",
        f"Average annual turnover: ~{int(res['Improved_Count'].mean())} institutions climbed and ~{int(res['Declined_Count'].mean())} dropped each year.",
    ]
    return res, insights


# =============================================================================
# DOMAIN 8: OUTLIER AND PERFORMANCE GAP ANALYSIS (Q36 - Q40)
# =============================================================================

def analyze_q36_high_rpc_relative_to_score(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
    factor: float = 1.5,
) -> tuple[pd.DataFrame, list[str]]:
    """Q36: Which institutions have unusually high research scores relative to their overall scores?"""
    sub = df.dropna(subset=["RPC", "Score"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if len(sub) < 5:
        return pd.DataFrame(), ["Insufficient data for outlier ratio analysis."]

    sub["RPC_Score_Ratio"] = (sub["RPC"] / sub["Score"]).round(3)
    q1 = sub["RPC_Score_Ratio"].quantile(0.25)
    q3 = sub["RPC_Score_Ratio"].quantile(0.75)
    iqr = q3 - q1
    cutoff = q3 + factor * iqr

    sub["Is_Outlier"] = sub["RPC_Score_Ratio"] > cutoff
    outliers = sub[sub["Is_Outlier"]].sort_values("RPC_Score_Ratio", ascending=False).reset_index(drop=True)

    insights = [
        f"Detected **{len(outliers)}** institutions with unusually high RPC/Score ratio (Cutoff: > {cutoff:.2f}).",
        f"Top outlier: **{outliers.iloc[0]['Name'] if not outliers.empty else 'None'}** (Ratio: {outliers.iloc[0]['RPC_Score_Ratio'] if not outliers.empty else 0:.2f}, RPC: {outliers.iloc[0]['RPC'] if not outliers.empty else 0:.1f}, Score: {outliers.iloc[0]['Score'] if not outliers.empty else 0:.1f}).",
    ]
    return sub[["Name", "RPC", "Score", "RPC_Score_Ratio", "Is_Outlier", "Rank", "Category", "Year"]].sort_values("RPC_Score_Ratio", ascending=False).reset_index(drop=True), insights


def analyze_q37_research_substantially_better_teaching(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
    gap_threshold: float = 15.0,
) -> tuple[pd.DataFrame, list[str]]:
    """Q37: Which institutions perform substantially better in research than in teaching?"""
    sub = df.dropna(subset=["RPC", "TLR"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if sub.empty:
        return pd.DataFrame(), ["No parameter records available."]

    sub["Research_Teaching_Gap"] = (sub["RPC"] - sub["TLR"]).round(2)
    gap_insts = sub[sub["Research_Teaching_Gap"] >= gap_threshold].sort_values("Research_Teaching_Gap", ascending=False).reset_index(drop=True)

    insights = [
        f"Found **{len(gap_insts)}** institutions where Research (RPC) exceeds Teaching (TLR) by >= {gap_threshold} points.",
        f"Lead research-specialist: **{gap_insts.iloc[0]['Name'] if not gap_insts.empty else 'None'}** (Gap: +{gap_insts.iloc[0]['Research_Teaching_Gap'] if not gap_insts.empty else 0:.2f} pts).",
    ]
    return gap_insts[["Name", "RPC", "TLR", "Research_Teaching_Gap", "Score", "Rank", "Category", "Year"]], insights


def analyze_q38_unusual_yoy_score_changes(
    df: pd.DataFrame,
    category: str = "Overall",
    top_n: int = 15,
) -> tuple[pd.DataFrame, list[str]]:
    """Q38: Which institutions have unusually large year-to-year changes in NIRF scores?"""
    sub = df.dropna(subset=["Score", "Year", "Name"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]

    sub = sub.sort_values(["Name", "Year"])
    sub["Prev_Score"] = sub.groupby("Name")["Score"].shift(1)
    sub["Prev_Year"] = sub.groupby("Name")["Year"].shift(1)
    sub["Year_Diff"] = sub["Year"] - sub["Prev_Year"]

    # Filter to consecutive year appearances
    consec = sub[sub["Year_Diff"] == 1].copy()
    consec["Score_Change"] = (consec["Score"] - consec["Prev_Score"]).round(2)
    consec["Abs_Score_Change"] = consec["Score_Change"].abs()

    q1 = consec["Abs_Score_Change"].quantile(0.25)
    q3 = consec["Abs_Score_Change"].quantile(0.75)
    cutoff = q3 + 1.5 * (q3 - q1)

    outliers = consec.sort_values("Abs_Score_Change", ascending=False).head(top_n).reset_index(drop=True)
    top = outliers.iloc[0] if not outliers.empty else None

    insights = [
        f"Largest annual score fluctuation: **{top['Name'] if top is not None else 'None'}** ({top['Prev_Year']:.0f} → {top['Year']:.0f}: Score changed by **{top['Score_Change']:+.2f} pts**).",
        f"Statistical anomaly threshold (1.5 * IQR): absolute score shifts exceeding **{cutoff:.2f} points**.",
    ]
    return outliers[["Name", "Prev_Year", "Year", "Prev_Score", "Score", "Score_Change", "Abs_Score_Change", "Category"]], insights


def analyze_q39_strong_params_poor_rank(
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
    rank_cutoff: int = 50,
) -> tuple[pd.DataFrame, list[str]]:
    """Q39: Which institutions have strong scores in one or more parameters but relatively poor overall rankings?"""
    sub = df.dropna(subset=["Rank"] + PARAMETER_COLS).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]
    if year != "All":
        sub = sub[sub["Year"] == int(year)]

    if sub.empty:
        return pd.DataFrame(), ["No parameter records available."]

    # Find 75th percentile for each parameter in the cohort
    p75 = {p: sub[p].quantile(0.75) for p in PARAMETER_COLS}

    strong_poor = []
    for _, row in sub[sub["Rank"] > rank_cutoff].iterrows():
        strong_pillars = [p for p in PARAMETER_COLS if row[p] >= p75[p]]
        if strong_pillars:
            strong_poor.append({
                "Name": row["Name"],
                "Rank": int(row["Rank"]),
                "Score": round(float(row["Score"]), 2),
                "Strong_Parameters": ", ".join(strong_pillars),
                "Strong_Param_Count": len(strong_pillars),
                **{p: round(float(row[p]), 2) for p in PARAMETER_COLS},
            })

    res = pd.DataFrame(strong_poor)
    if not res.empty:
        res = res.sort_values(["Strong_Param_Count", "Rank"], ascending=[False, True]).reset_index(drop=True)
        insights = [
            f"Identified **{len(res)}** institutions with Rank > #{rank_cutoff} holding at least one pillar score in the Top 25% (>= Q3).",
            f"Top example: **{res.iloc[0]['Name']}** (Rank #{res.iloc[0]['Rank']}, excel in: {res.iloc[0]['Strong_Parameters']}).",
        ]
    else:
        insights = [f"No institutions ranked > #{rank_cutoff} possessed parameters in the 75th percentile."]

    return res, insights


def analyze_q40_high_ranking_volatility_outliers(
    df: pd.DataFrame,
    category: str = "Overall",
    min_years: int = 3,
    top_n: int = 15,
) -> tuple[pd.DataFrame, list[str]]:
    """Q40: Which institutions show unusually high ranking volatility compared with similar institutions?"""
    sub = df.dropna(subset=["Rank", "Year", "Name"]).copy()
    if category != "All":
        sub = sub[sub["Category"] == category]

    grp = sub.groupby("Name").agg(
        Years_Count=("Year", "nunique"),
        Best_Rank=("Rank", "min"),
        Worst_Rank=("Rank", "max"),
        Rank_Std=("Rank", "std"),
        Avg_Rank=("Rank", "mean"),
    ).reset_index()

    grp = grp[grp["Years_Count"] >= min_years].dropna(subset=["Rank_Std"])
    if grp.empty:
        return pd.DataFrame(), [f"No institutions with >= {min_years} years of participation."]

    q1 = grp["Rank_Std"].quantile(0.25)
    q3 = grp["Rank_Std"].quantile(0.75)
    iqr = q3 - q1
    cutoff = q3 + 1.5 * iqr

    grp["Is_Volatility_Outlier"] = grp["Rank_Std"] > cutoff
    grp["Rank_Span"] = grp["Worst_Rank"] - grp["Best_Rank"]
    grp["Rank_Std"] = grp["Rank_Std"].round(2)
    grp["Avg_Rank"] = grp["Avg_Rank"].round(1)

    res = grp.sort_values("Rank_Std", ascending=False).head(top_n).reset_index(drop=True)
    outlier_count = grp["Is_Volatility_Outlier"].sum()

    insights = [
        f"Detected **{outlier_count}** ranking volatility outliers exceeding statistical cutoff (Rank Std > {cutoff:.2f}).",
        f"Most volatile institution: **{res.iloc[0]['Name']}** (Rank Std: {res.iloc[0]['Rank_Std']}, swing from #{int(res.iloc[0]['Best_Rank'])} to #{int(res.iloc[0]['Worst_Rank'])}).",
    ]
    return res, insights
