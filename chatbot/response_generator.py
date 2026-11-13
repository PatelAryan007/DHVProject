"""
NIRF Insight — Chatbot Response Generator
==========================================
Formats analytics results into clear, grounded, and polite user-facing answers.
Uses OpenAI to synthesize natural-language explanations when available,
and provides a clean, structured templated response when running offline.
"""

from typing import Any
import pandas as pd
from chatbot.llm_service import is_openai_configured, call_openai_chat


def generate_llm_response(
    user_query: str,
    tool_name: str,
    tool_args: dict[str, Any],
    facts: list[str],
    data_preview: str,
) -> str | None:
    """Use OpenAI to synthesize a polite, insightful explanation grounded strictly in the calculated facts."""
    if not is_openai_configured():
        return None

    system_prompt = (
        "You are the NIRF Insight AI Assistant, an analytics expert on Indian higher education.\n"
        "Your task is to provide a concise, professional answer to the user's question.\n"
        "RULES:\n"
        "1. ONLY state facts and numbers provided in the 'CALCULATED DATA & FACTS' section below.\n"
        "2. NEVER invent or extrapolate ranks, scores, or institution names.\n"
        "3. Remember that in NIRF, lower numerical rank is better (#1 is highest).\n"
        "4. Format your answer with clear markdown bullet points and bold highlights.\n"
        "5. Keep the tone insightful, academic, and professional."
    )

    user_content = (
        f"User Question: {user_query}\n\n"
        f"Executed Tool: {tool_name}\n"
        f"Parameters: {tool_args}\n\n"
        f"CALCULATED DATA & FACTS:\n"
        + "\n".join(f"- {f}" for f in facts)
        + f"\n\nDATA PREVIEW:\n{data_preview}\n\n"
        "Provide a clear, direct analytical response based on these exact facts."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    msg, err = call_openai_chat(messages, temperature=0.3, max_tokens=600)
    if err or not msg:
        return None

    return getattr(msg, "content", None)


def build_grounded_answer(
    user_query: str,
    tool_name: str,
    tool_args: dict[str, Any],
    table: pd.DataFrame,
    facts: list[str],
) -> str:
    """Generate the final assistant message content."""
    # Try LLM generation first if configured
    data_preview = ""
    if isinstance(table, pd.DataFrame) and not table.empty:
        data_preview = table.head(10).to_string(index=False)

    llm_answer = generate_llm_response(
        user_query=user_query,
        tool_name=tool_name,
        tool_args=tool_args,
        facts=facts,
        data_preview=data_preview,
    )

    if llm_answer and llm_answer.strip():
        return llm_answer

    # Structured Fallback Response
    lines = [f"### 📊 Analytical Findings"]
    for fact in facts:
        lines.append(f"- {fact}")

    if tool_args:
        clean_args = ", ".join(f"**{k}**: `{v}`" for k, v in tool_args.items() if v is not None)
        if clean_args:
            lines.append(f"\n*Applied Filters: {clean_args}*")

    return "\n".join(lines)
