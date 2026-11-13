"""
NIRF Insight — Chatbot Intent Parser
====================================
Translates natural-language user queries into structured analytics tool calls.
Supports two complementary paths:
1. OpenAI Function Calling: Deep semantic understanding using official OpenAI tool schemas.
2. Intelligent Heuristic Fallback: Robust pattern matching for offline/unconfigured environments.
"""

import json
import re
from typing import Any

from chatbot.llm_service import is_openai_configured, call_openai_chat
from chatbot.tool_registry import ANALYTICS_TOOLS


def parse_intent_with_openai(
    messages: list[dict[str, Any]],
) -> tuple[str | None, dict[str, Any], str | None]:
    """Invoke OpenAI tool calling to determine the appropriate analytics tool and parameters.

    Returns:
        (tool_name, tool_arguments_dict, direct_text_response_if_no_tool)
    """
    system_prompt = {
        "role": "system",
        "content": (
            "You are the NIRF Insight AI Assistant, an expert analytics assistant for the Indian National Institutional Ranking Framework (NIRF) dataset (2017-2025).\n"
            "Your job is to select the single best analytics tool from the provided tools to answer the user's question.\n"
            "If the user asks follow-up questions (e.g. 'Only in Karnataka', 'Compare those', 'What about 2024?'), use the conversation context to fill in parameters.\n"
            "Lower numerical rank means better rank (Rank #1 is top).\n"
            "If the question cannot be answered by any dataset tool, respond politely explaining the dataset scope."
        ),
    }

    formatted_messages = [system_prompt] + messages[-6:]  # Include last 6 turns for context

    resp_message, err = call_openai_chat(
        messages=formatted_messages,
        tools=ANALYTICS_TOOLS,
        tool_choice="auto",
        temperature=0.1,
    )

    if err or not resp_message:
        # Return error flag/message indicating OpenAI call failed so fallback can execute
        return None, {}, None

    # Check for tool calls
    if hasattr(resp_message, "tool_calls") and resp_message.tool_calls:
        tool_call = resp_message.tool_calls[0]
        tool_name = tool_call.function.name
        try:
            tool_args = json.loads(tool_call.function.arguments)
        except Exception:
            tool_args = {}
        return tool_name, tool_args, None

    # Direct response without tool call (e.g. greeting, general explanation)
    content = getattr(resp_message, "content", "") or ""
    return None, {}, content


