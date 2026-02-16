"""Planning Agent for query decomposition and task orchestration."""

import json
import logging
import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

try:
    from openai import AzureOpenAI, OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class TaskType(str, Enum):
    """Types of tasks the system can execute."""

    SQL_QUERY = "sql_query"
    PYTHON_ANALYSIS = "python_analysis"
    VISUALIZATION = "visualization"
    SYNTHESIS = "synthesis"


class TaskStatus(str, Enum):
    """Status of a task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Task(BaseModel):
    """A single task in the execution plan."""

    id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    description: str
    task_type: TaskType
    dependencies: list[str] = Field(default_factory=list)
    estimated_time: str = "5s"
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: int = 0


class ExecutionPlan(BaseModel):
    """Complete execution plan for a query."""

    plan_id: str = Field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    query: str
    main_objective: str
    tasks: list[Task] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"
    confidence: float = 0.0


class ParsedIntent(BaseModel):
    """Parsed intent from user query."""

    metrics: list[str] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    filters: list[str] = Field(default_factory=list)
    aggregations: list[str] = Field(default_factory=list)
    time_period: Optional[str] = None
    action: str = "query"  # query, analyze, visualize, compare
    confidence: float = 0.0
    ambiguities: list[str] = Field(default_factory=list)


class PlanningAgent:
    """Agent for planning and orchestrating query execution."""

    SYSTEM_PROMPT = """You are an expert data analyst assistant that helps plan and execute data queries.
Your job is to:
1. Parse user queries to understand their intent
2. Identify required metrics, dimensions, and filters
3. Create step-by-step execution plans
4. Break complex queries into manageable tasks

When parsing queries:
- Identify the metrics the user wants (e.g., revenue, count, average)
- Identify dimensions for grouping (e.g., by region, by time)
- Identify any filters or conditions
- Note any ambiguities that need clarification

When creating plans:
- Each task should be atomic and well-defined
- Tasks can depend on other tasks
- Estimate execution time for each task
- Include data retrieval, analysis, and visualization as needed
"""

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        model: Optional[str] = None,
        # Legacy parameters for backward compatibility
        azure_endpoint: Optional[str] = None,
        azure_api_key: Optional[str] = None,
        azure_deployment: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
    ):
        """Initialize Planning Agent.

        Args:
            llm_client: Pre-configured LLM client (OpenAI-compatible)
            model: Model name to use
            azure_endpoint: (Legacy) Azure OpenAI endpoint
            azure_api_key: (Legacy) Azure OpenAI API key
            azure_deployment: (Legacy) Azure deployment name
            openrouter_api_key: (Legacy) OpenRouter API key for fallback
        """
        # Use provided client if available
        if llm_client is not None and model is not None:
            self._llm_client = llm_client
            self._model = model
        else:
            # Legacy initialization for backward compatibility
            self._llm_client: Optional[Any] = None
            self._model: str = ""
            self._init_legacy_client(azure_endpoint, azure_api_key, azure_deployment, openrouter_api_key)

    def _init_legacy_client(
        self,
        azure_endpoint: Optional[str],
        azure_api_key: Optional[str],
        azure_deployment: Optional[str],
        openrouter_api_key: Optional[str],
    ) -> None:
        """Initialize LLM client using legacy parameters.

        Args:
            azure_endpoint: Azure OpenAI endpoint
            azure_api_key: Azure OpenAI API key
            azure_deployment: Azure deployment name
            openrouter_api_key: OpenRouter API key for fallback
        """

        if azure_endpoint and azure_api_key and OPENAI_AVAILABLE:
            self._llm_client = AzureOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=azure_api_key,
                api_version="2024-02-15-preview",
            )
            self._model = azure_deployment or "gpt-4-turbo"

        elif openrouter_api_key and OPENAI_AVAILABLE:
            self._llm_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_api_key,
            )
            self._model = "anthropic/claude-3-sonnet"

    def parse_intent(
        self,
        query: str,
        semantic_context: Optional[str] = None,
        rag_context: Optional[str] = None,
    ) -> ParsedIntent:
        """Parse user query to extract intent.

        Args:
            query: User's natural language query
            semantic_context: Context from semantic layer
            rag_context: Context from RAG system

        Returns:
            ParsedIntent with extracted information
        """
        if not self._llm_client:
            return self._fallback_parse(query)

        context_parts = []
        if semantic_context:
            context_parts.append(f"Semantic Layer:\n{semantic_context}")
        if rag_context:
            context_parts.append(f"Business Context:\n{rag_context}")

        prompt = f"""
{chr(10).join(context_parts)}

Parse the following user query and extract:
1. Metrics (what they want to measure)
2. Dimensions (how they want to group/slice data)
3. Filters (any conditions or constraints)
4. Time period (if mentioned)
5. Action type (query, analyze, visualize, compare)
6. Confidence (0.0-1.0) in your interpretation
7. Any ambiguities that need clarification

User Query: {query}

