"""
NIRF Insight — Chatbot Analytics Executor
==========================================
Executes validated analytics functions directly on the in-memory NIRF dataset.
Guarantees 100% numerical fidelity and zero hallucination. All answers and
visualizations are generated strictly from actual dataset calculations.
"""

from typing import Any
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from core.analytics import (
    PARAMETER_COLS,
    calculate_correlation,
    get_five_number_summary,
    get_dataset_kpis,
)
from components.charts import (
    COLORS,
    _apply_layout,
    create_bar_chart,
    create_line_chart,
    create_scatter_chart,
    create_histogram,
    create_box_plot,
    create_multi_radar_chart,
)


COMMON_ALIASES = {
    "iit madras": "Indian Institute of Technology Madras",
    "iit bombay": "Indian Institute of Technology Bombay",
    "iit delhi": "Indian Institute of Technology Delhi",
    "iit kanpur": "Indian Institute of Technology Kanpur",
    "iit kharagpur": "Indian Institute of Technology Kharagpur",
    "iit roorkee": "Indian Institute of Technology Roorkee",
    "iit guwahati": "Indian Institute of Technology Guwahati",
    "iit hyderabad": "Indian Institute of Technology Hyderabad",
    "iit bhu": "Indian Institute of Technology (BHU) Varanasi",
    "iisc": "Indian Institute of Science",
    "iisc bangalore": "Indian Institute of Science",
    "aiims": "All India Institute of Medical Sciences",
    "jnu": "Jawaharlal Nehru University",
    "bhu": "Banaras Hindu University",
    "du": "University of Delhi",
}


def _resolve_institution_name(query: str) -> str:
    """Normalize common institutional acronyms and abbreviations."""
    clean = query.strip().lower()
    if clean in COMMON_ALIASES:
        return COMMON_ALIASES[clean]
    if clean.startswith("iit "):
        return "Indian Institute of Technology " + query.strip()[4:]
    if clean.startswith("nit "):
        return "National Institute of Technology " + query.strip()[4:]
    return query.strip()