def parse_intent_heuristically(
    query: str,
    context: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Rule-based semantic parser used as a zero-dependency fallback or when OpenAI is not configured."""
    q_lower = query.lower().strip()
    ctx = context or {}

    # Extract Year (2017 to 2025)
    year_match = re.search(r"\b(201[7-9]|202[0-5])\b", q_lower)
    year = int(year_match.group(1)) if year_match else ctx.get("year", 2025)

    # Extract Category
    categories = [
        "engineering", "management", "university", "college", "pharmacy",
        "medical", "law", "architecture", "dental", "research", "agriculture",
        "innovation", "open university", "skill university", "state public university",
    ]
    detected_cat = ctx.get("category", "Overall")
    for cat in categories:
        if cat in q_lower:
            detected_cat = cat.title()
            break
    if "overall" in q_lower:
        detected_cat = "Overall"

    # Extract State
    states = [
        "tamil nadu", "karnataka", "delhi", "maharashtra", "kerala", "uttar pradesh",
        "telangana", "andhra pradesh", "west bengal", "gujarat", "punjab", "rajasthan",
        "haryana", "odisha", "bihar", "madhya pradesh", "assam", "jammu and kashmir",
    ]
    detected_state = ctx.get("state", None)
    for st in states:
        if st in q_lower:
            detected_state = st.title()
            break

    # Extract top N count (e.g. "top 5", "top 10", "top 20")
    n_match = re.search(r"\btop\s+(\d+)\b", q_lower)
    n_val = int(n_match.group(1)) if n_match else 10

    # 1. Dataset & Overview
    if any(k in q_lower for k in ["dataset summary", "about dataset", "overview", "what data", "how many records"]):
        return "get_dataset_summary", {}

    if any(k in q_lower for k in ["available years", "which years", "years present"]):
        return "get_available_years", {}

    if any(k in q_lower for k in ["available columns", "what fields", "what columns", "parameters list"]):
        return "get_available_columns", {}

    # 2. Correlation
    if any(k in q_lower for k in ["correlation", "relationship between", "associated with", "scatter"]):
        p1 = "RPC"
        p2 = "Score"
        for p in ["tlr", "rpc", "go", "oi", "perception"]:
            if p in q_lower:
                p1 = p.upper()
                break
        return "get_correlation_analysis", {"col1": p1, "col2": p2, "year": year, "category": detected_cat}

    # 3. Comparisons
    if "compare" in q_lower or " vs " in q_lower or "versus" in q_lower:
        # Check for state comparison (e.g. Karnataka vs Tamil Nadu)
        if "karnataka" in q_lower and "tamil nadu" in q_lower:
            return "get_state_analysis", {"state": "Karnataka", "year": year, "category": detected_cat}

        # Institution comparison
        common_insts = ["iit madras", "iit delhi", "iit bombay", "iit kanpur", "iit kharagpur", "iisc", "jnu", "bhu"]
        found = [inst.title() for inst in common_insts if inst in q_lower]
        if len(found) >= 2:
            return "compare_institutions", {"institutions": found, "year": year, "category": detected_cat}
        elif len(found) == 1:
            return "get_institution_details", {"institution_name": found[0], "category": detected_cat}

    # 4. Specific Institution Query
    common_names = ["iit", "nit", "iisc", "bits", "vit", "jnu", "aiims", "manipal", "amrita", "delhi university", "bhu"]
    for cname in common_names:
        if cname in q_lower:
            # Extract full institutional query
            return "get_institution_details", {"institution_name": cname.upper(), "category": detected_cat, "year": year}

    # 5. Trend / Time-series
    if any(k in q_lower for k in ["trend", "over time", "over the years", "trajectory", "historical"]):
        metric = "Score"
        for m in ["score", "rank", "tlr", "rpc", "go", "oi", "perception"]:
            if m in q_lower:
                metric = m.capitalize() if m in ("score", "rank") else m.upper()
                break
        return "get_yearly_trends", {"category": detected_cat, "metric": metric}

    # 6. Rank Climbers / Mobility
    if any(k in q_lower for k in ["improved", "climber", "climb", "gain", "increase in rank"]):
        return "get_rank_changes", {"category": detected_cat, "direction": "climbers", "year_start": 2024, "year_end": 2025}
    if any(k in q_lower for k in ["decline", "declined", "drop", "fell", "worst drop"]):
        return "get_rank_changes", {"category": detected_cat, "direction": "decliners", "year_start": 2024, "year_end": 2025}

    # 7. Distribution & Statistics
    if any(k in q_lower for k in ["distribution", "histogram", "dispersion", "spread"]):
        return "get_distribution_analysis", {"metric": "Score", "year": year, "category": detected_cat}

    if any(k in q_lower for k in ["average score", "median score", "statistics", "five number", "summary stat"]):
        return "get_score_statistics", {"year": year, "category": detected_cat}

    # 8. State Analysis
    if any(k in q_lower for k in ["state", "states", "highest number of institutions", "geographic"]):
        return "get_state_analysis", {"state": detected_state, "year": year, "category": detected_cat}

    # 9. Top N Institutions (Default for rankings)
    sort_by = "Score"
    for p in ["tlr", "rpc", "go", "oi", "perception"]:
        if p in q_lower:
            sort_by = p.upper()
            break

    args: dict[str, Any] = {
        "n": n_val,
        "year": year,
        "category": detected_cat,
        "sort_by": sort_by,
    }
    if detected_state:
        args["state"] = detected_state

    return "get_top_institutions", args
