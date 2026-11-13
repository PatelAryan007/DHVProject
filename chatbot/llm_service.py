"""
NIRF Insight — LLM Service (OpenAI Integration)
================================================
Handles OpenAI client initialization, authentication verification,
model configuration, and safe execution with robust error recovery.
API keys are strictly read from environment variables and never logged or exposed.
"""

import os
from typing import Any
from dotenv import load_dotenv

# Load .env file if available
load_dotenv()

DEFAULT_MODEL = "gpt-4o-mini"


def get_api_key() -> str | None:
    """Retrieve the OpenAI API key from the environment."""
    key = os.getenv("OPENAI_API_KEY", "").strip()
    return key if key else None


def is_openai_configured() -> bool:
    """Check if a valid OpenAI API key is present in the environment."""
    key = get_api_key()
    return bool(key and not key.startswith("your_") and len(key) > 10)


def get_configured_model() -> str:
    """Retrieve the configured OpenAI model name."""
    return os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def get_openai_client():
    """Instantiate and return the official OpenAI client."""
    if not is_openai_configured():
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=get_api_key())
    except Exception:
        return None


def call_openai_chat(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | dict[str, Any] = "auto",
    temperature: float = 0.2,
    max_tokens: int = 1000,
) -> tuple[Any | None, str | None]:
    """Execute a chat completion request to the OpenAI API.

    Returns:
        (response_choice_message, error_message)
    """
    client = get_openai_client()
    if not client:
        return None, "OpenAI API key is missing or not configured. Set OPENAI_API_KEY in your .env file."

    model = get_configured_model()

    try:
        params: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            params["tools"] = tools
            params["tool_choice"] = tool_choice

        completion = client.chat.completions.create(**params)
        choice = completion.choices[0]
        return choice.message, None

    except Exception as e:
        err_type = type(e).__name__
        err_msg = str(e)

        if "AuthenticationError" in err_type or "invalid_api_key" in err_msg.lower():
            return None, "Invalid OpenAI API Key. Please verify your OPENAI_API_KEY in .env."
        elif "RateLimitError" in err_type:
            return None, "OpenAI API rate limit exceeded or quota exhausted. Please check your OpenAI account billing."
        elif "APIConnectionError" in err_type:
            return None, "Could not connect to the OpenAI API. Please check your network connection."
        else:
            return None, f"OpenAI API Error ({err_type}): {err_msg}"
