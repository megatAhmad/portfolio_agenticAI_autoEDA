# API Reference

> Complete API documentation for Agentic Data Analyst components

---

## Table of Contents

- [Orchestration](#orchestration)
  - [PlanningAgent](#planningagent)
  - [UncertaintyScorer](#uncertaintyscorer)
  - [HITLController](#hitlcontroller)
- [Agents](#agents)
  - [SQLGeneratorAgent](#sqlgeneratoragent)
  - [PythonAnalystAgent](#pythonanalystagent)
  - [VisualizationAgent](#visualizationagent)
- [Knowledge](#knowledge)
  - [SemanticLayer](#semanticlayer)
  - [RAGSystem](#ragsystem)
- [Execution](#execution)
  - [SecureSandbox](#securesandbox)
  - [DatabaseManager](#databasemanager)
- [Models](#models)

---

## Orchestration

### PlanningAgent

**Module:** `app.orchestration.planning_agent`

The Planning Agent parses user queries, extracts intent, and creates execution plans.

#### Class: `PlanningAgent`

```python
from app.orchestration.planning_agent import PlanningAgent

agent = PlanningAgent(
    azure_endpoint="https://...",
    azure_api_key="...",
    azure_deployment="gpt-4-turbo",
    openrouter_api_key="..."  # Fallback
)
```

##### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `parse_intent()` | `query: str`, `semantic_context: str`, `rag_context: str` | `ParsedIntent` | Extract intent from natural language query |
| `create_plan()` | `query: str`, `parsed_intent: ParsedIntent`, `include_visualization: bool` | `ExecutionPlan` | Create task execution plan |
| `create_plan_with_llm()` | `query: str`, `semantic_context: str`, `available_tables: list` | `ExecutionPlan` | Create detailed plan using LLM |
| `validate_plan()` | `plan: ExecutionPlan` | `tuple[bool, list[str]]` | Validate plan consistency |
| `get_executable_tasks()` | `plan: ExecutionPlan` | `list[Task]` | Get tasks ready to execute |
| `update_task_status()` | `plan`, `task_id`, `status`, `result`, `error` | `None` | Update task status |

##### Example

```python
from app.orchestration.planning_agent import PlanningAgent, ParsedIntent

agent = PlanningAgent(
    azure_endpoint="https://my-resource.openai.azure.com/",
    azure_api_key="my-api-key",
    azure_deployment="gpt-4-turbo"
)

# Parse user query
intent = agent.parse_intent(
    query="Show revenue by region for last quarter",
    semantic_context="revenue = SUM(order_amount)",
    rag_context="Business operates in NA, EU, APAC regions"
)

print(f"Metrics: {intent.metrics}")      # ['revenue']
print(f"Dimensions: {intent.dimensions}")  # ['region']
print(f"Confidence: {intent.confidence}")  # 0.92

# Create execution plan
plan = agent.create_plan(
    query="Show revenue by region",
    parsed_intent=intent,
    include_visualization=True
)

print(f"Tasks: {len(plan.tasks)}")  # 4
for task in plan.tasks:
    print(f"  - {task.task_type}: {task.description}")
```

---

### UncertaintyScorer

**Module:** `app.orchestration.uncertainty_scorer`

Evaluates query confidence using a three-factor weighted scoring system.

#### Class: `UncertaintyScorer`

```python
from app.orchestration.uncertainty_scorer import UncertaintyScorer

scorer = UncertaintyScorer(
    threshold=0.95,      # HITL trigger threshold
    data_weight=0.35,    # Data completeness weight
    schema_weight=0.35,  # Schema confidence weight
    query_weight=0.30    # Query confidence weight
)
```

##### Scoring Formula

```
Overall Score = (data_weight × data_score) +
                (schema_weight × schema_score) +
                (query_weight × query_score)

Example:
  Data Score: 0.90 × 0.35 = 0.315
  Schema Score: 0.80 × 0.35 = 0.280
  Query Score: 0.85 × 0.30 = 0.255
  ─────────────────────────────────
  Overall: 0.850 (85%)
```

##### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `evaluate()` | `parsed_intent`, `semantic_layer`, `data_profile` | `UncertaintyResult` | Full uncertainty evaluation |
| `calculate_data_completeness()` | `data_profile`, `required_columns` | `tuple[float, list]` | Data quality score |
| `calculate_schema_confidence()` | `parsed_intent`, `semantic_layer` | `tuple[float, list, list]` | Schema mapping score |
| `calculate_query_confidence()` | `parsed_intent` | `tuple[float, list]` | Query interpretation score |
| `recalculate_with_clarifications()` | `original_result`, `clarifications` | `UncertaintyResult` | Recalculate after user input |

##### Example

```python
from app.orchestration.uncertainty_scorer import UncertaintyScorer
from app.knowledge.semantic_layer import SemanticLayer

scorer = UncertaintyScorer(threshold=0.95)
semantic_layer = SemanticLayer(config_path="config/semantic_layer.json")

# Evaluate query confidence
result = scorer.evaluate(
    parsed_intent=intent,
    semantic_layer=semantic_layer,
    data_profile={"columns": {"revenue": {"null_rate": 0.02}}}
)

print(f"Overall Score: {result.score:.0%}")           # 87%
print(f"Needs Clarification: {result.needs_clarification}")  # True
print(f"Questions: {len(result.suggested_questions)}")  # 2

# Display breakdown
print(f"Data: {result.breakdown.data_completeness:.0%}")
print(f"Schema: {result.breakdown.schema_confidence:.0%}")
print(f"Query: {result.breakdown.query_confidence:.0%}")
```

---

### HITLController

**Module:** `app.orchestration.hitl_controller`

Manages human-in-the-loop interactions including clarifications and approvals.

#### Class: `HITLController`

```python
from app.orchestration.hitl_controller import HITLController

hitl = HITLController(
    db_manager=db_manager,      # Optional: for logging
    semantic_layer=semantic_layer  # Optional: for learning
)
```

##### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `create_clarification_session()` | `uncertainty_result`, `conversation_id` | `ClarificationSession` | Create question session |
| `record_response()` | `session_id`, `question_id`, `response` | `bool` | Record user answer |
| `record_responses_batch()` | `session_id`, `responses: dict` | `dict[str, str]` | Record multiple answers |
| `create_approval_request()` | `plan`, `uncertainty_score` | `ApprovalRequest` | Request plan approval |
| `approve_plan()` | `request_id`, `modifications` | `ExecutionPlan` | Approve with modifications |
| `reject_plan()` | `request_id`, `reason` | `bool` | Reject execution plan |

##### Example

```python
from app.orchestration.hitl_controller import HITLController

hitl = HITLController()

# Create clarification session from uncertainty result
session = hitl.create_clarification_session(
    uncertainty_result=result,
    conversation_id="conv_123"
)

# Display questions
for q in session.questions:
    print(f"Q: {q.text}")
    for opt in q.options:
        print(f"   - {opt['label']}")

# Record user responses
clarified = hitl.record_responses_batch(
    session_id=session.session_id,
    responses={
        "revenue": "total_revenue",
        "time_period": "last_quarter"
    }
)

# Create approval request
approval = hitl.create_approval_request(
    plan=execution_plan,
    uncertainty_score=0.96
)

# Approve (optionally removing tasks)
approved_plan = hitl.approve_plan(
    request_id=approval.request_id,
    modifications=[]  # or ["task_3"] to remove task
)
```

---

## Agents

### SQLGeneratorAgent

**Module:** `app.agents.sql_generator`

Generates and executes SQL queries with semantic context awareness.

#### Class: `SQLGeneratorAgent`

```python
from app.agents.sql_generator import SQLGeneratorAgent

sql_agent = SQLGeneratorAgent(
    db_manager=db_manager,
    semantic_layer=semantic_layer,
    azure_endpoint="...",
    azure_api_key="...",
    azure_deployment="gpt-4-turbo"
)
```

##### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `generate_query()` | `natural_query`, `table_name`, `schema`, `context` | `SQLGenerationResult` | Generate SQL from NL |
| `validate_query()` | `sql_query` | `tuple[bool, list]` | Security validation |
| `execute_query()` | `sql_query`, `params` | `SQLExecutionResult` | Execute validated SQL |
| `generate_and_execute()` | `natural_query`, `context` | `tuple[SQLGenResult, SQLExecResult]` | Full pipeline |

##### Example

```python
# Generate SQL from natural language
gen_result = sql_agent.generate_query(
    natural_query="Total revenue by region last quarter",
    table_name="orders",
    schema={"revenue": "DECIMAL", "region": "VARCHAR"},
    additional_context="Exclude test orders"
)

print(f"SQL: {gen_result.query}")
# SELECT region, SUM(revenue) as total_revenue
# FROM orders
# WHERE order_date >= '2024-10-01' AND is_test = false
# GROUP BY region

# Execute
exec_result = sql_agent.execute_query(gen_result.query)
print(f"Rows: {len(exec_result.data)}")
```

---

### VisualizationAgent

**Module:** `app.agents.visualization`

Creates interactive Plotly visualizations with automatic chart type selection.

#### Class: `VisualizationAgent`

```python
from app.agents.visualization import VisualizationAgent

viz_agent = VisualizationAgent(
    azure_endpoint="...",  # Optional: for chart suggestions
    azure_api_key="..."
)
```

##### Chart Type Selection Logic

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTO CHART SELECTION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Time + Numeric       → Line Chart                               │
│  Category + Numeric   → Bar Chart (if categories <= 10)          │
│  2+ Numeric           → Scatter Plot                             │
│  2+ Categories + Num  → Heatmap                                  │
│  1 Numeric only       → Histogram                                │
│  Composition request  → Pie Chart                                │
│  Default              → Table                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

##### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `select_chart_type()` | `data`, `query_intent` | `str` | Auto-select best chart |
| `create_chart()` | `data`, `config: ChartConfig` | `VisualizationResult` | Create specific chart |
| `auto_visualize()` | `data`, `title`, `query_intent` | `VisualizationResult` | Auto chart creation |
| `suggest_chart_type()` | `query`, `data_description` | `str` | LLM chart suggestion |
| `create_dashboard()` | `charts`, `title`, `cols` | `str` | Multi-chart dashboard |

##### Example

```python
from app.agents.visualization import VisualizationAgent, ChartConfig

viz_agent = VisualizationAgent()

data = [
    {"region": "North", "revenue": 1000000},
    {"region": "South", "revenue": 850000},
    {"region": "East", "revenue": 920000},
]

# Auto visualization
result = viz_agent.auto_visualize(
    data=data,
    title="Revenue by Region"
)

print(f"Chart Type: {result.chart_type}")  # bar_chart
# result.chart_html contains the Plotly HTML

# Manual configuration
config = ChartConfig(
    chart_type="pie_chart",
    x_column="region",
    y_column="revenue",
    title="Revenue Distribution",
    height=500
)

pie_result = viz_agent.create_chart(data, config)
```

---

## Knowledge

### SemanticLayer

**Module:** `app.knowledge.semantic_layer`

Business context management with metrics, dimensions, synonyms, and rules.

#### Class: `SemanticLayer`

```python
from app.knowledge.semantic_layer import SemanticLayer

semantic = SemanticLayer(config_path="config/semantic_layer.json")
```

##### Configuration Schema

```json
{
  "version": "1.0",
  "metrics": [
    {
      "name": "total_revenue",
      "display_name": "Total Revenue",
      "description": "Sum of all order amounts",
      "sql": "SUM(net_order_amount)",
      "synonyms": ["sales", "revenue", "income"]
    }
  ],
  "dimensions": [
    {
      "name": "customer_region",
      "display_name": "Region",
      "column": "region",
      "type": "categorical",
      "synonyms": ["geo", "geography", "location"]
    }
  ],
  "business_rules": [
    {
      "name": "exclude_test_orders",
      "filter": "is_test_order = FALSE"
    }
  ]
}
```

##### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `get_metric()` | `name: str` | `Metric` | Get metric by name or synonym |
| `get_dimension()` | `name: str` | `Dimension` | Get dimension by name or synonym |
| `resolve_term()` | `term: str` | `dict` | Resolve term to metric/dimension |
| `find_matching_metrics()` | `term: str` | `list[Metric]` | Find all matching metrics |
| `add_synonym()` | `term`, `canonical_name`, `term_type` | `None` | Add new synonym |
| `to_prompt_context()` | | `str` | Generate LLM context string |

##### Example

```python
semantic = SemanticLayer(config_path="config/semantic_layer.json")

# Resolve user term
metric = semantic.get_metric("sales")  # Returns total_revenue metric
print(f"SQL: {metric.sql}")  # SUM(net_order_amount)

# Check for ambiguity
matches = semantic.find_matching_metrics("revenue")
if len(matches) > 1:
    print("Ambiguous! Multiple matches found")

# Add synonym from user clarification
semantic.add_synonym("money", "total_revenue", "metric")

# Generate context for LLM
context = semantic.to_prompt_context()
# "Available metrics: Total Revenue (SUM of order amounts)..."
```

---

### RAGSystem

**Module:** `app.knowledge.rag_system`

Vector-based retrieval for business context using ChromaDB.

#### Class: `RAGSystem`

```python
from app.knowledge.rag_system import RAGSystem

rag = RAGSystem(
    persist_dir=Path("./chroma_db"),
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"
)
```

##### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `add_document()` | `content`, `source`, `metadata` | `list[str]` | Add document chunks |
| `add_json_context()` | `json_path`, `source_name` | `list[str]` | Add JSON context file |
| `add_text_context()` | `text_path`, `source_name` | `list[str]` | Add text context file |
| `retrieve()` | `query`, `n_results`, `filter` | `RetrievalResult` | Retrieve relevant docs |
| `get_context_for_query()` | `query`, `n_results` | `str` | Get formatted context |
| `delete_source()` | `source: str` | `int` | Remove documents by source |
| `get_stats()` | | `dict` | Collection statistics |

##### Example

```python
rag = RAGSystem(persist_dir=Path("./chroma_db"))

# Add business context
rag.add_document(
    content="Revenue is calculated after discounts and returns...",
    source="finance_glossary.txt",
    metadata={"type": "definition", "department": "finance"}
)

# Add JSON context
rag.add_json_context(Path("config/semantic_layer.json"))

# Retrieve context for query
results = rag.retrieve("What counts as revenue?", n_results=3)
for doc in results.documents:
    print(f"[{doc.source}] {doc.content[:100]}...")

# Get formatted context for LLM
context = rag.get_context_for_query("revenue calculation")
print(context)
# "Relevant Business Context:
#  [1] (relevance: 0.89) Revenue is calculated after discounts..."
```

---

## Execution

### SecureSandbox

**Module:** `app.execution.sandbox`

Docker-based secure Python execution environment.

#### Class: `SecureSandbox`

```python
from app.execution.sandbox import SecureSandbox

sandbox = SecureSandbox(
    timeout=30,           # Max execution seconds
    memory_limit="512m",  # Container memory
    cpu_quota=50000       # CPU limit (50%)
)
```

##### Security Features

| Feature | Configuration | Description |
|---------|--------------|-------------|
| Network | `disabled` | No external connections |
| Filesystem | `read-only` | Cannot write outside /tmp |
| Memory | `512MB` | OOM kill if exceeded |
| Timeout | `30s` | Process killed after |
| Capabilities | `none` | All Linux capabilities dropped |

##### Blocked Patterns

```python
FORBIDDEN = {
    "eval", "exec", "__import__", "compile", "open",
    "os", "subprocess", "requests", "urllib", "socket"
}
```

##### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `execute()` | `code`, `input_data` | `SandboxResult` | Execute in Docker |
| `execute_simple()` | `code` | `SandboxResult` | Execute without Docker (testing) |

##### Example

```python
sandbox = SecureSandbox(timeout=30)

code = """
import pandas as pd
df = pd.DataFrame(data)
result = df.groupby('region')['revenue'].sum().to_dict()
"""

result = sandbox.execute(
    code=code,
    input_data={"data": [{"region": "North", "revenue": 100}]}
)

if result.success:
    print(f"Output: {result.output}")
    print(f"Time: {result.execution_time_ms}ms")
else:
    print(f"Error: {result.error}")
```

---

## Models

### Data Models Reference

```python
# Planning Agent Models
class ParsedIntent(BaseModel):
    metrics: list[str]
    dimensions: list[str]
    filters: list[str]
    time_period: Optional[str]
    action: str  # query, analyze, visualize, compare
    confidence: float
    ambiguities: list[str]

class Task(BaseModel):
    id: str
    description: str
    task_type: TaskType  # sql_query, python_analysis, visualization, synthesis
    dependencies: list[str]
    estimated_time: str
    status: TaskStatus  # pending, running, completed, failed, skipped

class ExecutionPlan(BaseModel):
    plan_id: str
    query: str
    main_objective: str
    tasks: list[Task]
    confidence: float

# Uncertainty Models
class UncertaintyBreakdown(BaseModel):
    data_completeness: float  # 0-1
    schema_confidence: float  # 0-1
    query_confidence: float   # 0-1
    overall: float            # Weighted average

class UncertaintyResult(BaseModel):
    score: float
    breakdown: UncertaintyBreakdown
    needs_clarification: bool
    reasons: list[str]
    suggested_questions: list[dict]

# HITL Models
class ClarificationQuestion(BaseModel):
    id: str
    question_type: ClarificationType  # multiple_choice, open_ended, confirmation
    text: str
    term: Optional[str]
    options: list[dict]
    response: Optional[str]

class ApprovalRequest(BaseModel):
    request_id: str
    plan: ExecutionPlan
    uncertainty_score: float
    approved: Optional[bool]

# Sandbox Models
class SandboxResult(BaseModel):
    success: bool
    stdout: str
    stderr: str
    output: dict
    execution_time_ms: int
    error: Optional[str]

# Visualization Models
class ChartConfig(BaseModel):
    chart_type: str
    x_column: Optional[str]
    y_column: Optional[str]
    color_column: Optional[str]
    title: str
    height: int = 400

class VisualizationResult(BaseModel):
    success: bool
    chart_type: str
    chart_json: Optional[str]
    chart_html: Optional[str]
    error: Optional[str]
```

---

## Error Handling

All components follow a consistent error handling pattern:

```python
# Components return result objects with success/error fields
result = component.operation(...)

if result.success:
    # Handle successful result
    process(result.output)
else:
    # Handle error gracefully
    log.error(result.error)
    show_user_friendly_message(result.error)

# Auto-retry for transient errors (max 3 attempts)
@retry(max_attempts=3, backoff=exponential)
def make_llm_call():
    ...
```

---

## Next Steps

- [User Guide](../guides/user-guide.md) - Step-by-step usage instructions
- [Architecture Deep Dive](../guides/architecture.md) - Detailed system design
- [Examples](../guides/examples.md) - Common use cases