def execute_chatbot_tool(
    df: pd.DataFrame,
    tool_name: str,
    tool_args: dict[str, Any],
) -> tuple[pd.DataFrame | dict[str, Any], list[str], go.Figure | None]:
    """Execute a whitelisted tool on the dataframe.

    Returns:
        (result_table_or_dict, key_facts_list, plotly_figure_or_none)
    """
    if df is None or df.empty:
        return pd.DataFrame(), ["Dataset is not available or is empty."], None

    args = tool_args or {}

    # -------------------------------------------------------------------------
    # 1. get_dataset_summary
    # -------------------------------------------------------------------------
    if tool_name == "get_dataset_summary":
        kpis = get_dataset_kpis(df)
        years = sorted(df["Year"].dropna().unique().astype(int).tolist())
        facts = [
            f"The NIRF dataset spans **{years[0]} to {years[-1]}** ({len(years)} annual editions).",
            f"Total ranked records: **{kpis['total_records']:,}** across **{kpis['unique_institutions']:,}** distinct institutions.",
            f"Coverage includes **{kpis['categories_count']}** disciplines across **{kpis['states_count']}** states/UTs.",
            f"National average score is **{kpis['avg_score']:.2f}** (Median: {kpis['median_score']:.2f}).",
        ]
        cat_counts = df["Category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Records"]
        fig = create_bar_chart(cat_counts, x="Category", y="Records", title="Records by Category", color=COLORS["primary"])
        return cat_counts, facts, fig

    # -------------------------------------------------------------------------
    # 2. get_available_years
    # -------------------------------------------------------------------------
    elif tool_name == "get_available_years":
        years = sorted(df["Year"].dropna().unique().astype(int).tolist())
        yearly_counts = df.groupby("Year")["Name"].count().reset_index()
        yearly_counts.columns = ["Year", "Ranked_Institutions"]
        facts = [
            f"Available NIRF ranking editions: **{', '.join(str(y) for y in years)}**.",
            f"Latest available edition is **{years[-1]}**.",
        ]
        fig = create_line_chart(yearly_counts, x="Year", y="Ranked_Institutions", title="Total Institutions Ranked Per Year")
        return yearly_counts, facts, fig

    # -------------------------------------------------------------------------
    # 3. get_available_columns
    # -------------------------------------------------------------------------
    elif tool_name == "get_available_columns":
        cols_summary = []
        for c in df.columns:
            if not c.endswith("_Raw") and c not in ("Is_Tied_Rank", "Is_Withdrawn", "Data_Availability"):
                cols_summary.append({
                    "Column": c,
                    "Type": "Numerical" if pd.api.types.is_numeric_dtype(df[c]) else "Categorical",
                    "Non_Null_Count": int(df[c].count()),
                })
        table = pd.DataFrame(cols_summary)
        facts = [
            f"Dataset contains **{len(table)}** primary analytics fields.",
            "5 Core Pillars: TLR (Teaching & Resources), RPC (Research & Professional Practice), GO (Graduation Outcomes), OI (Outreach & Inclusivity), Perception.",
        ]
        return table, facts, None

    # -------------------------------------------------------------------------
    # 4. get_top_institutions
    # -------------------------------------------------------------------------
    elif tool_name == "get_top_institutions":
        n = int(args.get("n", 10))
        year = args.get("year", 2025)
        cat = args.get("category", "Overall")
        state = args.get("state")
        sort_by = args.get("sort_by", "Score")

        sub = df.copy()
        if cat and cat != "All":
            sub = sub[sub["Category"].str.lower() == cat.lower().strip()]
        if year and year != "All":
            sub = sub[sub["Year"] == int(year)]
        if state and state != "All":
            sub = sub[sub["State"].str.contains(state.strip(), case=False, na=False)]

        if sub.empty:
            return pd.DataFrame(), [f"No institutions found for Category: {cat}, Year: {year}, State: {state or 'All'}."], None

        sort_col = sort_by if sort_by in sub.columns else "Score"
        asc = True if sort_col == "Rank" else False

        top_df = sub.dropna(subset=[sort_col]).sort_values(sort_col, ascending=asc).head(n).reset_index(drop=True)
        cols_to_show = ["Rank", "Name", "Category", "State", "Score"] + [p for p in PARAMETER_COLS if p in top_df.columns]
        table = top_df[[c for c in cols_to_show if c in top_df.columns]]

        leader = top_df.iloc[0]
        state_info = f" in {state}" if state else ""
        facts = [
            f"🏆 **#1 Ranked:** **{leader['Name']}** ({leader.get('State', 'N/A')}) with a Score of **{leader['Score']:.2f}** (Rank #{int(leader['Rank'])}).",
            f"Top {len(top_df)} institutions in **{cat}** ({year}){state_info} sorted by {sort_col}.",
        ]

        # Horizontal Bar Chart
        chart_data = top_df.sort_values(sort_col, ascending=not asc)
        fig = create_bar_chart(chart_data, x="Name", y=sort_col, title=f"Top {len(top_df)} in {cat} ({year})", horizontal=True, color=COLORS["primary"])
        return table, facts, fig

    # -------------------------------------------------------------------------
    # 5. get_institution_details
    # -------------------------------------------------------------------------
    elif tool_name == "get_institution_details":
        raw_name = args.get("institution_name", "").strip()
        name_query = _resolve_institution_name(raw_name)
        cat = args.get("category")
        year = args.get("year")

        if not name_query:
            return pd.DataFrame(), ["Please specify an institution name."], None

        sub = df[df["Name"].str.contains(name_query, case=False, na=False)].copy()
        if sub.empty and raw_name != name_query:
            sub = df[df["Name"].str.contains(raw_name, case=False, na=False)].copy()

        if cat and cat != "All":
            sub = sub[sub["Category"].str.lower() == cat.lower().strip()]
        if year and year != "All":
            sub = sub[sub["Year"] == int(year)]

        if sub.empty:
            return pd.DataFrame(), [f"No records matching '{name_query}' found in the dataset."], None

        sub = sub.sort_values(["Year", "Score"], ascending=[True, False]).reset_index(drop=True)
        cols = ["Year", "Name", "Category", "Rank", "Score", "City", "State"] + [p for p in PARAMETER_COLS if p in sub.columns]
        table = sub[[c for c in cols if c in sub.columns]]

        latest_rec = sub.iloc[-1]
        best_rank = sub["Rank"].min()
        facts = [
            f"Found **{len(sub)}** historical records for **{latest_rec['Name']}** across {sub['Year'].nunique()} edition(s).",
            f"Latest record ({latest_rec['Year']}, {latest_rec['Category']}): Rank **#{int(latest_rec['Rank'])}** with Score **{latest_rec['Score']:.2f}**.",
            f"All-time Best Rank: **#{int(best_rank)}**.",
        ]

        # Trajectory chart if multiple years
        if sub["Year"].nunique() > 1:
            fig = create_line_chart(sub, x="Year", y="Rank", color="Category", title=f"Ranking Trajectory: {latest_rec['Name']}")
            if fig:
                fig.update_yaxes(autorange="reversed", title="NIRF Rank (Lower = Better)")
        else:
            # Single year radar chart if 5 parameters exist
            pillars_present = [p for p in PARAMETER_COLS if p in latest_rec and pd.notna(latest_rec[p])]
            if len(pillars_present) == 5:
                vals = [float(latest_rec[p]) for p in pillars_present]
                fig = create_multi_radar_chart(pillars_present, [{"name": latest_rec["Name"], "values": vals}], title=f"Parameter Profile: {latest_rec['Name']} ({latest_rec['Year']})")
            else:
                fig = None

        return table, facts, fig

    # -------------------------------------------------------------------------
    # 6. compare_institutions
    # -------------------------------------------------------------------------
    elif tool_name == "compare_institutions":
        inst_names = args.get("institutions", [])
        year = args.get("year", 2025)
        cat = args.get("category", "Overall")

        if not inst_names:
            return pd.DataFrame(), ["Please specify at least 2 institutions to compare."], None

        matched_dfs = []
        for raw_query in inst_names:
            query = _resolve_institution_name(raw_query)
            m = df[(df["Name"].str.contains(query, case=False, na=False))].copy()
            if m.empty and raw_query != query:
                m = df[(df["Name"].str.contains(raw_query, case=False, na=False))].copy()
            if cat and cat != "All":
                m_cat = m[m["Category"].str.lower() == cat.lower().strip()]
                if not m_cat.empty:
                    m = m_cat
            if year and year != "All":
                m_yr = m[m["Year"] == int(year)]
                if not m_yr.empty:
                    m = m_yr
            if not m.empty:
                matched_dfs.append(m.sort_values("Year").iloc[-1:])

        if not matched_dfs:
            return pd.DataFrame(), [f"Could not find matching records for the requested institutions."], None

        comp_df = pd.concat(matched_dfs).drop_duplicates(subset=["Name", "Year"]).reset_index(drop=True)
        cols = ["Name", "Category", "Year", "Rank", "Score"] + [p for p in PARAMETER_COLS if p in comp_df.columns]
        table = comp_df[[c for c in cols if c in comp_df.columns]]

        # Facts
        best_inst = comp_df.sort_values("Rank").iloc[0]
        facts = [
            f"Comparing **{len(comp_df)}** institutions for **{cat}** ({year}).",
            f"Highest ranked in cohort: **{best_inst['Name']}** (Rank #{int(best_inst['Rank'])}, Score: {best_inst['Score']:.2f}).",
        ]

        # Multi-Radar chart if 5 parameters present
        traces = []
        for _, row in comp_df.iterrows():
            if all(p in row and pd.notna(row[p]) for p in PARAMETER_COLS):
                vals = [float(row[p]) for p in PARAMETER_COLS]
                traces.append({"name": row["Name"], "values": vals})

        if traces:
            fig = create_multi_radar_chart(PARAMETER_COLS, traces, title=f"Institution Comparison ({year})")
        else:
            fig = create_bar_chart(comp_df, x="Name", y="Score", title=f"Score Comparison ({year})", color=COLORS["primary"])

        return table, facts, fig

    # -------------------------------------------------------------------------
    # 7. get_yearly_trends
    # -------------------------------------------------------------------------
    elif tool_name == "get_yearly_trends":
        cat = args.get("category", "Overall")
        inst = args.get("institution_name")
        metric = args.get("metric", "Score")

        sub = df.copy()
        if cat and cat != "All":
            sub = sub[sub["Category"].str.lower() == cat.lower().strip()]
        if inst:
            sub = sub[sub["Name"].str.contains(inst.strip(), case=False, na=False)]

        if sub.empty:
            return pd.DataFrame(), ["No data matching trend criteria."], None

        if inst:
            trend = sub.sort_values("Year").reset_index(drop=True)
            table = trend[["Year", "Name", "Category", metric, "Rank"]].reset_index(drop=True)
            fig = create_line_chart(table, x="Year", y=metric, title=f"{metric} Trend for {inst}")
            if metric == "Rank" and fig:
                fig.update_yaxes(autorange="reversed")
            facts = [
                f"Historical trajectory of **{metric}** for **{inst}** ({trend['Year'].min()}–{trend['Year'].max()}).",
                f"Latest ({trend.iloc[-1]['Year']}): {metric} = **{trend.iloc[-1][metric]}** (Rank #{int(trend.iloc[-1]['Rank'])}).",
            ]
        else:
            trend = sub.groupby("Year")[metric].agg(["mean", "median", "count"]).round(2).reset_index()
            trend.columns = ["Year", f"Mean_{metric}", f"Median_{metric}", "Count"]
            table = trend
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=trend["Year"], y=trend[f"Mean_{metric}"], mode="lines+markers", name=f"Mean {metric}", line=dict(color=COLORS["primary"], width=3)))
            fig.add_trace(go.Scatter(x=trend["Year"], y=trend[f"Median_{metric}"], mode="lines+markers", name=f"Median {metric}", line=dict(color=COLORS["accent"], dash="dash", width=2)))
            fig = _apply_layout(fig, title=f"National Average {metric} Trend in {cat} (2017–2025)")
            facts = [
                f"Average {metric} in {cat} shifted from **{trend.iloc[0][f'Mean_{metric}']}** ({trend.iloc[0]['Year']}) to **{trend.iloc[-1][f'Mean_{metric}']}** ({trend.iloc[-1]['Year']}).",
                f"Latest median in {cat} ({trend.iloc[-1]['Year']}): **{trend.iloc[-1][f'Median_{metric}']}** across {trend.iloc[-1]['Count']} institutions.",
            ]
        return table, facts, fig

    # -------------------------------------------------------------------------
    # 8. get_state_analysis
    # -------------------------------------------------------------------------
    elif tool_name == "get_state_analysis":
        state_q = args.get("state")
        year = args.get("year", 2025)
        cat = args.get("category", "Overall")
        top_n = int(args.get("top_n_states", 10))

        sub = df.copy()
        if cat and cat != "All":
            sub = sub[sub["Category"].str.lower() == cat.lower().strip()]
        if year and year != "All":
            sub = sub[sub["Year"] == int(year)]

        if state_q:
            sub_st = sub[sub["State"].str.contains(state_q.strip(), case=False, na=False)].sort_values("Rank").reset_index(drop=True)
            if sub_st.empty:
                return pd.DataFrame(), [f"No institutions found in {state_q} for Year {year} ({cat})."], None
            table = sub_st[["Rank", "Name", "City", "State", "Score"]].head(25)
            facts = [
                f"Found **{len(sub_st)}** institutions in **{state_q}** for {year} ({cat}).",
                f"Top institution in {state_q}: **{sub_st.iloc[0]['Name']}** (Rank #{int(sub_st.iloc[0]['Rank'])}, Score: {sub_st.iloc[0]['Score']:.2f}).",
                f"Average state score: **{sub_st['Score'].mean():.2f}** (Median: {sub_st['Score'].median():.2f}).",
            ]
            fig = create_bar_chart(sub_st.head(10).sort_values("Score", ascending=True), x="Name", y="Score", title=f"Top Institutions in {state_q} ({year})", horizontal=True, color=COLORS["primary"])
            return table, facts, fig
        else:
            state_agg = sub.groupby("State").agg(
                Institutions=("Name", "count"),
                Avg_Score=("Score", "mean"),
                Top_50_Count=("Rank", lambda r: (r <= 50).sum()),
            ).round(2).reset_index().sort_values("Institutions", ascending=False)
            table = state_agg.head(top_n)
            top_st = table.iloc[0]
            facts = [
                f"**{top_st['State']}** leads the country with **{top_st['Institutions']}** institutions in {year} ({cat}).",
                f"Top 3 states by representation: {', '.join(table['State'].head(3).tolist())}.",
            ]
            fig = create_bar_chart(table.sort_values("Institutions", ascending=True), x="State", y="Institutions", title=f"Top States by Institution Count ({year})", horizontal=True, color=COLORS["primary"])
            return table, facts, fig

    # -------------------------------------------------------------------------
    # 9. get_category_analysis
    # -------------------------------------------------------------------------
    elif tool_name == "get_category_analysis":
        year = args.get("year", 2025)
        sub = df.copy()
        if year and year != "All":
            sub = sub[sub["Year"] == int(year)]

        cat_summary = sub.groupby("Category").agg(
            Institutions=("Name", "count"),
            Avg_Score=("Score", "mean"),
            Median_Score=("Score", "median"),
            Top_Score=("Score", "max"),
        ).round(2).reset_index().sort_values("Institutions", ascending=False)

        table = cat_summary
        top_cat = cat_summary.iloc[0]
        facts = [
            f"Evaluated **{len(cat_summary)}** disciplines in {year}.",
            f"Largest category: **{top_cat['Category']}** with {top_cat['Institutions']:,} institutions.",
            f"Highest median score discipline: **{cat_summary.sort_values('Median_Score', ascending=False).iloc[0]['Category']}**.",
        ]
        fig = create_bar_chart(cat_summary, x="Category", y="Institutions", title=f"Institutions by Category ({year})", color=COLORS["primary"])
        return table, facts, fig

    # -------------------------------------------------------------------------
    # 10. get_parameter_analysis
    # -------------------------------------------------------------------------
    elif tool_name == "get_parameter_analysis":
        param = args.get("parameter", "RPC")
        year = args.get("year", 2025)
        cat = args.get("category", "Overall")
        top_n = int(args.get("top_n", 10))

        sub = df.copy()
        if cat and cat != "All":
            sub = sub[sub["Category"].str.lower() == cat.lower().strip()]
        if year and year != "All":
            sub = sub[sub["Year"] == int(year)]

        if param not in sub.columns:
            return pd.DataFrame(), [f"Parameter '{param}' not found in dataset."], None

        clean_p = sub.dropna(subset=[param]).sort_values(param, ascending=False).reset_index(drop=True)
        top_p = clean_p.head(top_n)
        table = top_p[["Rank", "Name", "Category", param, "Score", "State"]].reset_index(drop=True)

        leader = top_p.iloc[0]
        facts = [
            f"🏆 Top institution in **{param}**: **{leader['Name']}** with {param} = **{leader[param]:.2f}** (Overall Score: {leader['Score']:.2f}).",
            f"Parameter mean across cohort: **{clean_p[param].mean():.2f}** (Median: {clean_p[param].median():.2f}).",
        ]
        fig = create_bar_chart(top_p.sort_values(param, ascending=True), x="Name", y=param, title=f"Top {top_n} Institutions in {param} ({year})", horizontal=True, color=COLORS["accent"])
        return table, facts, fig

    # -------------------------------------------------------------------------
    # 11. get_score_statistics
    # -------------------------------------------------------------------------
    elif tool_name == "get_score_statistics":
        year = args.get("year", 2025)
        cat = args.get("category", "Overall")

        sub = df.copy()
        if cat and cat != "All":
            sub = sub[sub["Category"].str.lower() == cat.lower().strip()]
        if year and year != "All":
            sub = sub[sub["Year"] == int(year)]

        summary = get_five_number_summary(sub, "Score")
        if not summary:
            return pd.DataFrame(), [f"No numeric score data found for {cat} ({year})."], None

        table = pd.DataFrame([{"Metric": k, "Value": v} for k, v in summary.items() if k != "column"])
        facts = [
            f"Score Summary for **{cat}** ({year}) across {summary['count']:,} institutions:",
            f"Mean: **{summary['mean']:.2f}** · Median: **{summary['median']:.2f}** · Std Dev: **{summary['std']:.2f}**.",
            f"IQR (Spread): **{summary['iqr']:.2f}** · Range: **[{summary['min']:.2f}, {summary['max']:.2f}]**.",
        ]
        fig = create_box_plot(sub, x="Category", y="Score", title=f"Score Box Plot for {cat} ({year})")
        return table, facts, fig

    # -------------------------------------------------------------------------
    # 12. get_correlation_analysis
    # -------------------------------------------------------------------------
    elif tool_name == "get_correlation_analysis":
        c1 = args.get("col1", "RPC")
        c2 = args.get("col2", "Score")
        year = args.get("year", 2025)
        cat = args.get("category", "Overall")

        sub = df.copy()
        if cat and cat != "All":
            sub = sub[sub["Category"].str.lower() == cat.lower().strip()]
        if year and year != "All":
            sub = sub[sub["Year"] == int(year)]

        r, n, desc = calculate_correlation(sub, c1, c2)
        if r is None:
            return pd.DataFrame(), [f"Could not compute correlation between {c1} and {c2} ({desc})."], None

        table = sub[[c1, c2, "Name", "Category", "Year"]].dropna().head(50).reset_index(drop=True)
        facts = [
            f"Pearson correlation ($r$) between **{c1}** and **{c2}**: **{r:.4f}** ({desc}, sample size: {n:,}).",
            f"Shows a {desc.lower()} between {c1} and {c2} in {cat} ({year}).",
        ]
        fig = create_scatter_chart(sub, x=c1, y=c2, title=f"{c1} vs {c2} Correlation (r = {r})", hover_name="Name", trendline="ols")
        return table, facts, fig

    # -------------------------------------------------------------------------
    # 13. get_rank_changes
    # -------------------------------------------------------------------------
    elif tool_name == "get_rank_changes":
        cat = args.get("category", "Overall")
        y1 = int(args.get("year_start", 2024))
        y2 = int(args.get("year_end", 2025))
        direction = args.get("direction", "climbers")
        top_n = int(args.get("top_n", 10))

        sub = df[df["Category"] == cat].dropna(subset=["Rank", "Year", "Name"])
        s1 = sub[sub["Year"] == y1].set_index("Name")
        s2 = sub[sub["Year"] == y2].set_index("Name")
        common = s1.index.intersection(s2.index)

        records = []
        for n in common:
            r1 = float(s1.loc[n, "Rank"])
            r2 = float(s2.loc[n, "Rank"])
            delta = int(r1 - r2)  # positive = climb
            records.append({
                "Name": n,
                f"Rank_{y1}": int(r1),
                f"Rank_{y2}": int(r2),
                "Rank_Movement": delta,
            })
        rdf = pd.DataFrame(records)
        if rdf.empty:
            return pd.DataFrame(), [f"No common institutions tracked between {y1} and {y2} in {cat}."], None

        if direction == "climbers":
            filtered_r = rdf[rdf["Rank_Movement"] > 0].sort_values("Rank_Movement", ascending=False).head(top_n)
            facts = [
                f"Top rank climbers in {cat} ({y1} → {y2}): **{filtered_r.iloc[0]['Name']}** gained +{filtered_r.iloc[0]['Rank_Movement']} positions.",
                f"A total of **{len(rdf[rdf['Rank_Movement'] > 0])}** institutions improved their rank between {y1} and {y2}.",
            ]
        else:
            filtered_r = rdf[rdf["Rank_Movement"] < 0].sort_values("Rank_Movement", ascending=True).head(top_n)
            facts = [
                f"Largest rank decliners in {cat} ({y1} → {y2}): **{filtered_r.iloc[0]['Name']}** dropped {abs(filtered_r.iloc[0]['Rank_Movement'])} positions.",
                f"A total of **{len(rdf[rdf['Rank_Movement'] < 0])}** institutions experienced a rank decline between {y1} and {y2}.",
            ]

        table = filtered_r.reset_index(drop=True)
        fig = create_bar_chart(table.sort_values("Rank_Movement", ascending=True), x="Name", y="Rank_Movement", title=f"Rank Movement ({y1} → {y2})", horizontal=True, color=COLORS["primary"] if direction == "climbers" else "#A04040")
        return table, facts, fig

    # -------------------------------------------------------------------------
    # 14. get_distribution_analysis
    # -------------------------------------------------------------------------
    elif tool_name == "get_distribution_analysis":
        metric = args.get("metric", "Score")
        year = args.get("year", 2025)
        cat = args.get("category", "Overall")

        sub = df.copy()
        if cat and cat != "All":
            sub = sub[sub["Category"].str.lower() == cat.lower().strip()]
        if year and year != "All":
            sub = sub[sub["Year"] == int(year)]

        s = sub[metric].dropna()
        table = sub[["Rank", "Name", "Category", metric]].sort_values(metric, ascending=False).head(50).reset_index(drop=True)
        facts = [
            f"Distribution of **{metric}** in **{cat}** ({year}) across {len(s):,} institutions.",
            f"Mean: **{s.mean():.2f}** · Median: **{s.median():.2f}** · Std Dev: **{s.std():.2f}**.",
        ]
        fig = create_histogram(sub, x=metric, title=f"{metric} Distribution ({year})", nbins=30)
        return table, facts, fig

    # -------------------------------------------------------------------------
    # 15. get_filtered_dataset_summary
    # -------------------------------------------------------------------------
    elif tool_name == "get_filtered_dataset_summary":
        sub = df.copy()
        if args.get("category") and args["category"] != "All":
            sub = sub[sub["Category"].str.lower() == args["category"].lower().strip()]
        if args.get("year") and args["year"] != "All":
            sub = sub[sub["Year"] == int(args["year"])]
        if args.get("state") and args["state"] != "All":
            sub = sub[sub["State"].str.contains(args["state"].strip(), case=False, na=False)]
        if args.get("min_score"):
            sub = sub[sub["Score"] >= float(args["min_score"])]
        if args.get("max_rank"):
            sub = sub[sub["Rank"] <= int(args["max_rank"])]

        table = sub[["Rank", "Name", "Category", "State", "Score"]].sort_values("Rank").head(50).reset_index(drop=True)
        facts = [
            f"Found **{len(sub):,}** matching institutions for the specified criteria.",
            f"Average score in slice: **{sub['Score'].mean():.2f}** (Median: {sub['Score'].median():.2f})." if not sub.empty else "No records found.",
        ]
        fig = create_bar_chart(table.head(10).sort_values("Score", ascending=True), x="Name", y="Score", title="Matching Filtered Slice", horizontal=True, color=COLORS["primary"]) if not table.empty else None
        return table, facts, fig

    return pd.DataFrame(), [f"Unknown analytics operation: {tool_name}"], None
