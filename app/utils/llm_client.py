"""Utility functions for creating LLM clients based on provider settings."""

import logging
from typing import Any, Optional

from config.settings import AppSettings, get_settings

logger = logging.getLogger(__name__)

# Try to import Langfuse
try:
    from langfuse.openai import openai as langfuse_openai
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    logger.warning("Langfuse not available. Install with: pip install langfuse")

# Global Langfuse instance
_langfuse_instance: Optional[Any] = None


def get_langfuse(settings: Optional[AppSettings] = None) -> Optional[Any]:
    """Get or create Langfuse instance.

    Args:
        settings: Application settings

    Returns:
        Langfuse instance or None if disabled/unavailable
    """
    global _langfuse_instance

    if settings is None:
        settings = get_settings()

    if not settings.langfuse.enabled:
        return None

    if not LANGFUSE_AVAILABLE:
        logger.warning("Langfuse is enabled but not installed")
        return None

    if not settings.langfuse.public_key or not settings.langfuse.secret_key:
        logger.warning("Langfuse credentials not configured")
        return None

    if _langfuse_instance is None:
        try:
            _langfuse_instance = Langfuse(
                public_key=settings.langfuse.public_key,
                secret_key=settings.langfuse.secret_key,
                host=settings.langfuse.host,
            )
            logger.info(f"Langfuse initialized with host: {settings.langfuse.host}")
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse: {e}")
            return None

    return _langfuse_instance


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

    # Create base client
    if provider == "azure":
        client, model = _create_azure_client(settings, prefer_fast_model)
    elif provider == "openrouter":
        client, model = _create_openrouter_client(settings, prefer_fast_model)
    else:
        raise ValueError(
            f"Invalid LLM provider: {provider}. Must be 'azure' or 'openrouter'"
        )

    # Wrap with Langfuse if enabled
    langfuse = get_langfuse(settings)
    if langfuse and LANGFUSE_AVAILABLE:
        try:
            # Patch the client with Langfuse observability
            client = langfuse_openai.wrap_openai_client(client)
            logger.info("LLM client wrapped with Langfuse observability")
        except Exception as e:
            logger.warning(f"Failed to wrap client with Langfuse: {e}")

    return client, model


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
    trace_name: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    tags: Optional[list[str]] = None,
    **kwargs,
) -> str:
    """Call LLM with retry logic and optional Langfuse tracing.

    Args:
        client: OpenAI-compatible client
        model: Model name
        messages: Chat messages
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        trace_name: Optional name for Langfuse trace
        user_id: Optional user ID for Langfuse
        session_id: Optional session ID for Langfuse
        tags: Optional tags for Langfuse
        **kwargs: Additional parameters

    Returns:
        Response text

    Raises:
        Exception: If LLM call fails after retries
    """
    max_retries = 3
    retry_delay = 2

    # Add Langfuse metadata if available
    if LANGFUSE_AVAILABLE and get_langfuse():
        if trace_name:
            kwargs.setdefault("name", trace_name)
        if user_id:
            kwargs.setdefault("user_id", user_id)
        if session_id:
            kwargs.setdefault("session_id", session_id)
        if tags:
            kwargs.setdefault("tags", tags)

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


def get_model_for_agent(
    agent_type: str,
    settings: Optional[AppSettings] = None,
    prefer_fast: bool = False,
) -> str:
    """Get the configured model for a specific agent type.

    Args:
        agent_type: Type of agent (e.g., "planning_agent", "sql_generator", "python_analyst",
                    "visualization", "uncertainty_scorer", "hitl_controller", "embeddings")
        settings: Application settings
        prefer_fast: If True and no agent-specific model set, use fast model

    Returns:
        Model name/deployment to use for this agent

    Examples:
        # Get model for planning agent
        model = get_model_for_agent("planning_agent", settings)

        # Get fast model for uncertainty scorer
        model = get_model_for_agent("uncertainty_scorer", settings, prefer_fast=True)
    """
    if settings is None:
        settings = get_settings()

    # Get agent-specific model if configured
    agent_model = getattr(settings.models, agent_type, "")
    if agent_model:
        logger.info(f"Using configured model for {agent_type}: {agent_model}")
        return agent_model

    # Fall back to default or fast model
    if prefer_fast and settings.models.fast:
        logger.info(f"Using fast model for {agent_type}: {settings.models.fast}")
        return settings.models.fast

    if settings.models.default:
        logger.info(f"Using default model for {agent_type}: {settings.models.default}")
        return settings.models.default

    # Fall back to provider defaults
    provider = settings.llm_provider.lower()
    if provider == "azure":
        model = (
            settings.azure_openai.gpt35_deployment
            if prefer_fast
            else settings.azure_openai.gpt4_deployment
        )
    else:  # openrouter
        model = "anthropic/claude-3-haiku" if prefer_fast else settings.openrouter.model

    logger.info(f"Using provider default model for {agent_type}: {model}")
    return model


def create_llm_client_for_agent(
    agent_type: str,
    settings: Optional[AppSettings] = None,
    prefer_fast: bool = False,
) -> tuple[Any, str]:
    """Create an LLM client with the appropriate model for a specific agent.

    This is a convenience wrapper around create_llm_client that automatically
    selects the right model based on agent type and configuration.

    Args:
        agent_type: Type of agent (e.g., "planning_agent", "sql_generator")
        settings: Application settings
        prefer_fast: If True, prefer fast model when no agent-specific model set

    Returns:
        Tuple of (client, model_name)

    Examples:
        # Create client for SQL generator with its configured model
        client, model = create_llm_client_for_agent("sql_generator", settings)

        # Create client for uncertainty scorer with fast model preference
        client, model = create_llm_client_for_agent("uncertainty_scorer", settings, prefer_fast=True)
    """
    if settings is None:
        settings = get_settings()

    # Get the model for this agent
    model = get_model_for_agent(agent_type, settings, prefer_fast)

    # Create client (this will use provider default, we'll override the model)
    client, _ = create_llm_client(settings, prefer_fast)

    return client, model


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
