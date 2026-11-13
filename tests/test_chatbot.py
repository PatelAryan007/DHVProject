"""
NIRF Insight — Chatbot Automated Test Suite
===========================================
Tests OpenAI configuration handling, intent parsing, analytics tool execution,
conversational context memory, and numerical grounding against the live dataset.
"""

import pytest
import pandas as pd
import plotly.graph_objects as go

from core.data_loader import load_data
from chatbot.llm_service import is_openai_configured, get_configured_model
from chatbot.tool_registry import ANALYTICS_TOOLS
from chatbot.analytics_executor import execute_chatbot_tool
from chatbot.intent_parser import parse_intent_heuristically
from chatbot.conversation_manager import ConversationManager
from chatbot.chatbot_service import process_user_message, ChatbotResponse


@pytest.fixture(scope="module")
def nirf_df():
    """Load dataset for test execution."""
    df = load_data()
    assert df is not None and not df.empty, "Dataset must load successfully."
    return df


# ---------------------------------------------------------------------------
# 1. Configuration & Security Tests
# ---------------------------------------------------------------------------

def test_api_key_configuration_check(monkeypatch):
    """Verify that is_openai_configured handles missing or placeholder keys safely."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert not is_openai_configured()

    monkeypatch.setenv("OPENAI_API_KEY", "your_openai_api_key_here")
    assert not is_openai_configured()

    monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-test1234567890abcdef")
    assert is_openai_configured()


def test_model_name_configuration(monkeypatch):
    """Verify configurable model name with gpt-4o-mini default."""
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    assert get_configured_model() == "gpt-4o-mini"

    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    assert get_configured_model() == "gpt-4o"


def test_tool_registry_schemas():
    """Verify all 15 analytics tools have valid OpenAI tool schemas."""
    assert len(ANALYTICS_TOOLS) == 15
    for t in ANALYTICS_TOOLS:
        assert t["type"] == "function"
        assert "name" in t["function"]
        assert "description" in t["function"]
        assert "parameters" in t["function"]


# ---------------------------------------------------------------------------
# 2. Analytics Tool Execution Verification (Live Dataset)
# ---------------------------------------------------------------------------

def test_tool_get_dataset_summary(nirf_df):
    """Verify dataset summary returns KPIs, facts, and figure."""
    table, facts, fig = execute_chatbot_tool(nirf_df, "get_dataset_summary", {})
    assert not table.empty
    assert len(facts) >= 3
    assert fig is not None


def test_tool_get_top_institutions(nirf_df):
    """Verify top institutions tool respects n, category, and year parameters."""
    args = {"n": 5, "year": 2024, "category": "Engineering"}
    table, facts, fig = execute_chatbot_tool(nirf_df, "get_top_institutions", args)
    assert not table.empty
    assert len(table) == 5
    assert (table["Category"] == "Engineering").all()
    assert fig is not None
    # Verify rank 1 is IIT Madras in Engineering 2024
    assert "Indian Institute of Technology Madras" in table.iloc[0]["Name"]


def test_tool_compare_institutions(nirf_df):
    """Verify multi-institution comparison."""
    args = {"institutions": ["IIT Madras", "IIT Bombay"], "year": 2024, "category": "Overall"}
    table, facts, fig = execute_chatbot_tool(nirf_df, "compare_institutions", args)
    assert not table.empty
    assert len(table) >= 2
    assert fig is not None


def test_tool_get_yearly_trends(nirf_df):
    """Verify yearly trends tool computes longitudinal aggregates."""
    args = {"category": "Overall", "metric": "Score"}
    table, facts, fig = execute_chatbot_tool(nirf_df, "get_yearly_trends", args)
    assert not table.empty
    assert "Mean_Score" in table.columns
    assert fig is not None


def test_tool_get_state_analysis(nirf_df):
    """Verify state analysis tool returns state rankings."""
    args = {"year": 2024, "category": "Overall", "top_n_states": 5}
    table, facts, fig = execute_chatbot_tool(nirf_df, "get_state_analysis", args)
    assert not table.empty
    assert "Institutions" in table.columns
    assert fig is not None


def test_tool_get_correlation_analysis(nirf_df):
    """Verify correlation calculation tool produces numerical r and scatter plot."""
    args = {"col1": "RPC", "col2": "Score", "year": 2024, "category": "Overall"}
    table, facts, fig = execute_chatbot_tool(nirf_df, "get_correlation_analysis", args)
    assert not table.empty
    assert any("pearson" in f.lower() for f in facts)
    assert fig is not None


def test_tool_get_score_statistics(nirf_df):
    """Verify score summary statistics tool computes exact 5-number summary."""
    args = {"year": 2024, "category": "Overall"}
    table, facts, fig = execute_chatbot_tool(nirf_df, "get_score_statistics", args)
    assert not table.empty
    assert fig is not None


# ---------------------------------------------------------------------------
# 3. Intent Parser Tests
# ---------------------------------------------------------------------------

def test_heuristic_parser_top_institutions():
    """Verify parser extracts top N, category, and year from query."""
    tool, args = parse_intent_heuristically("Show me the top 5 Engineering colleges in 2024")
    assert tool == "get_top_institutions"
    assert args["n"] == 5
    assert args["category"] == "Engineering"
    assert args["year"] == 2024


def test_heuristic_parser_correlation():
    """Verify parser detects correlation queries."""
    tool, args = parse_intent_heuristically("What is the correlation between RPC and Score?")
    assert tool == "get_correlation_analysis"
    assert args["col1"] == "RPC"


def test_heuristic_parser_institution_comparison():
    """Verify parser detects comparison queries."""
    tool, args = parse_intent_heuristically("Compare IIT Madras and IIT Bombay in 2024")
    assert tool == "compare_institutions"
    assert len(args["institutions"]) == 2


# ---------------------------------------------------------------------------
# 4. Conversation Memory & End-to-End Pipeline
# ---------------------------------------------------------------------------

def test_conversation_context_memory():
    """Verify that conversation manager captures and updates filters across turns."""
    cm = ConversationManager()
    cm.add_message("user", "Top 10 Engineering colleges in 2024", tool_name="get_top_institutions", tool_args={"category": "Engineering", "year": 2024})
    assert cm.last_context.get("category") == "Engineering"
    assert cm.last_context.get("year") == 2024

    # Follow-up turn
    tool, args = parse_intent_heuristically("Only in Karnataka", context=cm.last_context)
    assert args.get("state") == "Karnataka"
    assert args.get("category") == "Engineering"
    assert args.get("year") == 2024


def test_end_to_end_process_user_message(nirf_df):
    """Verify end-to-end user query execution producing valid answer, table, and figure."""
    cm = ConversationManager()
    resp = process_user_message("What is the average NIRF score trend?", nirf_df, cm)

    assert isinstance(resp, ChatbotResponse)
    assert resp.answer_text is not None and len(resp.answer_text) > 0
    assert resp.table is not None and not resp.table.empty
    assert resp.fig is not None
    assert len(cm.history) == 2  # 1 user + 1 assistant
