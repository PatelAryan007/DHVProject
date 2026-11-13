"""
NIRF Insight — Main Chatbot Service Orchestrator
================================================
Coordinates intent parsing, Python dataset calculation, automatic visualization,
answer synthesis, and multi-turn session persistence.
"""

from typing import Any
import pandas as pd
import plotly.graph_objects as go

from chatbot.llm_service import is_openai_configured, get_configured_model
from chatbot.intent_parser import parse_intent_with_openai, parse_intent_heuristically
from chatbot.analytics_executor import execute_chatbot_tool
from chatbot.response_generator import build_grounded_answer
from chatbot.conversation_manager import ConversationManager


class ChatbotResponse:
    """Encapsulates the full response returned by the chatbot."""

    def __init__(
        self,
        answer_text: str,
        table: pd.DataFrame | None = None,
        fig: go.Figure | None = None,
        tool_name: str | None = None,
        tool_args: dict[str, Any] | None = None,
        used_llm: bool = False,
        error: str | None = None,
    ):
        self.answer_text = answer_text
        self.table = table
        self.fig = fig
        self.tool_name = tool_name
        self.tool_args = tool_args or {}
        self.used_llm = used_llm
        self.error = error


def process_user_message(
    user_query: str,
    df: pd.DataFrame,
    conv_manager: ConversationManager,
) -> ChatbotResponse:
    """Process a user query through the end-to-end dataset chatbot pipeline.

    Flow:
    1. Parse user intent (OpenAI Function Calling or Heuristic Parser)
    2. Execute validated analytics tool in Python/Pandas
    3. Generate Plotly chart if relevant
    4. Synthesize natural-language explanation
    5. Update conversation memory
    """
    clean_query = user_query.strip()
    if not clean_query:
        return ChatbotResponse(answer_text="Please ask a question about NIRF rankings or institutions.")

    tool_name = None
    tool_args: dict[str, Any] = {}
    direct_reply = None
    used_llm = False

    # 1. Intent Parsing
    if is_openai_configured():
        llm_messages = conv_manager.get_messages_for_llm()
        llm_messages.append({"role": "user", "content": clean_query})

        tool_name, tool_args, direct_reply = parse_intent_with_openai(llm_messages)
        if tool_name:
            used_llm = True

    # Fallback to heuristic parser if no tool detected or OpenAI not configured
    if not tool_name and not direct_reply:
        tool_name, tool_args = parse_intent_heuristically(clean_query, context=conv_manager.last_context)

    # If LLM returned a direct conversational message (e.g. greeting)
    if direct_reply and not tool_name:
        conv_manager.add_message("user", clean_query)
        conv_manager.add_message("assistant", direct_reply)
        return ChatbotResponse(answer_text=direct_reply, used_llm=True)

    # 2. Execute Analytics Tool in Python / Pandas
    table, facts, fig = execute_chatbot_tool(df, tool_name=tool_name, tool_args=tool_args)

    # 3. Generate Grounded Explanation
    answer_text = build_grounded_answer(
        user_query=clean_query,
        tool_name=tool_name,
        tool_args=tool_args,
        table=table,
        facts=facts,
    )

    # 4. Save to Conversation History
    conv_manager.add_message(
        role="user",
        content=clean_query,
    )
    conv_manager.add_message(
        role="assistant",
        content=answer_text,
        tool_name=tool_name,
        tool_args=tool_args,
        table=table,
        fig=fig,
    )

    return ChatbotResponse(
        answer_text=answer_text,
        table=table,
        fig=fig,
        tool_name=tool_name,
        tool_args=tool_args,
        used_llm=used_llm,
    )
