"""
NIRF Insight — Tool Registry for Chatbot
=========================================
Declares official OpenAI function-calling tool schemas for controlled,
whitelisted analytics operations on the NIRF dataset.
"""

from typing import Any

ANALYTICS_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_dataset_summary",
            "description": "Get high-level summary of the NIRF dataset including record count, year span, categories, and states.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_years",
            "description": "Get all NIRF ranking edition years present in the dataset (2017 to 2025).",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_columns",
            "description": "Get all valid dataset column names and their descriptions (Score, Rank, TLR, RPC, GO, OI, Perception, etc.).",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_institutions",
            "description": "Retrieve the top N institutions filtered by category, year, or state, sorted by Score (highest first) or Rank.",
            "parameters": {
                "type": "object",
                "properties": {
                    "n": {"type": "integer", "description": "Number of institutions to return (e.g. 5, 10, 20). Default is 10."},
                    "year": {"type": "integer", "description": "Specific ranking year (2017-2025). Default is latest (2025)."},
                    "category": {"type": "string", "description": "Discipline category (e.g. 'Overall', 'Engineering', 'Management', 'University', 'College', 'Pharmacy', 'Medical'). Default is 'Overall'."},
                    "state": {"type": "string", "description": "Optional state filter (e.g. 'Tamil Nadu', 'Karnataka', 'Delhi', 'Maharashtra')."},
                    "sort_by": {"type": "string", "enum": ["Score", "Rank", "TLR", "RPC", "GO", "OI", "Perception"], "description": "Metric to sort by. Default is 'Score'."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_institution_details",
            "description": "Retrieve historical ranks, scores, and 5-pillar parameter metrics for a specific institution across years.",
            "parameters": {
                "type": "object",
                "properties": {
                    "institution_name": {"type": "string", "description": "Exact or partial name of the institution (e.g. 'IIT Madras', 'IISc', 'IIT Bombay')."},
                    "category": {"type": "string", "description": "Discipline category (e.g. 'Overall', 'Engineering'). Default is 'Overall'."},
                    "year": {"type": "integer", "description": "Optional year filter if querying a single edition."},
                },
                "required": ["institution_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_institutions",
            "description": "Compare 2 or more institutions side-by-side in terms of Score, Rank, and the 5 parameters (TLR, RPC, GO, OI, Perception).",
            "parameters": {
                "type": "object",
                "properties": {
                    "institutions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of institution names to compare (e.g. ['IIT Madras', 'IIT Delhi', 'IIT Bombay']).",
                    },
                    "year": {"type": "integer", "description": "Comparison year. Default is latest (2025)."},
                    "category": {"type": "string", "description": "Discipline category. Default is 'Overall'."},
                },
                "required": ["institutions"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_yearly_trends",
            "description": "Analyze longitudinal trend of average Score, Rank, or a parameter over the years 2017 to 2025.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Optional category filter."},
                    "institution_name": {"type": "string", "description": "Optional institution name to track its specific trend."},
                    "metric": {"type": "string", "enum": ["Score", "Rank", "TLR", "RPC", "GO", "OI", "Perception"], "description": "Metric to track. Default is 'Score'."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_state_analysis",
            "description": "Analyze institution distribution, counts, average scores, and top performers across Indian states.",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {"type": "string", "description": "Specific state to analyze, or omit to get national state ranking."},
                    "year": {"type": "integer", "description": "Specific year (default 2025)."},
                    "category": {"type": "string", "description": "Specific category (default 'Overall')."},
                    "top_n_states": {"type": "integer", "description": "Number of top states to return if ranking states. Default 10."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_category_analysis",
            "description": "Compare average scores, participation counts, and parameter benchmarks across NIRF categories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "Specific year (default 2025)."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_parameter_analysis",
            "description": "Analyze the 5 NIRF pillar parameters (TLR, RPC, GO, OI, Perception) - find top performers, averages, or correlations with overall Score.",
            "parameters": {
                "type": "object",
                "properties": {
                    "parameter": {"type": "string", "enum": ["TLR", "RPC", "GO", "OI", "Perception"], "description": "The specific pillar parameter to analyze."},
                    "year": {"type": "integer", "description": "Ranking year (default 2025)."},
                    "category": {"type": "string", "description": "Category (default 'Overall')."},
                    "top_n": {"type": "integer", "description": "Number of top institutions in this parameter to retrieve. Default 10."},
                },
                "required": ["parameter"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_score_statistics",
            "description": "Calculate exact five-number summary (min, Q1, median, Q3, max), mean, standard deviation, and IQR of scores for a given year and category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "Specific ranking year (default 2025)."},
                    "category": {"type": "string", "description": "Specific category (default 'Overall')."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_correlation_analysis",
            "description": "Calculate Pearson and Spearman correlation between two numeric variables (e.g. RPC vs Score, TLR vs RPC).",
            "parameters": {
                "type": "object",
                "properties": {
                    "col1": {"type": "string", "description": "First numeric column (e.g. 'RPC', 'TLR', 'Perception')."},
                    "col2": {"type": "string", "description": "Second numeric column (e.g. 'Score', 'Rank', 'RPC'). Default 'Score'."},
                    "year": {"type": "integer", "description": "Optional year filter."},
                    "category": {"type": "string", "description": "Optional category filter (default 'Overall')."},
                },
                "required": ["col1"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_rank_changes",
            "description": "Identify biggest rank climbers or largest decliners between two years within a category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Category (default 'Overall')."},
                    "year_start": {"type": "integer", "description": "Initial year (e.g. 2024 or 2017)."},
                    "year_end": {"type": "integer", "description": "Final year (e.g. 2025)."},
                    "direction": {"type": "string", "enum": ["climbers", "decliners"], "description": "Direction of rank movement. Default 'climbers'."},
                    "top_n": {"type": "integer", "description": "Number of institutions to return. Default 10."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_distribution_analysis",
            "description": "Analyze score or rank distribution, quartiles, or score tiers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric": {"type": "string", "enum": ["Score", "Rank", "TLR", "RPC", "GO", "OI", "Perception"], "description": "Metric to analyze distribution for. Default 'Score'."},
                    "year": {"type": "integer", "description": "Specific year (default 2025)."},
                    "category": {"type": "string", "description": "Specific category (default 'Overall')."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_filtered_dataset_summary",
            "description": "Execute arbitrary filtered cohort summary across year, category, state, rank range, and score range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "Year filter."},
                    "category": {"type": "string", "description": "Category filter."},
                    "state": {"type": "string", "description": "State filter."},
                    "min_score": {"type": "number", "description": "Minimum score filter."},
                    "max_rank": {"type": "integer", "description": "Maximum rank cutoff (e.g. 50, 100)."},
                },
            },
        },
    },
]