Respond in JSON format:
{{
    "metrics": ["metric1", "metric2"],
    "dimensions": ["dimension1"],
    "filters": ["filter1"],
    "time_period": "last quarter",
    "action": "query",
    "confidence": 0.85,
    "ambiguities": ["unclear which revenue metric"]
}}
"""

        try:
            response = self._llm_client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=500,
            )

            content = response.choices[0].message.content or "{}"

            # Extract JSON from response
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return ParsedIntent(**data)

            return self._fallback_parse(query)

        except Exception as e:
            logger.error(f"Intent parsing failed: {e}")
            return self._fallback_parse(query)

    def _fallback_parse(self, query: str) -> ParsedIntent:
        """Fallback intent parsing without LLM.

        Args:
            query: User query

        Returns:
            Basic ParsedIntent
        """
        query_lower = query.lower()

        # Simple keyword detection
        metrics = []
        if any(word in query_lower for word in ["revenue", "sales", "income"]):
            metrics.append("revenue")
        if any(word in query_lower for word in ["count", "number", "how many"]):
            metrics.append("count")
        if any(word in query_lower for word in ["average", "avg", "mean"]):
            metrics.append("average")

        dimensions = []
        if "region" in query_lower:
            dimensions.append("region")
        if any(word in query_lower for word in ["month", "quarter", "year", "time"]):
            dimensions.append("time")
        if "category" in query_lower:
            dimensions.append("category")

        action = "query"
        if any(word in query_lower for word in ["analyze", "analysis"]):
            action = "analyze"
        if any(word in query_lower for word in ["chart", "graph", "visualize", "show"]):
            action = "visualize"
        if "compare" in query_lower:
            action = "compare"

        time_period = None
        if "last quarter" in query_lower:
            time_period = "last_quarter"
        elif "this year" in query_lower or "ytd" in query_lower:
            time_period = "ytd"
        elif "last month" in query_lower:
            time_period = "last_month"

        return ParsedIntent(
            metrics=metrics or ["value"],
            dimensions=dimensions,
            filters=[],
            time_period=time_period,
            action=action,
            confidence=0.5,
            ambiguities=["Parsed with fallback method - may need clarification"],
        )

    def create_plan(
        self,
        query: str,
        parsed_intent: ParsedIntent,
        include_visualization: bool = True,
    ) -> ExecutionPlan:
        """Create execution plan from parsed intent.

        Args:
            query: Original user query
            parsed_intent: Parsed intent
            include_visualization: Whether to include visualization tasks

        Returns:
            ExecutionPlan with tasks
        """
        tasks = []

        # Task 1: SQL Query for data retrieval
        metrics_str = ", ".join(parsed_intent.metrics) if parsed_intent.metrics else "data"
        dimensions_str = ", ".join(parsed_intent.dimensions) if parsed_intent.dimensions else ""

        sql_description = f"Query database for {metrics_str}"
        if dimensions_str:
            sql_description += f" grouped by {dimensions_str}"
        if parsed_intent.time_period:
            sql_description += f" for {parsed_intent.time_period}"

        tasks.append(Task(
            id="task_1",
            description=sql_description,
            task_type=TaskType.SQL_QUERY,
            dependencies=[],
            estimated_time="2s",
        ))

        # Task 2: Analysis (if needed)
        if parsed_intent.action in ["analyze", "compare"]:
            analysis_type = "comparative analysis" if parsed_intent.action == "compare" else "statistical analysis"
            tasks.append(Task(
                id="task_2",
                description=f"Perform {analysis_type} on retrieved data",
                task_type=TaskType.PYTHON_ANALYSIS,
                dependencies=["task_1"],
                estimated_time="5s",
            ))

        # Task 3: Visualization
        if include_visualization and parsed_intent.action != "query":
            viz_dep = "task_2" if len(tasks) > 1 else "task_1"
            tasks.append(Task(
                id=f"task_{len(tasks) + 1}",
                description="Generate interactive visualization of results",
                task_type=TaskType.VISUALIZATION,
                dependencies=[viz_dep],
                estimated_time="3s",
            ))

        # Task 4: Synthesis (summary)
        tasks.append(Task(
            id=f"task_{len(tasks) + 1}",
            description="Generate natural language summary of findings",
            task_type=TaskType.SYNTHESIS,
            dependencies=[t.id for t in tasks],
            estimated_time="4s",
        ))

        main_objective = f"Analyze {metrics_str}"
        if dimensions_str:
            main_objective += f" by {dimensions_str}"

        return ExecutionPlan(
            query=query,
            main_objective=main_objective,
            tasks=tasks,
            confidence=parsed_intent.confidence,
        )

    def create_plan_with_llm(
        self,
        query: str,
        semantic_context: Optional[str] = None,
        available_tables: Optional[list[str]] = None,
    ) -> ExecutionPlan:
        """Create detailed plan using LLM.

        Args:
            query: User query
            semantic_context: Semantic layer context
            available_tables: List of available tables

        Returns:
            ExecutionPlan
        """
        if not self._llm_client:
            intent = self._fallback_parse(query)
            return self.create_plan(query, intent)

        tables_str = ", ".join(available_tables) if available_tables else "unknown"

        prompt = f"""
