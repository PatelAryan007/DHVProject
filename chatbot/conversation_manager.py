"""
NIRF Insight — Conversation Context Manager
===========================================
Preserves session state, conversation history, and contextual parameters
across multi-turn dialogues to resolve follow-up queries.
"""

from typing import Any


class ConversationManager:
    """Manages chat history and contextual filter memory across conversation turns."""

    def __init__(self, history: list[dict[str, Any]] | None = None):
        # IMPORTANT: Never do `history or []` because an empty list evaluates to False in Python,
        # which creates a detached new list and breaks Streamlit session state!
        if history is not None:
            self.history = history
        else:
            self.history = []
        self.last_context: dict[str, Any] = self._extract_recent_context()

    def add_message(
        self,
        role: str,
        content: str,
        tool_name: str | None = None,
        tool_args: dict[str, Any] | None = None,
        table: Any | None = None,
        fig: Any | None = None,
        error: str | None = None,
    ):
        """Append a message turn directly to the underlying persistent history list."""
        msg = {
            "role": role,
            "content": content,
            "tool_name": tool_name,
            "tool_args": tool_args or {},
            "table": table,
            "fig": fig,
            "error": error,
        }
        self.history.append(msg)
        if tool_args:
            self.update_context(tool_args)

    def update_context(self, args: dict[str, Any]):
        """Update recent context memory from executed parameters."""
        for key in ["category", "year", "state", "institutions", "metric"]:
            if key in args and args[key] is not None:
                self.last_context[key] = args[key]

    def _extract_recent_context(self) -> dict[str, Any]:
        """Scan backwards through history to find the most recent filter context."""
        ctx: dict[str, Any] = {}
        for msg in reversed(self.history):
            args = msg.get("tool_args", {})
            for key in ["category", "year", "state", "institutions", "metric"]:
                if key not in ctx and key in args and args[key] is not None:
                    ctx[key] = args[key]
        return ctx

    def get_messages_for_llm(self) -> list[dict[str, Any]]:
        """Format history for OpenAI chat completions."""
        llm_msgs = []
        for msg in self.history:
            llm_msgs.append({
                "role": msg["role"],
                "content": str(msg.get("content", "")),
            })
        return llm_msgs

    def clear(self):
        """Reset conversation history and context."""
        self.history.clear()
        self.last_context.clear()
