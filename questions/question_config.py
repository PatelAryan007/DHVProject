"""
NIRF Insight — Question Configuration & Analytical Metadata
===========================================================
Defines the official 40 analytical questions organized into 8 domains,
annotated with exact titles, questions, required dataset columns,
supported filter types, recommended chart types, operations, and analytical rules.
"""

from typing import Any

QUESTION_DOMAINS: dict[str, dict[str, Any]] = {
    "Time-Series and Trend Analysis": {
        "icon": "📈",
        "description": "Analyze longitudinal trends, institutional trajectories, score evolution, and persistent leaders across 2017–2025.",
        "questions": [
            {
                "id": "Q1",
                "domain": "Time-Series and Trend Analysis",
                "title": "Institutional Ranking Trajectory",
                "question": "How has the overall NIRF ranking of a selected institution changed from 2017 to 2025?",
                "operation": "INSTITUTION_RANK_TRAJECTORY",
                "chart_type": "line",
                "required_cols": ["Year", "Name", "Rank", "Score", "Category"],
                "supported_filters": ["institution", "category"],
                "analytical_rules": [
                    "Tracks an institution's rank over available years within a consistent category.",
                    "Lower numerical rank indicates better performance; Y-axis is inverted for intuitive ranking presentation.",
                    "Years where an institution did not participate are preserved as gaps rather than zero ranks.",
                ],
            },
            {
                "id": "Q2",
                "domain": "Time-Series and Trend Analysis",
                "title": "Greatest Rank Improvement Over Time",
                "question": "Which institutions have shown the greatest improvement in rank over nine years?",
                "operation": "GREATEST_RANK_IMPROVEMENT",
                "chart_type": "bar",
                "required_cols": ["Year", "Name", "Rank", "Category"],
                "supported_filters": ["category"],
                "analytical_rules": [
                    "Rank improvement = Initial_Rank - Final_Rank (positive delta represents an upward climb in standings).",
                    "Evaluates matched institutions participating across at least 2 years in the same category.",
                    "Only compares within the same category to maintain ranking validity.",
                ],
            },
            {
                "id": "Q3",
                "domain": "Time-Series and Trend Analysis",
                "title": "Largest Rank Decline Over Time",
                "question": "Which institutions have experienced the largest decline in rank?",
                "operation": "LARGEST_RANK_DECLINE",
                "chart_type": "bar",
                "required_cols": ["Year", "Name", "Rank", "Category"],
                "supported_filters": ["category"],
                "analytical_rules": [
                    "Rank decline = Final_Rank - Initial_Rank (higher positive number indicates dropping to a worse/higher numerical rank).",
                    "Requires multi-year presence in the same category.",
                    "Does not penalize or fabricate ranks for missing years.",
                ],
            },
            {
                "id": "Q4",
                "domain": "Time-Series and Trend Analysis",
                "title": "Average NIRF Score Trend Over Time",
                "question": "How has the average NIRF score changed over time?",
                "operation": "AVG_SCORE_OVER_TIME",
                "chart_type": "line",
                "required_cols": ["Year", "Score", "Category"],
                "supported_filters": ["category"],
                "analytical_rules": [
                    "Computes annual mean and median scores across ranked institutions.",
                    "Excludes categories without published numeric scores (e.g., Innovation, SDG).",
                    "Averages reflect cohort-level movement over 2017–2025.",
                ],
            },
            {
                "id": "Q5",
                "domain": "Time-Series and Trend Analysis",
                "title": "Persistent Top 10 Institutions",
                "question": "Which institutions have consistently remained in the top 10 across multiple years?",
                "operation": "PERSISTENT_TOP_10",
                "chart_type": "bar",
                "required_cols": ["Year", "Name", "Rank", "Category"],
                "supported_filters": ["category"],
                "analytical_rules": [
                    "Identifies institutions achieving Rank <= 10 in multiple ranking editions.",
                    "Highlights elite institutions retaining top 10 status across all participating years.",
                ],
            },
        ],
    },
    "Geospatial and Regional Analysis": {
        "icon": "🗺️",
        "description": "Evaluate state-wise representation, regional clusters, interstate comparisons, and geographic trends.",
        "questions": [
            {
                "id": "Q6",
                "domain": "Geospatial and Regional Analysis",
                "title": "States with Highest Top 100 Institutions",
                "question": "Which states have the highest number of institutions in the top 100?",
                "operation": "STATES_TOP_100_COUNT",
                "chart_type": "bar",
                "required_cols": ["State", "Rank", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Filters institutions with Rank <= 100 in the selected year and category.",
                    "Standardizes state names to prevent duplicate geographic tallies.",
                ],
            },
            {
                "id": "Q7",
                "domain": "Geospatial and Regional Analysis",
                "title": "Geographical Distribution Change (2017–2025)",
                "question": "How has the geographical distribution of top-ranked institutions changed from 2017 to 2025?",
                "operation": "GEO_DISTRIBUTION_CHANGE",
                "chart_type": "line",
                "required_cols": ["State", "Rank", "Year", "Category"],
                "supported_filters": ["category"],
                "analytical_rules": [
                    "Tracks the annual count of Top 100 institutions for the leading states across all 9 years.",
                    "Reveals shifting regional concentration and decentralization over time.",
                ],
            },
            {
                "id": "Q8",
                "domain": "Geospatial and Regional Analysis",
                "title": "States Improving Top 100 Representation",
                "question": "Which states have improved their representation in the top 100 over the years?",
                "operation": "STATES_IMPROVING_TOP_100",
                "chart_type": "bar",
                "required_cols": ["State", "Rank", "Year", "Category"],
                "supported_filters": ["category", "comparison_years"],
                "analytical_rules": [
                    "Calculates net change in Top 100 institution count between baseline and target years.",
                    "Positive delta indicates growing regional higher-education strength.",
                ],
            },
            {
                "id": "Q9",
                "domain": "Geospatial and Regional Analysis",
                "title": "Karnataka vs Tamil Nadu Ranking Comparison",
                "question": "How do institutions in Karnataka compare with institutions in Tamil Nadu in terms of NIRF rankings?",
                "operation": "KARNATAKA_VS_TAMIL_NADU",
                "chart_type": "box",
                "required_cols": ["State", "Score", "Rank", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Compares key southern education powerhouses: Karnataka and Tamil Nadu.",
                    "Analyzes score distribution, rank dispersion, and total institutions represented.",
                ],
            },
            {
                "id": "Q10",
                "domain": "Geospatial and Regional Analysis",
                "title": "States with Largest Newly Appearing Institutions",
                "question": "Which states have the largest number of newly appearing institutions in the rankings?",
                "operation": "STATES_NEW_ENTRANTS",
                "chart_type": "bar",
                "required_cols": ["State", "Name", "Year", "Category"],
                "supported_filters": ["category"],
                "analytical_rules": [
                    "Defines newly appearing as an institution's first observed appearance in the 2017–2025 dataset.",
                    "Does not assume new establishment, solely first entry into published NIRF rankings.",
                ],
            },
        ],
    },
    "Univariate Analysis": {
        "icon": "📊",
        "description": "Single-variable distributions, five-number summaries, score spreads, and quartile distributions.",
        "questions": [
            {
                "id": "Q11",
                "domain": "Univariate Analysis",
                "title": "NIRF Score Distribution in Selected Year",
                "question": "What is the distribution of NIRF scores for institutions in a selected year?",
                "operation": "SCORE_DISTRIBUTION_YEAR",
                "chart_type": "histogram",
                "required_cols": ["Score", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Calculates parametric and non-parametric dispersion: mean, median, standard deviation, IQR.",
                    "Only considers institutions with published numeric scores.",
                ],
            },
            {
                "id": "Q12",
                "domain": "Univariate Analysis",
                "title": "Overall Rank Distribution Across Institutions",
                "question": "How are overall ranks distributed across institutions?",
                "operation": "RANK_DISTRIBUTION",
                "chart_type": "histogram",
                "required_cols": ["Rank", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Analyzes rank frequency, rank bands, and tie occurrences.",
                    "Respects category ranking spans (e.g. top 50, top 100, top 200).",
                ],
            },
            {
                "id": "Q13",
                "domain": "Univariate Analysis",
                "title": "Summary Statistics of Scores (Avg, Median, Min, Max)",
                "question": "What are the average, median, minimum and maximum NIRF scores in a given year?",
                "operation": "SCORE_SUMMARY_STATS",
                "chart_type": "box",
                "required_cols": ["Score", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Provides exact five-number summary plus Mean, Std Dev, and IQR.",
                    "Compares central tendency (mean vs median) to assess distribution skewness.",
                ],
            },
            {
                "id": "Q14",
                "domain": "Univariate Analysis",
                "title": "Institution Share by Score Quartile",
                "question": "What percentage of ranked institutions fall into each score quartile?",
                "operation": "SCORE_QUARTILE_PERCENTAGE",
                "chart_type": "pie",
                "required_cols": ["Score", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Divides scores into four empirical quartiles: Q1 (0-25%), Q2 (25-50%), Q3 (50-75%), Q4 (75-100%).",
                    "Displays institution counts and percentages within each quartile segment.",
                ],
            },
            {
                "id": "Q15",
                "domain": "Univariate Analysis",
                "title": "Score Distribution Across Categories",
                "question": "How does the distribution of NIRF scores vary across different NIRF categories?",
                "operation": "SCORE_DISTRIBUTION_BY_CATEGORY",
                "chart_type": "box",
                "required_cols": ["Score", "Category", "Year"],
                "supported_filters": ["year"],
                "analytical_rules": [
                    "Compares score spreads and median thresholds across all evaluated institutional categories.",
                    "Excludes categories without published numeric scores.",
                ],
            },
        ],
    },
    "Bivariate and Correlation Analysis": {
        "icon": "🔗",
        "description": "Linear and rank correlations, scatter relationships, regression trends, and parameter interactions.",
        "questions": [
            {
                "id": "Q16",
                "domain": "Bivariate and Correlation Analysis",
                "title": "Association Between RPC and Overall Score",
                "question": "Is there an association between RPC scores and overall NIRF scores?",
                "operation": "RPC_VS_SCORE_CORRELATION",
                "chart_type": "scatter",
                "required_cols": ["RPC", "Score", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Calculates Pearson r and Spearman rho between Research (RPC) and Overall Score.",
                    "Includes linear regression trendline with hover details.",
                ],
            },
            {
                "id": "Q17",
                "domain": "Bivariate and Correlation Analysis",
                "title": "Perception vs Overall NIRF Score Relationship",
                "question": "How are Perception scores related to overall NIRF scores?",
                "operation": "PERCEPTION_VS_SCORE_CORRELATION",
                "chart_type": "scatter",
                "required_cols": ["Perception", "Score", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Examines whether academic/employer perception matches total evaluated score.",
                    "Measures correlation strength and highlights perception outliers.",
                ],
            },
            {
                "id": "Q18",
                "domain": "Bivariate and Correlation Analysis",
                "title": "Parameter with Strongest Score Correlation",
                "question": "Which NIRF parameter has the strongest correlation with the overall NIRF score?",
                "operation": "STRONGEST_PARAM_CORRELATION",
                "chart_type": "bar",
                "required_cols": ["Score", "TLR", "RPC", "GO", "OI", "Perception", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Ranks all 5 parameters (TLR, RPC, GO, OI, Perception) by Pearson and Spearman correlation with Score.",
                    "Identifies the primary statistical driver of NIRF overall ranking.",
                ],
            },
            {
                "id": "Q19",
                "domain": "Bivariate and Correlation Analysis",
                "title": "Relationship Between TLR and RPC Scores",
                "question": "What is the relationship between TLR and RPC scores?",
                "operation": "TLR_VS_RPC_RELATIONSHIP",
                "chart_type": "scatter",
                "required_cols": ["TLR", "RPC", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Investigates the synergy or trade-off between Teaching/Resources (TLR) and Research (RPC).",
                    "Computes bivariate correlation coefficient and regression line.",
                ],
            },
            {
                "id": "Q20",
                "domain": "Bivariate and Correlation Analysis",
                "title": "Research vs Score Correlation Evolution (2017–2025)",
                "question": "Has the correlation between research-related scores and overall NIRF scores changed from 2017 to 2025?",
                "operation": "RESEARCH_CORRELATION_EVOLUTION",
                "chart_type": "line",
                "required_cols": ["RPC", "Score", "Year", "Category"],
                "supported_filters": ["category"],
                "analytical_rules": [
                    "Calculates annual Pearson r between RPC and Score for each year from 2017 to 2025.",
                    "Plots correlation coefficient trend over the 9-year historical horizon.",
                ],
            },
        ],
    },
    "Multivariate Analysis": {
        "icon": "🔬",
        "description": "Multi-parameter composites, radar profiles, parameter gaps, and holistic institutional comparisons.",
        "questions": [
            {
                "id": "Q21",
                "domain": "Multivariate Analysis",
                "title": "Top 5 Institutions Across All Five Parameters",
                "question": "Which are the top five institutions based on their performance across all five NIRF parameters?",
                "operation": "TOP_5_ALL_PARAMETERS",
                "chart_type": "radar",
                "required_cols": ["TLR", "RPC", "GO", "OI", "Perception", "Name", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Computes a transparent composite score as the equal-weighted average of all 5 parameters: (TLR + RPC + GO + OI + Perception) / 5.",
                    "Excludes institutions with missing parameter records (does not treat missing values as zero).",
                    "Renders a comparative multi-institution radar chart.",
                ],
            },
            {
                "id": "Q22",
                "domain": "Multivariate Analysis",
                "title": "High Research vs Relatively Low Teaching Institutions",
                "question": "Which institutions have high research scores but relatively low teaching scores?",
                "operation": "HIGH_RPC_LOW_TLR",
                "chart_type": "bar",
                "required_cols": ["RPC", "TLR", "Name", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Calculates the Research-Teaching gap: Delta = RPC - TLR.",
                    "Identifies institutions with the largest positive delta (research-focused institutions with lower teaching scores).",
                ],
            },
            {
                "id": "Q23",
                "domain": "Multivariate Analysis",
                "title": "High Teaching vs Relatively Low Perception Institutions",
                "question": "Which institutions have high teaching scores but relatively low perception scores?",
                "operation": "HIGH_TLR_LOW_PERCEPTION",
                "chart_type": "bar",
                "required_cols": ["TLR", "Perception", "Name", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Calculates the Teaching-Perception gap: Delta = TLR - Perception.",
                    "Highlights institutions excelling in pedagogy and infrastructure that have not yet achieved commensurate public perception.",
                ],
            },
            {
                "id": "Q24",
                "domain": "Multivariate Analysis",
                "title": "Score Improvement Despite Parameter Decline",
                "question": "Which institutions have improved their overall scores despite declining in one or more parameters?",
                "operation": "IMPROVED_SCORE_DECLINED_PARAMS",
                "chart_type": "bar",
                "required_cols": ["Score", "TLR", "RPC", "GO", "OI", "Perception", "Name", "Year", "Category"],
                "supported_filters": ["category", "comparison_years"],
                "analytical_rules": [
                    "Identifies institutions where Overall Score increased (Score_t2 > Score_t1) but at least one pillar parameter decreased.",
                    "Documents compensatory mechanics where strong gains in one parameter offset losses in another.",
                ],
            },
            {
                "id": "Q25",
                "domain": "Multivariate Analysis",
                "title": "Largest Gap Between Strongest and Weakest Parameters",
                "question": "Which institutions have the largest gap between their strongest and weakest NIRF parameters?",
                "operation": "LARGEST_PARAMETER_GAP",
                "chart_type": "bar",
                "required_cols": ["TLR", "RPC", "GO", "OI", "Perception", "Name", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Computes Parameter Gap = max(TLR, RPC, GO, OI, Perception) - min(TLR, RPC, GO, OI, Perception).",
                    "Ranks institutions with the most asymmetrical / unbalanced parameter profiles.",
                ],
            },
        ],
    },
    "Distribution and Statistical Analysis": {
        "icon": "📉",
        "description": "Comparative dispersion, variance analysis, median and IQR dynamics, and interstate spread.",
        "questions": [
            {
                "id": "Q26",
                "domain": "Distribution and Statistical Analysis",
                "title": "Top 10 vs Remaining Institutions Score Comparison",
                "question": "How does the score distribution of top 10 institutions compare with the remaining institutions?",
                "operation": "TOP_10_VS_REMAINING_SCORES",
                "chart_type": "box",
                "required_cols": ["Rank", "Score", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Partitions institutions into 'Top 10' (Rank <= 10) and 'Remaining' (Rank > 10).",
                    "Compares statistical distributions, medians, and IQRs between the two cohorts.",
                ],
            },
            {
                "id": "Q27",
                "domain": "Distribution and Statistical Analysis",
                "title": "Score Dispersion Comparison Between Two Years",
                "question": "Are NIRF scores more dispersed in one year compared with another?",
                "operation": "SCORE_DISPERSION_TWO_YEARS",
                "chart_type": "box",
                "required_cols": ["Score", "Year", "Category"],
                "supported_filters": ["category", "comparison_years"],
                "analytical_rules": [
                    "Compares standard deviation, variance, and IQR between two selected ranking editions.",
                    "Determines whether the score gap among institutions is expanding or compressing.",
                ],
            },
            {
                "id": "Q28",
                "domain": "Distribution and Statistical Analysis",
                "title": "NIRF Parameter with Greatest Variability",
                "question": "Which NIRF parameter shows the greatest variability?",
                "operation": "PARAMETER_GREATEST_VARIABILITY",
                "chart_type": "bar",
                "required_cols": ["TLR", "RPC", "GO", "OI", "Perception", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Calculates standard deviation and coefficient of variation (CV = std / mean) for all 5 parameters.",
                    "Identifies which parameter exhibits the widest variance across institutions.",
                ],
            },
            {
                "id": "Q29",
                "domain": "Distribution and Statistical Analysis",
                "title": "Median and IQR Dynamics Over Time",
                "question": "How have the median and interquartile range of NIRF scores changed over time?",
                "operation": "MEDIAN_IQR_OVER_TIME",
                "chart_type": "line",
                "required_cols": ["Score", "Year", "Category"],
                "supported_filters": ["category"],
                "analytical_rules": [
                    "Calculates median and IQR (Q3 - Q1) of NIRF scores for each year from 2017 to 2025.",
                    "Plots longitudinal median score progression alongside dispersion bands.",
                ],
            },
            {
                "id": "Q30",
                "domain": "Distribution and Statistical Analysis",
                "title": "Score Distribution Variation Across States",
                "question": "How does the distribution of NIRF scores vary across states?",
                "operation": "SCORE_DISTRIBUTION_ACROSS_STATES",
                "chart_type": "box",
                "required_cols": ["State", "Score", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Compares score spreads across states with at least 3 ranked institutions.",
                    "Identifies states with tight clusters vs high intra-state performance disparity.",
                ],
            },
        ],
    },
    "Ranking Transitions and Mobility": {
        "icon": "🔄",
        "description": "Rank band transitions, top 10 entry/exit dynamics, persistence rates, and annual movement breakdowns.",
        "questions": [
            {
                "id": "Q31",
                "domain": "Ranking Transitions and Mobility",
                "title": "Movement from Rank 51–100 into Top 50",
                "question": "How many institutions moved from the 51–100 rank band into the top 50 between two selected years?",
                "operation": "TRANSITION_51_100_TO_TOP_50",
                "chart_type": "bar",
                "required_cols": ["Rank", "Name", "Year", "Category"],
                "supported_filters": ["category", "comparison_years"],
                "analytical_rules": [
                    "Identifies institutions ranked between 51 and 100 in Year 1 that achieved Rank <= 50 in Year 2.",
                    "Compares matched institutions within the same category.",
                ],
            },
            {
                "id": "Q32",
                "domain": "Ranking Transitions and Mobility",
                "title": "Top 10 Entrants and Exits",
                "question": "Which institutions entered or exited the top 10 between consecutive years?",
                "operation": "TOP_10_ENTRANTS_EXITS",
                "chart_type": "bar",
                "required_cols": ["Rank", "Name", "Year", "Category"],
                "supported_filters": ["category", "comparison_years"],
                "analytical_rules": [
                    "New Entrant: Rank > 10 (or unranked) in Year 1, but Rank <= 10 in Year 2.",
                    "Exit: Rank <= 10 in Year 1, but Rank > 10 (or unranked) in Year 2.",
                ],
            },
            {
                "id": "Q33",
                "domain": "Ranking Transitions and Mobility",
                "title": "Percentage Remaining in the Same Rank Band",
                "question": "What percentage of institutions remained in the same rank band between two selected years?",
                "operation": "SAME_RANK_BAND_PERCENTAGE",
                "chart_type": "pie",
                "required_cols": ["Rank", "Name", "Year", "Category"],
                "supported_filters": ["category", "comparison_years"],
                "analytical_rules": [
                    "Defines standard NIRF rank bands: 1–10, 11–25, 26–50, 51–100, 101+.",
                    "Calculates the percentage of institutions that remained in their original tier.",
                ],
            },
            {
                "id": "Q34",
                "domain": "Ranking Transitions and Mobility",
                "title": "Largest Upward and Downward Rank Movements",
                "question": "Which institutions experienced the largest upward or downward movements in rank?",
                "operation": "LARGEST_RANK_MOVEMENTS",
                "chart_type": "bar",
                "required_cols": ["Rank", "Name", "Year", "Category"],
                "supported_filters": ["category", "comparison_years"],
                "analytical_rules": [
                    "Rank Movement = Rank_Year1 - Rank_Year2. Positive = climbed up; Negative = dropped down.",
                    "Displays top gainers and decliners side-by-side.",
                ],
            },
            {
                "id": "Q35",
                "domain": "Ranking Transitions and Mobility",
                "title": "Annual Count of Improved, Declined, and Retained Ranks",
                "question": "How many institutions improved, declined or retained their ranking positions each year?",
                "operation": "ANNUAL_RANK_MOVEMENT_SUMMARY",
                "chart_type": "bar",
                "required_cols": ["Rank", "Name", "Year", "Category"],
                "supported_filters": ["category"],
                "analytical_rules": [
                    "Evaluates all adjacent year pairs (2017-18, 2018-19, ..., 2024-25).",
                    "Tallies institutions with Improved, Declined, or Retained ranks.",
                ],
            },
        ],
    },
    "Outlier and Performance Gap Analysis": {
        "icon": "🎯",
        "description": "Statistical anomaly detection, score jumps, parameter imbalances, and ranking volatility outliers.",
        "questions": [
            {
                "id": "Q36",
                "domain": "Outlier and Performance Gap Analysis",
                "title": "Unusually High Research Relative to Overall Score",
                "question": "Which institutions have unusually high research scores relative to their overall scores?",
                "operation": "HIGH_RPC_RELATIVE_TO_SCORE",
                "chart_type": "scatter",
                "required_cols": ["RPC", "Score", "Name", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Calculates RPC-to-Score ratio and detects statistical outliers exceeding 1.5 * IQR above the median ratio.",
                    "Highlights institutions with research output far outpacing their overall institutional standing.",
                ],
            },
            {
                "id": "Q37",
                "domain": "Outlier and Performance Gap Analysis",
                "title": "Substantially Better Research Than Teaching",
                "question": "Which institutions perform substantially better in research than in teaching?",
                "operation": "RESEARCH_SUBSTANTIALLY_BETTER_TEACHING",
                "chart_type": "bar",
                "required_cols": ["RPC", "TLR", "Name", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Identifies institutions where (RPC - TLR) exceeds a substantial threshold (e.g. > 15 points).",
                    "Ranks institutions by research dominance over teaching metrics.",
                ],
            },
            {
                "id": "Q38",
                "domain": "Outlier and Performance Gap Analysis",
                "title": "Unusually Large Year-to-Year Score Changes",
                "question": "Which institutions have unusually large year-to-year changes in NIRF scores?",
                "operation": "UNUSUAL_YOY_SCORE_CHANGES",
                "chart_type": "scatter",
                "required_cols": ["Score", "Name", "Year", "Category"],
                "supported_filters": ["category"],
                "analytical_rules": [
                    "Computes annual score change |Score_t - Score_t-1| across consecutive years.",
                    "Flags anomalous fluctuations exceeding 1.5 * IQR of the delta distribution.",
                ],
            },
            {
                "id": "Q39",
                "domain": "Outlier and Performance Gap Analysis",
                "title": "Strong Parameters But Relatively Poor Overall Rank",
                "question": "Which institutions have strong scores in one or more parameters but relatively poor overall rankings?",
                "operation": "STRONG_PARAMS_POOR_RANK",
                "chart_type": "bar",
                "required_cols": ["Rank", "TLR", "RPC", "GO", "OI", "Perception", "Name", "Year", "Category"],
                "supported_filters": ["year", "category"],
                "analytical_rules": [
                    "Identifies institutions possessing at least one parameter score >= 75th percentile while having a Rank > 50.",
                    "Exposes institutional pockets of excellence obscured by lower overall composite ranking.",
                ],
            },
            {
                "id": "Q40",
                "domain": "Outlier and Performance Gap Analysis",
                "title": "Unusually High Ranking Volatility",
                "question": "Which institutions show unusually high ranking volatility compared with similar institutions?",
                "operation": "HIGH_RANKING_VOLATILITY_OUTLIERS",
                "chart_type": "bar",
                "required_cols": ["Rank", "Name", "Year", "Category"],
                "supported_filters": ["category"],
                "analytical_rules": [
                    "Computes standard deviation of ranks for institutions with >= 3 participating years.",
                    "Detects statistical outliers exceeding Q3 + 1.5 * IQR of the category volatility distribution.",
                ],
            },
        ],
    },
}

