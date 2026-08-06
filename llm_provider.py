import logging
from typing import Any

from config import settings

logger = logging.getLogger("underwrite.llm")


def get_llm() -> Any | None:
    """
    Instantiate the configured LLM provider.
    Returns None if the provider is not configured properly or API keys are missing.
    """
    provider = settings.llm_provider.lower()

    if provider == "openai":
        if not settings.openai_api_key:
            logger.warning("OpenAI API key missing. AI remediation disabled.")
            return None
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=settings.openai_api_key,
        )

    elif provider == "anthropic":
        if not settings.anthropic_api_key:
            logger.warning("Anthropic API key missing. AI remediation disabled.")
            return None
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model_name="claude-3-5-sonnet-20240620",
            temperature=0,
            api_key=settings.anthropic_api_key,
        )

    elif provider == "gemini":
        if not settings.google_api_key:
            logger.warning("Google API key missing. AI remediation disabled.")
            return None
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0,
            google_api_key=settings.google_api_key,
        )

    elif provider == "azure":
        if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
            logger.warning("Azure OpenAI configuration missing. AI remediation disabled.")
            return None
        from langchain_openai import AzureChatOpenAI
        return AzureChatOpenAI(
            azure_deployment="gpt-4o",
            api_version="2024-02-01",
            temperature=0,
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
        )

    else:
        logger.warning("Unknown LLM provider: %s. AI remediation disabled.", provider)
        return None
