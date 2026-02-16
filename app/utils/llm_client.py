"""Utility functions for creating LLM clients based on provider settings."""

import logging
from typing import Any, Optional

from config.settings import AppSettings, get_settings

logger = logging.getLogger(__name__)


def create_llm_client(
    settings: Optional[AppSettings] = None,
    prefer_fast_model: bool = False,
) -> tuple[Any, str]:
    """Create an LLM client based on application settings.

    Args:
        settings: Application settings. If None, will load from get_settings()
        prefer_fast_model: If True, use faster/cheaper model when available

    Returns:
        Tuple of (client, model_name)

    Raises:
        ImportError: If openai package not installed
        ValueError: If provider is invalid or configuration is missing
    """
    if settings is None:
        settings = get_settings()

    try:
        from openai import AzureOpenAI, OpenAI
    except ImportError:
        raise ImportError(
            "openai package not installed. Run: pip install openai"
        )

    provider = settings.llm_provider.lower()

    if provider == "azure":
        return _create_azure_client(settings, prefer_fast_model)
    elif provider == "openrouter":
        return _create_openrouter_client(settings, prefer_fast_model)
    else:
        raise ValueError(
            f"Invalid LLM provider: {provider}. Must be 'azure' or 'openrouter'"
        )


def _create_azure_client(
    settings: AppSettings,
    prefer_fast_model: bool,
) -> tuple[Any, str]:
    """Create Azure OpenAI client.

    Args:
        settings: Application settings
        prefer_fast_model: Use GPT-3.5 instead of GPT-4

    Returns:
        Tuple of (client, deployment_name)
    """
    from openai import AzureOpenAI

    if not settings.azure_openai.endpoint or not settings.azure_openai.api_key:
        raise ValueError(
            "Azure OpenAI configuration missing. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY"
        )

    client = AzureOpenAI(
        azure_endpoint=settings.azure_openai.endpoint,
        api_key=settings.azure_openai.api_key,
        api_version=settings.azure_openai.api_version,
    )

    model = (
        settings.azure_openai.gpt35_deployment
        if prefer_fast_model
        else settings.azure_openai.gpt4_deployment
    )

    logger.info(f"Created Azure OpenAI client with model: {model}")
    return client, model


def _create_openrouter_client(
    settings: AppSettings,
    prefer_fast_model: bool,
) -> tuple[Any, str]:
    """Create OpenRouter client.

    Args:
        settings: Application settings
        prefer_fast_model: Use cheaper model if True

    Returns:
        Tuple of (client, model_name)
    """
    from openai import OpenAI

    if not settings.openrouter.api_key:
        raise ValueError(
            "OpenRouter configuration missing. Set OPENROUTER_API_KEY"
        )

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter.api_key,
    )

    # Use configured model or default to cheaper option if prefer_fast_model
    if prefer_fast_model:
        # Use Haiku for faster/cheaper responses
        model = "anthropic/claude-3-haiku"
    else:
        # Use configured model (default: claude-3-sonnet)
        model = settings.openrouter.model

    logger.info(f"Created OpenRouter client with model: {model}")
    return client, model


def get_llm_with_fallback(
    settings: Optional[AppSettings] = None,
    prefer_fast_model: bool = False,
) -> tuple[Any, str]:
    """Get LLM client with automatic fallback.

    Tries primary provider first, then falls back to alternative if it fails.

    Args:
        settings: Application settings
        prefer_fast_model: Use faster/cheaper model

    Returns:
        Tuple of (client, model_name)
    """
    if settings is None:
        settings = get_settings()

    try:
        # Try primary provider
        return create_llm_client(settings, prefer_fast_model)
    except Exception as e:
        logger.warning(f"Primary LLM provider failed: {e}, trying fallback")

        # Try fallback provider
        fallback_provider = "openrouter" if settings.llm_provider == "azure" else "azure"

        try:
            # Temporarily change provider
            original_provider = settings.llm_provider
            settings.llm_provider = fallback_provider
            client, model = create_llm_client(settings, prefer_fast_model)
            settings.llm_provider = original_provider
            logger.info(f"Using fallback provider: {fallback_provider}")
            return client, model
        except Exception as fallback_error:
            logger.error(f"Fallback provider also failed: {fallback_error}")
            raise RuntimeError(
                f"Both primary ({settings.llm_provider}) and fallback ({fallback_provider}) LLM providers failed"
            ) from fallback_error


def call_llm(
    client: Any,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 2000,
    **kwargs,
) -> str:
    """Call LLM with retry logic.

    Args:
        client: OpenAI-compatible client
        model: Model name
        messages: Chat messages
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        **kwargs: Additional parameters

    Returns:
        Response text

    Raises:
        Exception: If LLM call fails after retries
    """
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            return response.choices[0].message.content or ""

        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}, retrying...")
                import time
                time.sleep(retry_delay * (2 ** attempt))
            else:
                logger.error(f"LLM call failed after {max_retries} attempts: {e}")
                raise


def get_provider_info(settings: Optional[AppSettings] = None) -> dict[str, Any]:
    """Get information about current LLM provider configuration.

    Args:
        settings: Application settings

    Returns:
        Dictionary with provider information
    """
    if settings is None:
        settings = get_settings()

    info = {
        "provider": settings.llm_provider,
        "configured": False,
        "fallback_available": False,
    }

    if settings.llm_provider == "azure":
        info["configured"] = bool(
            settings.azure_openai.endpoint and settings.azure_openai.api_key
        )
        info["fallback_available"] = bool(settings.openrouter.api_key)
        info["model"] = settings.azure_openai.gpt4_deployment
        info["fast_model"] = settings.azure_openai.gpt35_deployment
    else:  # openrouter
        info["configured"] = bool(settings.openrouter.api_key)
        info["fallback_available"] = bool(
            settings.azure_openai.endpoint and settings.azure_openai.api_key
        )
        info["model"] = settings.openrouter.model
        info["fast_model"] = "anthropic/claude-3-haiku"

    return info
