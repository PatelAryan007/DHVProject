"""
NIRF Insight — Chatbot Package
==============================
Modular AI Chatbot engine integrating OpenAI API with dataset-grounded analytics.
"""

from chatbot.chatbot_service import process_user_message, ChatbotResponse
from chatbot.llm_service import is_openai_configured, get_configured_model

__all__ = [
    "process_user_message",
    "ChatbotResponse",
    "is_openai_configured",
    "get_configured_model",
]
