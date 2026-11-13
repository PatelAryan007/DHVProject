"""
NIRF Insight — Central Question Execution Engine
================================================
Coordinates execution for all 40 official questions.
Extracts relevant filter arguments, dispatches to analytical functions,
assembles grounded insights, maps visualizations to charts, and provides
formatted supporting data tables with CSV export readiness.
"""

from typing import Any
import pandas as pd

from questions.question_config import get_question_by_id
from questions.question_functions import (
    analyze_q1_institution_trajectory,
    analyze_q2_greatest_rank_improvement,
    analyze_q3_largest_rank_decline,
    analyze_q4_avg_score_over_time,
    analyze_q5_persistent_top_10,
    analyze_q6_states_top_100,
    analyze_q7_geo_distribution_change,
    analyze_q8_states_improving_top_100,
    analyze_q9_karnataka_vs_tamil_nadu,
    analyze_q10_states_new_entrants,
    analyze_q11_score_distribution_year,
    analyze_q12_rank_distribution,
    analyze_q13_score_summary_stats,
    analyze_q14_score_quartile_percentage,
    analyze_q15_score_distribution_by_category,
    analyze_q16_rpc_vs_score,
    analyze_q17_perception_vs_score,
    analyze_q18_strongest_param_correlation,
    analyze_q19_tlr_vs_rpc,
    analyze_q20_research_correlation_evolution,
    analyze_q21_top_5_all_parameters,
    analyze_q22_high_rpc_low_tlr,
    analyze_q23_high_tlr_low_perception,
    analyze_q24_improved_score_declined_params,
    analyze_q25_largest_parameter_gap,
    analyze_q26_top_10_vs_remaining,
    analyze_q27_score_dispersion_two_years,
    analyze_q28_parameter_greatest_variability,
    analyze_q29_median_iqr_over_time,
    analyze_q30_score_distribution_across_states,
    analyze_q31_transition_51_100_to_top_50,
    analyze_q32_top_10_entrants_exits,
    analyze_q33_same_rank_band_percentage,
    analyze_q34_largest_rank_movements,
    analyze_q35_annual_rank_movement_summary,
    analyze_q36_high_rpc_relative_to_score,
    analyze_q37_research_substantially_better_teaching,
    analyze_q38_unusual_yoy_score_changes,
    analyze_q39_strong_params_poor_rank,
    analyze_q40_high_ranking_volatility_outliers,
)
from questions.chart_mapping import build_question_chart


