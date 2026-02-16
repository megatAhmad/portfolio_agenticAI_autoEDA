"""Python Analyst Agent for generating and executing analysis code."""

import logging
import re
from typing import Any, Optional

from pydantic import BaseModel

from app.execution.sandbox import SecureSandbox, SandboxResult

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


class CodeGenerationResult(BaseModel):
    """Result of code generation."""

    success: bool
    code: Optional[str] = None
    explanation: str = ""
    confidence: float = 0.0
    error: Optional[str] = None


class AnalysisResult(BaseModel):
    """Result of Python analysis execution."""

    success: bool
    output: dict[str, Any] = {}
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: int = 0
    error: Optional[str] = None


class PythonAnalystAgent:
    """Agent for generating and executing Python analysis code."""

    SYSTEM_PROMPT = """You are an expert Python data analyst specializing in pandas and data visualization.
Your task is to generate Python code for data analysis based on user requests.

Guidelines:
1. Use pandas for data manipulation
2. Use numpy for numerical operations
3. Use plotly for interactive visualizations (preferred) or matplotlib
4. The input data will be available as a pandas DataFrame named 'df'
5. Store your main result in a variable named 'result'
6. Store any figure/plot in a variable named 'fig'
7. Write clean, efficient code with comments
8. Handle edge cases (empty data, missing values)
9. DO NOT use any network operations, file I/O, or system calls
10. Return ONLY the Python code, no explanations

Available packages: pandas, numpy, scipy, scikit-learn, plotly, matplotlib, seaborn
"""

    def __init__(
        self,
        sandbox: Optional[SecureSandbox] = None,
        llm_client: Optional[Any] = None,
        model: Optional[str] = None,
        settings: Optional[AppSettings] = None,
        # Legacy parameters for backward compatibility
        azure_endpoint: Optional[str] = None,
        azure_api_key: Optional[str] = None,
        azure_deployment: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
    ):
        """Initialize Python Analyst Agent.

        Args:
            sandbox: Secure sandbox for code execution
            llm_client: Pre-configured LLM client (OpenAI-compatible)
            model: Model name to use (overrides configured model)
            settings: Application settings (for model configuration)
            azure_endpoint: (Legacy) Azure OpenAI endpoint
            azure_api_key: (Legacy) Azure OpenAI API key
            azure_deployment: (Legacy) Azure deployment name
            openrouter_api_key: (Legacy) OpenRouter API key for fallback
        """
        self.sandbox = sandbox or SecureSandbox()

        self._llm_client: Optional[Any] = None
        self._model: str = ""

        # Use provided client if available
        if llm_client is not None and model is not None:
            self._llm_client = llm_client
            self._model = model
            logger.info(f"Python Analyst initialized with provided client and model: {model}")
        # Use configured model for Python analyst
        elif LLM_CLIENT_AVAILABLE:
            if settings is None:
                settings = get_settings()
            self._llm_client, self._model = create_llm_client_for_agent(
                "python_analyst", settings, prefer_fast=False
            )
            logger.info(f"Python Analyst initialized with model: {self._model}")
        # Try Azure OpenAI first (legacy)
        elif azure_endpoint and azure_api_key and OPENAI_AVAILABLE:
            self._llm_client = AzureOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=azure_api_key,
                api_version="2024-02-15-preview",
            )
            self._model = azure_deployment or "gpt-4-turbo"
            logger.info("Using Azure OpenAI for Python analysis (legacy)")
        # Fallback to OpenRouter (legacy)
        elif openrouter_api_key and OPENAI_AVAILABLE:
            self._llm_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_api_key,
            )
            self._model = "anthropic/claude-3-sonnet"
            logger.info("Using OpenRouter for Python analysis (legacy)")

    def generate_code(
        self,
        task: str,
        data_schema: Optional[dict[str, Any]] = None,
        data_sample: Optional[list[dict[str, Any]]] = None,
        additional_context: Optional[str] = None,
    ) -> CodeGenerationResult:
        """Generate Python analysis code from task description.

        Args:
            task: Description of the analysis task
            data_schema: Schema of the input data
            data_sample: Sample rows from the data
            additional_context: Additional context for code generation

        Returns:
            CodeGenerationResult with generated code
        """
        if not self._llm_client:
            return CodeGenerationResult(
                success=False,
                error="LLM client not configured",
            )

        # Build context
        context_parts = []

        if data_schema:
            schema_str = "\n".join(
                f"  - {col}: {info.get('type', 'unknown')}"
                for col, info in data_schema.items()
            )
            context_parts.append(f"Data Schema:\n{schema_str}")

        if data_sample:
            import json
            sample_str = json.dumps(data_sample[:3], indent=2, default=str)
            context_parts.append(f"Sample Data (first 3 rows):\n{sample_str}")

        if additional_context:
            context_parts.append(f"Additional Context:\n{additional_context}")

        user_prompt = f"""
{chr(10).join(context_parts)}

Task: {task}

Generate Python code to accomplish this task. The data is available as a pandas DataFrame named 'df'.
Store your main result in a variable named 'result'.
If creating a visualization, store it in a variable named 'fig'.

Return ONLY the Python code, no explanations.
"""

        try:
            response = self._llm_client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=2000,
            )

            content = response.choices[0].message.content or ""

            # Extract code from response
            code = self._extract_code(content)

            if not code:
                return CodeGenerationResult(
                    success=False,
                    error="Could not extract code from response",
                )

            return CodeGenerationResult(
                success=True,
                code=code,
                confidence=0.85,
                explanation="Code generated successfully",
            )

        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return CodeGenerationResult(
                success=False,
                error=str(e),
            )

    def _extract_code(self, content: str) -> str:
        """Extract Python code from LLM response.

        Args:
            content: LLM response content

        Returns:
            Extracted code
        """
        # Try to find code block
        code_match = re.search(r"```python\s*(.*?)```", content, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        # Try generic code block
        code_match = re.search(r"```\s*(.*?)```", content, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        # Assume entire content is code
        return content.strip()

    def execute_code(
        self,
        code: str,
        data: Optional[dict[str, Any]] = None,
    ) -> AnalysisResult:
        """Execute Python code in sandbox.

        Args:
            code: Python code to execute
            data: Data to make available (will be converted to DataFrame)

        Returns:
            AnalysisResult with execution details
        """
        # Prepare data for sandbox
        input_data = {}
        if data:
            input_data["records"] = data if isinstance(data, list) else [data]

        # Wrap code to handle data input
        wrapped_code = f"""
import pandas as pd
import numpy as np

# Load data from input
if 'records' in data and data['records']:
    df = pd.DataFrame(data['records'])
else:
    df = pd.DataFrame()

# User code starts here
{code}
"""

        # Execute in sandbox
        result = self.sandbox.execute(wrapped_code, input_data)

        return AnalysisResult(
            success=result.success,
            output=result.output,
            stdout=result.stdout,
            stderr=result.stderr,
            execution_time_ms=result.execution_time_ms,
            error=result.error,
        )

    def generate_and_execute(
        self,
        task: str,
        data: Optional[list[dict[str, Any]]] = None,
        data_schema: Optional[dict[str, Any]] = None,
        additional_context: Optional[str] = None,
    ) -> tuple[CodeGenerationResult, Optional[AnalysisResult]]:
        """Generate code and execute it.

        Args:
            task: Analysis task description
            data: Input data records
            data_schema: Schema of input data
            additional_context: Additional context

        Returns:
            Tuple of (generation_result, execution_result)
        """
        # Use first few rows as sample
        sample = data[:5] if data else None

        # Generate code
        gen_result = self.generate_code(
            task=task,
            data_schema=data_schema,
            data_sample=sample,
            additional_context=additional_context,
        )

        if not gen_result.success or not gen_result.code:
            return gen_result, None

        # Execute code
        exec_result = self.execute_code(gen_result.code, data)

        return gen_result, exec_result

    def generate_statistical_analysis(
        self,
        data: list[dict[str, Any]],
        analysis_type: str = "descriptive",
    ) -> tuple[CodeGenerationResult, Optional[AnalysisResult]]:
        """Generate and execute statistical analysis.

        Args:
            data: Input data
            analysis_type: Type of analysis ('descriptive', 'correlation', 'distribution')

        Returns:
            Tuple of results
        """
        task_map = {
            "descriptive": "Generate descriptive statistics (mean, median, std, min, max, quartiles) for all numeric columns. Store the result as a DataFrame in 'result'.",
            "correlation": "Calculate correlation matrix for numeric columns and identify the strongest correlations. Store the correlation matrix in 'result'.",
            "distribution": "Analyze the distribution of each numeric column (skewness, kurtosis, normality test). Store results in 'result' as a DataFrame.",
        }

        task = task_map.get(analysis_type, task_map["descriptive"])
        return self.generate_and_execute(task, data)

    def generate_trend_analysis(
        self,
        data: list[dict[str, Any]],
        date_column: str,
        value_column: str,
    ) -> tuple[CodeGenerationResult, Optional[AnalysisResult]]:
        """Generate and execute trend analysis.

        Args:
            data: Input data
            date_column: Name of date column
            value_column: Name of value column

        Returns:
            Tuple of results
        """
        task = f"""
Analyze trends in '{value_column}' over time ('{date_column}'):
1. Convert date column to datetime
2. Calculate rolling averages (7-day, 30-day)
3. Calculate month-over-month growth rates
4. Identify any seasonality patterns
5. Store a summary DataFrame in 'result' with columns: date, value, rolling_7d, rolling_30d, mom_growth
"""
        return self.generate_and_execute(task, data)

    def explain_code(self, code: str) -> str:
        """Generate human-readable explanation of Python code.

        Args:
            code: Python code to explain

        Returns:
            Explanation string
        """
        if not self._llm_client:
            return "Unable to explain code: LLM not configured"

        try:
            response = self._llm_client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": "Explain Python code in simple, non-technical language.",
                    },
                    {
                        "role": "user",
                        "content": f"Explain what this Python code does in 2-3 sentences:\n```python\n{code}\n```",
                    },
                ],
                temperature=0.3,
                max_tokens=200,
            )

            return response.choices[0].message.content or "Unable to generate explanation"

        except Exception as e:
            logger.error(f"Code explanation failed: {e}")
            return f"Unable to explain code: {e}"
