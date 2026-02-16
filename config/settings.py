"""Application settings and configuration management."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AzureOpenAISettings(BaseSettings):
    """Azure OpenAI API configuration."""

    model_config = SettingsConfigDict(env_prefix="AZURE_OPENAI_")

    endpoint: str = Field(default="", description="Azure OpenAI endpoint URL")
    api_key: str = Field(default="", description="Azure OpenAI API key")
    api_version: str = Field(default="2024-02-15-preview", description="API version")
    gpt4_deployment: str = Field(
        default="gpt-4-turbo", alias="AZURE_GPT4_DEPLOYMENT", description="GPT-4 deployment name"
    )
    gpt35_deployment: str = Field(
        default="gpt-35-turbo",
        alias="AZURE_GPT35_DEPLOYMENT",
        description="GPT-3.5 deployment name",
    )


class OpenRouterSettings(BaseSettings):
    """OpenRouter fallback API configuration."""

    model_config = SettingsConfigDict(env_prefix="OPENROUTER_")

    api_key: str = Field(default="", description="OpenRouter API key")
    model: str = Field(
        default="anthropic/claude-3-sonnet", description="Default model to use"
    )


class PostgresSettings(BaseSettings):
    """PostgreSQL database configuration."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    db: str = Field(default="analytics_db", description="Database name")
    user: str = Field(default="analyst", description="Database user")
    password: str = Field(default="", description="Database password")

    @property
    def connection_string(self) -> str:
        """Generate SQLAlchemy connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    @property
    def async_connection_string(self) -> str:
        """Generate async SQLAlchemy connection string."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class AppSettings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Agentic Data Analyst", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")

    # LLM Provider Selection
    llm_provider: str = Field(
        default="azure",
        description="LLM provider to use: 'azure' or 'openrouter'"
    )

    # Uncertainty threshold
    uncertainty_threshold: float = Field(
        default=0.95, description="Threshold for triggering HITL clarification"
    )

    # Sandbox settings
    sandbox_enabled: bool = Field(
        default=True,
        description="Enable Docker sandbox for code execution. If False, runs code locally (LESS SECURE)"
    )
    max_sandbox_timeout: int = Field(
        default=30, description="Maximum timeout for sandbox execution in seconds"
    )
    sandbox_memory_limit: str = Field(
        default="512m", description="Memory limit for sandbox container"
    )

    # Upload settings
    max_upload_size_mb: int = Field(
        default=100, description="Maximum file upload size in MB"
    )

    # Cache settings
    cache_enabled: bool = Field(default=True, description="Enable caching")

    # ChromaDB
    chroma_persist_dir: Path = Field(
        default=Path("./chroma_db"), description="ChromaDB persistence directory"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[Path] = Field(
        default=Path("./logs/app.log"), description="Log file path"
    )

    # Sub-configurations
    azure_openai: AzureOpenAISettings = Field(default_factory=AzureOpenAISettings)
    openrouter: OpenRouterSettings = Field(default_factory=OpenRouterSettings)
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)

    # Scoring weights
    data_completeness_weight: float = Field(
        default=0.35, description="Weight for data completeness score"
    )
    schema_confidence_weight: float = Field(
        default=0.35, description="Weight for schema confidence score"
    )
    query_confidence_weight: float = Field(
        default=0.30, description="Weight for query confidence score"
    )


@lru_cache
def get_settings() -> AppSettings:
    """Get cached application settings."""
    return AppSettings()


# Convenience instance
settings = get_settings()