def execute_question(
    question_or_id: dict[str, Any] | str,
    df: pd.DataFrame,
    year: int | str = 2025,
    category: str = "Overall",
    institution: str = "Indian Institute of Technology Madras",
    comparison_years: tuple[int, int] = (2024, 2025),
) -> tuple[Any, list[str], pd.DataFrame, str | None]:
    """Execute analytical operation for any of the 40 questions.

    Returns:
        (plotly_figure, analytical_insights, supporting_table, error_message)
    """
    if isinstance(question_or_id, str):
        q_meta = get_question_by_id(question_or_id)
        if not q_meta:
            return None, [], pd.DataFrame(), f"Question ID '{question_or_id}' not found."
    else:
        q_meta = question_or_id

    qid = q_meta.get("id", "").upper().strip()
    title = f"{qid}: {q_meta.get('title', '')}"

    if df is None or df.empty:
        return None, ["Dataset is empty or filter selection yielded 0 rows."], pd.DataFrame(), "Empty dataset."

    # Validate required columns
    required_cols = q_meta.get("required_cols", [])
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        return None, [f"Missing required columns: {', '.join(missing_cols)}"], pd.DataFrame(), f"Missing columns: {missing_cols}"

    table = pd.DataFrame()
    insights: list[str] = []
    y1, y2 = comparison_years

    # -------------------------------------------------------------------------
    # Route by Question ID
    # -------------------------------------------------------------------------
    if qid == "Q1":
        table, insights = analyze_q1_institution_trajectory(df, institution_name=institution, category=category)
    elif qid == "Q2":
        table, insights = analyze_q2_greatest_rank_improvement(df, category=category)
    elif qid == "Q3":
        table, insights = analyze_q3_largest_rank_decline(df, category=category)
    elif qid == "Q4":
        table, insights = analyze_q4_avg_score_over_time(df, category=category)
    elif qid == "Q5":
        table, insights = analyze_q5_persistent_top_10(df, category=category)

    elif qid == "Q6":
        table, insights = analyze_q6_states_top_100(df, year=year, category=category)
    elif qid == "Q7":
        table, insights = analyze_q7_geo_distribution_change(df, category=category)
    elif qid == "Q8":
        table, insights = analyze_q8_states_improving_top_100(df, category=category, year_start=y1, year_end=y2)
    elif qid == "Q9":
        table, insights = analyze_q9_karnataka_vs_tamil_nadu(df, year=year, category=category)
    elif qid == "Q10":
        table, insights = analyze_q10_states_new_entrants(df, category=category)

    elif qid == "Q11":
        table, insights = analyze_q11_score_distribution_year(df, year=year, category=category)
    elif qid == "Q12":
        table, insights = analyze_q12_rank_distribution(df, year=year, category=category)
    elif qid == "Q13":
        table, insights = analyze_q13_score_summary_stats(df, year=year, category=category)
    elif qid == "Q14":
        table, insights = analyze_q14_score_quartile_percentage(df, year=year, category=category)
    elif qid == "Q15":
        table, insights = analyze_q15_score_distribution_by_category(df, year=year)

    elif qid == "Q16":
        table, insights = analyze_q16_rpc_vs_score(df, year=year, category=category)
    elif qid == "Q17":
        table, insights = analyze_q17_perception_vs_score(df, year=year, category=category)
    elif qid == "Q18":
        table, insights = analyze_q18_strongest_param_correlation(df, year=year, category=category)
    elif qid == "Q19":
        table, insights = analyze_q19_tlr_vs_rpc(df, year=year, category=category)
    elif qid == "Q20":
        table, insights = analyze_q20_research_correlation_evolution(df, category=category)

    elif qid == "Q21":
        table, insights = analyze_q21_top_5_all_parameters(df, year=year, category=category)
    elif qid == "Q22":
        table, insights = analyze_q22_high_rpc_low_tlr(df, year=year, category=category)
    elif qid == "Q23":
        table, insights = analyze_q23_high_tlr_low_perception(df, year=year, category=category)
    elif qid == "Q24":
        table, insights = analyze_q24_improved_score_declined_params(df, category=category, year_start=y1, year_end=y2)
    elif qid == "Q25":
        table, insights = analyze_q25_largest_parameter_gap(df, year=year, category=category)

    elif qid == "Q26":
        table, insights = analyze_q26_top_10_vs_remaining(df, year=year, category=category)
    elif qid == "Q27":
        table, insights = analyze_q27_score_dispersion_two_years(df, category=category, year_1=y1, year_2=y2)
    elif qid == "Q28":
        table, insights = analyze_q28_parameter_greatest_variability(df, year=year, category=category)
    elif qid == "Q29":
        table, insights = analyze_q29_median_iqr_over_time(df, category=category)
    elif qid == "Q30":
        table, insights = analyze_q30_score_distribution_across_states(df, year=year, category=category)

    elif qid == "Q31":
        table, insights = analyze_q31_transition_51_100_to_top_50(df, category=category, year_start=y1, year_end=y2)
    elif qid == "Q32":
        table, insights = analyze_q32_top_10_entrants_exits(df, category=category, year_start=y1, year_end=y2)
    elif qid == "Q33":
        table, insights = analyze_q33_same_rank_band_percentage(df, category=category, year_start=y1, year_end=y2)
    elif qid == "Q34":
        table, insights = analyze_q34_largest_rank_movements(df, category=category, year_start=y1, year_end=y2)
    elif qid == "Q35":
        table, insights = analyze_q35_annual_rank_movement_summary(df, category=category)

    elif qid == "Q36":
        table, insights = analyze_q36_high_rpc_relative_to_score(df, year=year, category=category)
    elif qid == "Q37":
        table, insights = analyze_q37_research_substantially_better_teaching(df, year=year, category=category)
    elif qid == "Q38":
        table, insights = analyze_q38_unusual_yoy_score_changes(df, category=category)
    elif qid == "Q39":
        table, insights = analyze_q39_strong_params_poor_rank(df, year=year, category=category)
    elif qid == "Q40":
        table, insights = analyze_q40_high_ranking_volatility_outliers(df, category=category)
    else:
        return None, [f"Question operation for '{qid}' is not recognized."], pd.DataFrame(), "Unknown question."

    fig = build_question_chart(qid, table, title=title)

    return fig, insights, table, None


# Backward compatibility wrapper for existing calls:
def execute_question_analysis(
    question: dict[str, Any],
    data: pd.DataFrame,
) -> tuple[Any, list[str], pd.DataFrame]:
    """Backward-compatible entry point returning (fig, insights, table)."""
    fig, insights, table, _ = execute_question(question, data)
    return fig, insights, table