# ---------------------------------------------------------------------------
# Flat Helpers
# ---------------------------------------------------------------------------

def get_all_questions() -> list[dict[str, Any]]:
    """Return flat list of all 40 questions."""
    flat = []
    for domain_name, data in QUESTION_DOMAINS.items():
        for q in data["questions"]:
            q_copy = q.copy()
            q_copy["domain_icon"] = data["icon"]
            flat.append(q_copy)
    return flat


def get_question_by_id(question_id: str) -> dict[str, Any] | None:
    """Retrieve question definition by unique question ID (e.g. 'Q1'..'Q40')."""
    target = question_id.upper().strip()
    for domain_name, data in QUESTION_DOMAINS.items():
        for q in data["questions"]:
            if q["id"].upper() == target:
                q_copy = q.copy()
                q_copy["domain_icon"] = data["icon"]
                return q_copy
    return None


def get_domain_names() -> list[str]:
    """Ordered list of domain names."""
    return list(QUESTION_DOMAINS.keys())


def get_domain_icon(domain_name: str) -> str:
    """Icon emoji for a given domain."""
    return QUESTION_DOMAINS.get(domain_name, {}).get("icon", "📊")


# Backwards compatibility aliases
QUESTION_CATEGORIES = QUESTION_DOMAINS
get_category_names = get_domain_names
get_category_icon = get_domain_icon


