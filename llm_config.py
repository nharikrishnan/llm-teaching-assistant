"""LLM provider configuration: env-based selection and chat model factory."""

from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# Default model names per provider
DEFAULT_OPENAI_MODEL = "gpt-5.2"
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"


def get_llm():
    """
    Return a LangChain chat model based on DEFAULT_PROVIDER and env API keys.

    Reads DEFAULT_PROVIDER (openai | anthropic), then the corresponding API key.
    Returns a LangChain BaseChatModel (ChatOpenAI or ChatAnthropic).

    Raises:
        ValueError: If no provider is configured or API key is missing.
    """
    provider = (os.getenv("DEFAULT_PROVIDER") or "openai").strip().lower()

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key.startswith("sk-your-"):
            raise ValueError(
                "OpenAI is selected but OPENAI_API_KEY is not set or is placeholder. "
                "Set OPENAI_API_KEY in .env"
            )
        from langchain_openai import ChatOpenAI

        model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip()
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=0.3,
        )

    if provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key == "your-anthropic-key-here":
            raise ValueError(
                "Anthropic is selected but ANTHROPIC_API_KEY is not set or is placeholder. "
                "Set ANTHROPIC_API_KEY in .env"
            )
        from langchain_anthropic import ChatAnthropic

        model = os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL).strip()
        return ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=0.3,
        )

    raise ValueError(
        f"Unknown DEFAULT_PROVIDER: {provider}. Use 'openai' or 'anthropic'."
    )


def get_available_provider() -> str | None:
    """
    Return the provider name that has a valid API key, or None.

    Checks OPENAI_API_KEY and ANTHROPIC_API_KEY; DEFAULT_PROVIDER is ignored.
    """
    openai_key = os.getenv("OPENAI_API_KEY", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if openai_key and not openai_key.startswith("sk-your-"):
        return "openai"
    if anthropic_key and anthropic_key != "your-anthropic-key-here":
        return "anthropic"
    return None
