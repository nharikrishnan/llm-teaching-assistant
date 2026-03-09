"""LLM provider configuration: env-based selection and chat model factory."""

from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"


def get_llm():
    """Return a LangChain chat model based on DEFAULT_PROVIDER and env API keys."""
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
        return ChatOpenAI(model=model, api_key=api_key, temperature=0.3)

    if provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key == "your-anthropic-key-here":
            raise ValueError(
                "Anthropic is selected but ANTHROPIC_API_KEY is not set or is placeholder. "
                "Set ANTHROPIC_API_KEY in .env"
            )
        from langchain_anthropic import ChatAnthropic

        model = os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL).strip()
        return ChatAnthropic(model=model, api_key=api_key, temperature=0.3)

    raise ValueError(
        f"Unknown DEFAULT_PROVIDER: {provider}. Use 'openai' or 'anthropic'."
    )
