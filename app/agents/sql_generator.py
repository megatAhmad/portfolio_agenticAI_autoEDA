"""SQL Generator Agent for translating natural language to SQL queries."""

import logging
import re
import time
from typing import Any, Optional

import pandas as pd
from pydantic import BaseModel

from app.execution.db_manager import DatabaseManager
from app.knowledge.semantic_layer import SemanticLayer

logger = logging.getLogger(__name__)

try:
    from openai import AzureOpenAI, OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available")

try:
    from app.utils.llm_client import create_llm_client_for_agent
    from config.settings import get_settings, AppSettings
    LLM_CLIENT_AVAILABLE = True
except ImportError:
    LLM_CLIENT_AVAILABLE = False


class SQLGenerationResult(BaseModel):
    """Result of SQL generation."""

    success: bool
    query: Optional[str] = None
    explanation: str = ""
    confidence: float = 0.0
    error: Optional[str] = None


class SQLExecutionResult(BaseModel):
    """Result of SQL execution."""

    success: bool
    data: Optional[list[dict[str, Any]]] = None
    row_count: int = 0
    execution_time_ms: int = 0
    query: str = ""
    error: Optional[str] = None


class SQLGeneratorAgent:
    """Agent for generating and executing SQL queries."""

    SYSTEM_PROMPT = """You are an expert SQL query generator for PostgreSQL databases.
Your task is to translate natural language questions into accurate SQL queries.

Guidelines:
1. Use only the tables and columns that exist in the provided schema
2. Apply appropriate aggregations (SUM, COUNT, AVG) based on the metric definitions
3. Include relevant WHERE clauses for filters and business rules
4. Use proper JOINs when multiple tables are involved
5. Format dates appropriately for PostgreSQL
6. Always use parameterized query placeholders (:param_name) for user inputs
7. Return ONLY the SQL query, no explanations

When uncertain about column mappings, indicate your confidence level.
"""

    def __init__(
        self,
        db_manager: DatabaseManager,
        semantic_layer: SemanticLayer,
        llm_client: Optional[Any] = None,
        model: Optional[str] = None,
        settings: Optional[AppSettings] = None,
        # Legacy parameters for backward compatibility
        azure_endpoint: Optional[str] = None,
        azure_api_key: Optional[str] = None,
        azure_deployment: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
    ):
        """Initialize SQL Generator Agent.

        Args:
            db_manager: Database manager instance
            semantic_layer: Semantic layer instance
            llm_client: Pre-configured LLM client (OpenAI-compatible)
            model: Model name to use (overrides configured model)
            settings: Application settings (for model configuration)
            azure_endpoint: (Legacy) Azure OpenAI endpoint
            azure_api_key: (Legacy) Azure OpenAI API key
            azure_deployment: (Legacy) Azure deployment name
            openrouter_api_key: (Legacy) OpenRouter API key for fallback
        """
        self.db_manager = db_manager
        self.semantic_layer = semantic_layer

        self._llm_client: Optional[Any] = None
        self._model: str = ""

        # Use provided client if available
        if llm_client is not None and model is not None:
            self._llm_client = llm_client
            self._model = model
            logger.info(f"SQL Generator initialized with provided client and model: {model}")
        # Use configured model for SQL generator
        elif LLM_CLIENT_AVAILABLE:
            if settings is None:
                settings = get_settings()
            self._llm_client, self._model = create_llm_client_for_agent(
                "sql_generator", settings, prefer_fast=False
            )
            logger.info(f"SQL Generator initialized with model: {self._model}")
        # Try Azure OpenAI first (legacy)
        elif azure_endpoint and azure_api_key and OPENAI_AVAILABLE:
            self._llm_client = AzureOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=azure_api_key,
                api_version="2024-02-15-preview",
            )
            self._model = azure_deployment or "gpt-4-turbo"
            logger.info("Using Azure OpenAI for SQL generation (legacy)")
        # Fallback to OpenRouter (legacy)
        elif openrouter_api_key and OPENAI_AVAILABLE:
            self._llm_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_api_key,
            )
            self._model = "anthropic/claude-3-sonnet"
            logger.info("Using OpenRouter for SQL generation (legacy)")

    def _build_schema_context(self, table_names: Optional[list[str]] = None) -> str:
        """Build schema context for LLM prompt.

        Args:
            table_names: Specific tables to include (all if None)

        Returns:
            Formatted schema string
        """
        tables = table_names or self.db_manager.list_tables()
        schema_parts = ["Database Schema:"]

        for table in tables:
            try:
                schema = self.db_manager.get_table_schema(table)
                schema_parts.append(f"\nTable: {table}")
                for col_name, col_info in schema["columns"].items():
                    schema_parts.append(f"  - {col_name}: {col_info['type']}")
            except Exception as e:
                logger.warning(f"Could not get schema for {table}: {e}")

        return "\n".join(schema_parts)

    def _build_semantic_context(self) -> str:
        """Build semantic layer context for LLM prompt.

        Returns:
            Formatted semantic context
        """
        return self.semantic_layer.to_prompt_context()

    def generate_sql(
        self,
        query: str,
        table_names: Optional[list[str]] = None,
        additional_context: Optional[str] = None,
    ) -> SQLGenerationResult:
        """Generate SQL from natural language query.

        Args:
            query: Natural language query
            table_names: Specific tables to use
            additional_context: Additional context for the query

        Returns:
            SQLGenerationResult with generated query
        """
        if not self._llm_client:
            return SQLGenerationResult(
                success=False,
                error="LLM client not configured",
            )

        # Build context
        schema_context = self._build_schema_context(table_names)
        semantic_context = self._build_semantic_context()

        user_prompt = f"""
{schema_context}

{semantic_context}

{f"Additional Context: {additional_context}" if additional_context else ""}

User Question: {query}

Generate a PostgreSQL query to answer this question. Return ONLY the SQL query.
Also provide a confidence score (0.0-1.0) for your query interpretation.

Format your response as:
CONFIDENCE: <score>
SQL:
<query>
"""

        try:
            response = self._llm_client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=1000,
            )

            content = response.choices[0].message.content or ""

            # Parse response
            confidence = 0.85  # Default
            sql_query = ""

            # Extract confidence
            confidence_match = re.search(r"CONFIDENCE:\s*([\d.]+)", content)
            if confidence_match:
                confidence = float(confidence_match.group(1))

            # Extract SQL
            sql_match = re.search(r"SQL:\s*\n?(.*)", content, re.DOTALL)
            if sql_match:
                sql_query = sql_match.group(1).strip()
                # Clean up markdown code blocks if present
                sql_query = re.sub(r"```sql\s*", "", sql_query)
                sql_query = re.sub(r"```\s*$", "", sql_query)
                sql_query = sql_query.strip()

            if not sql_query:
                # Try to extract any SQL-like content
                sql_query = content.strip()
                if sql_query.startswith("```"):
                    sql_query = re.sub(r"```\w*\s*", "", sql_query)
                    sql_query = sql_query.replace("```", "").strip()

            return SQLGenerationResult(
                success=True,
                query=sql_query,
                confidence=confidence,
                explanation=f"Generated with {confidence:.0%} confidence",
            )

        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return SQLGenerationResult(
                success=False,
                error=str(e),
            )

    def validate_sql(self, query: str) -> tuple[bool, Optional[str]]:
        """Validate SQL query for security and syntax.

        Args:
            query: SQL query to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        query_upper = query.upper()

        # Check for dangerous operations
        dangerous_patterns = [
            r"\bDROP\b",
            r"\bDELETE\b",
            r"\bTRUNCATE\b",
            r"\bALTER\b",
            r"\bCREATE\b",
            r"\bINSERT\b",
            r"\bUPDATE\b",
            r"\bGRANT\b",
            r"\bREVOKE\b",
            r"--",  # SQL comments (potential injection)
            r";.*\w",  # Multiple statements
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, query_upper):
                return False, f"Dangerous SQL pattern detected: {pattern}"

        # Basic syntax check - should start with SELECT
        if not query_upper.strip().startswith("SELECT"):
            return False, "Query must be a SELECT statement"

        return True, None

    def execute_sql(
        self,
        query: str,
        params: Optional[dict[str, Any]] = None,
    ) -> SQLExecutionResult:
        """Execute a SQL query safely.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            SQLExecutionResult with data or error
        """
        # Validate first
        is_valid, error = self.validate_sql(query)
        if not is_valid:
            return SQLExecutionResult(
                success=False,
                query=query,
                error=error,
            )

        start_time = time.time()

        try:
            df = self.db_manager.execute_sql(query, params)
            execution_time_ms = int((time.time() - start_time) * 1000)

            return SQLExecutionResult(
                success=True,
                data=df.to_dict(orient="records"),
                row_count=len(df),
                execution_time_ms=execution_time_ms,
                query=query,
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"SQL execution failed: {e}")

            return SQLExecutionResult(
                success=False,
                query=query,
                execution_time_ms=execution_time_ms,
                error=str(e),
            )

    def generate_and_execute(
        self,
        query: str,
        table_names: Optional[list[str]] = None,
        additional_context: Optional[str] = None,
    ) -> tuple[SQLGenerationResult, Optional[SQLExecutionResult]]:
        """Generate SQL from query and execute it.

        Args:
            query: Natural language query
            table_names: Specific tables to use
            additional_context: Additional context

        Returns:
            Tuple of (generation_result, execution_result)
        """
        # Generate SQL
        gen_result = self.generate_sql(query, table_names, additional_context)

        if not gen_result.success or not gen_result.query:
            return gen_result, None

        # Execute SQL
        exec_result = self.execute_sql(gen_result.query)

        return gen_result, exec_result

    def explain_query(self, query: str) -> str:
        """Generate human-readable explanation of SQL query.

        Args:
            query: SQL query to explain

        Returns:
            Explanation string
        """
        if not self._llm_client:
            return "Unable to explain query: LLM not configured"

        try:
            response = self._llm_client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": "Explain SQL queries in simple, non-technical language.",
                    },
                    {
                        "role": "user",
                        "content": f"Explain what this SQL query does in 2-3 sentences:\n{query}",
                    },
                ],
                temperature=0.3,
                max_tokens=200,
            )

            return response.choices[0].message.content or "Unable to generate explanation"

        except Exception as e:
            logger.error(f"Query explanation failed: {e}")
            return f"Unable to explain query: {e}"