Create an execution plan for the following user query.

{f"Semantic Context: {semantic_context}" if semantic_context else ""}
Available Tables: {tables_str}

User Query: {query}

Create a step-by-step plan with the following task types:
- sql_query: Retrieve data from database
- python_analysis: Perform calculations or statistical analysis
- visualization: Create charts or graphs
- synthesis: Generate summary text

Respond in JSON format:
{{
    "main_objective": "Brief description of the goal",
    "confidence": 0.85,
    "tasks": [
        {{
            "id": "task_1",
            "description": "What this task does",
            "task_type": "sql_query",
            "dependencies": [],
            "estimated_time": "2s"
        }}
    ]
}}
"""

        try:
            response = self._llm_client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=1000,
            )

            content = response.choices[0].message.content or "{}"

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())

                tasks = []
                for task_data in data.get("tasks", []):
                    tasks.append(Task(
                        id=task_data.get("id", f"task_{len(tasks) + 1}"),
                        description=task_data.get("description", ""),
                        task_type=TaskType(task_data.get("task_type", "sql_query")),
                        dependencies=task_data.get("dependencies", []),
                        estimated_time=task_data.get("estimated_time", "5s"),
                    ))

                return ExecutionPlan(
                    query=query,
                    main_objective=data.get("main_objective", "Execute query"),
                    tasks=tasks,
                    confidence=data.get("confidence", 0.8),
                )

        except Exception as e:
            logger.error(f"LLM plan creation failed: {e}")

        # Fallback
        intent = self._fallback_parse(query)
        return self.create_plan(query, intent)

    def validate_plan(self, plan: ExecutionPlan) -> tuple[bool, list[str]]:
        """Validate execution plan for consistency.

        Args:
            plan: Execution plan to validate

        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []

        if not plan.tasks:
            issues.append("Plan has no tasks")
            return False, issues

        task_ids = {t.id for t in plan.tasks}

        for task in plan.tasks:
            # Check dependencies exist
            for dep in task.dependencies:
                if dep not in task_ids:
                    issues.append(f"Task {task.id} depends on non-existent task {dep}")

            # Check for circular dependencies
            if task.id in task.dependencies:
                issues.append(f"Task {task.id} has circular dependency on itself")

        # Check we have at least one data retrieval task
        has_data_task = any(t.task_type == TaskType.SQL_QUERY for t in plan.tasks)
        if not has_data_task:
            issues.append("Plan has no data retrieval task")

        return len(issues) == 0, issues

    def get_executable_tasks(self, plan: ExecutionPlan) -> list[Task]:
        """Get tasks that are ready to execute.

        Args:
            plan: Execution plan

        Returns:
            List of tasks with all dependencies completed
        """
        completed_ids = {
            t.id for t in plan.tasks
            if t.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED]
        }

        executable = []
        for task in plan.tasks:
            if task.status == TaskStatus.PENDING:
                deps_satisfied = all(dep in completed_ids for dep in task.dependencies)
                if deps_satisfied:
                    executable.append(task)

        return executable

    def update_task_status(
        self,
        plan: ExecutionPlan,
        task_id: str,
        status: TaskStatus,
        result: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
        execution_time_ms: int = 0,
    ) -> None:
        """Update task status in plan.

        Args:
            plan: Execution plan
            task_id: Task ID to update
            status: New status
            result: Task result if completed
            error: Error message if failed
            execution_time_ms: Execution time
        """
        for task in plan.tasks:
            if task.id == task_id:
                task.status = status
                task.result = result
                task.error = error
                task.execution_time_ms = execution_time_ms
                break

        # Update plan status
        statuses = [t.status for t in plan.tasks]
        if all(s == TaskStatus.COMPLETED for s in statuses):
            plan.status = "completed"
        elif any(s == TaskStatus.FAILED for s in statuses):
            plan.status = "failed"
        elif any(s == TaskStatus.RUNNING for s in statuses):
            plan.status = "running"

    def format_plan_for_display(self, plan: ExecutionPlan) -> str:
        """Format plan for user display.

        Args:
            plan: Execution plan

        Returns:
            Formatted string
        """
        lines = [
            f"Execution Plan: {plan.main_objective}",
            f"Confidence: {plan.confidence:.0%}",
            "",
            "Tasks:",
        ]

        for i, task in enumerate(plan.tasks, 1):
            status_icon = {
                TaskStatus.PENDING: "⏸",
                TaskStatus.RUNNING: "⚙",
                TaskStatus.COMPLETED: "✓",
                TaskStatus.FAILED: "✗",
                TaskStatus.SKIPPED: "⊘",
            }.get(task.status, "?")

            deps_str = f" (depends on: {', '.join(task.dependencies)})" if task.dependencies else ""
            lines.append(f"  {status_icon} {i}. {task.description} [{task.estimated_time}]{deps_str}")

        return "\n".join(lines)
