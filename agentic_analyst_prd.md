# Project Requirements Document (PRD)
## Agentic Data Analyst: Local-First Semantic Analytics Platform

**Document Version:** 1.0  
**Date:** January 27, 2026  
**Project Code:** ADA-2026  
**Classification:** Technical Specification

---

## Executive Summary

### Project Vision
Build a production-grade agentic data analyst that combines semantic context understanding with human-in-the-loop validation, operating entirely on local/free-tier infrastructure. The system addresses the critical gap identified in research: **95% of AI analytics tools fail on ambiguous queries** due to lack of business context and absent clarification mechanisms.

### Research Foundation
Based on comprehensive analysis of 2026's leading agentic analytics platforms (Omni, Snowflake Cortex, ThoughtSpot, Tableau), this project implements the proven "consultant pattern"—AI that asks clarifying questions rather than guessing when facing ambiguity. Research shows this approach improves accuracy from **42.5% to 92.5%** on complex queries.

### Core Differentiators
1. **Semantic Context Validation**: Automatically assesses whether provided business context (TXT/JSON) is sufficient to interpret data, triggering user requests for additional context when gaps exceed 5%
2. **Uncertainty-Driven HITL**: 95% confidence threshold triggers human clarification before query execution
3. **Zero Cloud Dependency**: Fully local execution with PostgreSQL, ChromaDB, and containerized Python sandbox
4. **Transparent Planning**: Hierarchical task breakdown with explicit user approval before execution

### Success Metrics
| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Query Accuracy (with context) | >90% | User validation on 100-query test set |
| Clarification Precision | <15% false positives | Ratio of unnecessary clarifications |
| Context Gap Detection | >85% recall | Manual review of missed ambiguities |
| Response Latency (cached) | <2s P95 | Application performance monitoring |
| User Satisfaction | >4.2/5.0 | Post-interaction surveys |

### Budget & Timeline
- **Infrastructure Cost**: $0/month (local-first architecture)
- **API Costs**: ~$50-150/month (Azure OpenAI consumption-based)
- **Development Timeline**: 12 weeks (phased implementation)
- **Team Size**: 2-3 engineers + 1 data analyst (SME)

---

## System Architecture

### Architectural Principles
1. **Local-First Design**: All computation and storage on-premise/local machine
2. **Modular Components**: Loosely coupled services for independent testing/scaling
3. **Fail-Safe Defaults**: System halts and requests clarification rather than proceeding with uncertain assumptions
4. **Audit Trail**: Complete logging of all interactions, queries, and agent decisions

### High-Level Architecture Diagram (Text Representation)

```
┌─────────────────────────────────────────────────────────────────────┐
│                          STREAMLIT UI LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────┐ │
│  │ Chat         │  │ Context      │  │ Plan         │  │ Results │ │
│  │ Interface    │  │ Validator    │  │ Approval UI  │  │ Explorer│ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION ENGINE                            │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Planning Agent                               │ │
│  │  • Intent Classification  • Task Decomposition                  │ │
│  │  • Dependency Resolution  • Hierarchical Planning               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                 Uncertainty Scorer                              │ │
│  │  • Data Completeness (null rates, coverage)                     │ │
│  │  • Schema Confidence (field mapping accuracy)                   │ │
│  │  • Query Confidence (LLM self-assessment)                       │ │
│  │  • Threshold Evaluation (default: 95%)                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              HITL Controller                                    │ │
│  │  • Clarification Question Generator                             │ │
│  │  • User Response Parser                                         │ │
│  │  • Context Enrichment Loop                                      │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SPECIALIZED AGENTS                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐           │
│  │ SQL Generator │  │Python Analyst │  │ Visualization │           │
│  │ Agent         │  │ Agent         │  │ Agent         │           │
│  │ • Query Gen   │  │ • Code Gen    │  │ • Chart Gen   │           │
│  │ • Validation  │  │ • Execution   │  │ • Interactive │           │
│  └───────────────┘  └───────────────┘  └───────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     KNOWLEDGE & DATA LAYER                           │
│  ┌──────────────────────┐  ┌──────────────────────┐                 │
│  │  Semantic Layer      │  │  RAG System          │                 │
│  │  ┌────────────────┐  │  │  ┌────────────────┐ │                 │
│  │  │ Metric Defs    │  │  │  │ ChromaDB       │ │                 │
│  │  │ Column Mapping │  │  │  │ (Context Docs) │ │                 │
│  │  │ Business Rules │  │  │  │ HF Embeddings  │ │                 │
│  │  │ Relationships  │  │  │  └────────────────┘ │                 │
│  │  └────────────────┘  │  │                      │                 │
│  │  (JSON Config)       │  │                      │                 │
│  └──────────────────────┘  └──────────────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EXECUTION & STORAGE                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ Python Sandbox   │  │ PostgreSQL       │  │ Interaction DB   │  │
│  │ (Docker/Firejail)│  │ (User Data)      │  │ (Audit Log)      │  │
│  │ • pandas         │  │ • Tables         │  │ • Conversations  │  │
│  │ • numpy          │  │ • Views          │  │ • Clarifications │  │
│  │ • plotly         │  │ • Aggregations   │  │ • Feedback       │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         LLM INTEGRATION                              │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Azure OpenAI / OpenRouter API                                  │ │
│  │  • GPT-4-Turbo for planning and reasoning                       │ │
│  │  • GPT-3.5-Turbo for validation and formatting                  │ │
│  │  • Fallback/redundancy support                                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Descriptions

#### 1. Streamlit UI Layer
**Technology**: Streamlit 1.30+  
**Purpose**: User interaction interface with four main views
- **Chat Interface**: Natural language query input with conversation history
- **Context Validator**: Upload and validate TXT/JSON business context files
- **Plan Approval UI**: Display hierarchical task breakdown, await user confirmation
- **Results Explorer**: Interactive tables (AgGrid), Plotly charts, exportable outputs

#### 2. Orchestration Engine
**Technology**: Custom Python orchestrator (LangGraph-inspired state machine)  
**Components**:
- **Planning Agent**: Decomposes user queries into executable steps using LLM reasoning
- **Uncertainty Scorer**: Multi-factor confidence calculation (data completeness + schema alignment + query clarity)
- **HITL Controller**: Generates clarification questions, manages approval workflows

#### 3. Specialized Agents
**SQL Generator Agent**:
- Translates semantic requests into PostgreSQL queries
- Validates against schema before execution
- Implements query result caching

**Python Analyst Agent**:
- Generates pandas/numpy analysis code
- Executes in sandboxed environment
- Returns results + generated artifacts

**Visualization Agent**:
- Creates Plotly interactive charts
- Supports drill-down and filtering
- Exports to HTML/JSON

#### 4. Knowledge & Data Layer
**Semantic Layer** (JSON configuration):
```json
{
  "metrics": [
    {
      "name": "total_revenue",
      "sql": "SUM(order_amount)",
      "description": "Total revenue from all orders",
      "synonyms": ["sales", "income", "revenue"],
      "aggregation": "sum"
    }
  ],
  "dimensions": [
    {
      "name": "customer_region",
      "column": "region",
      "type": "categorical",
      "sample_values": ["North", "South", "East", "West"]
    }
  ],
  "relationships": [
    {
      "from_table": "orders",
      "to_table": "customers",
      "join_type": "inner",
      "on": "customer_id"
    }
  ]
}
```

**RAG System**:
- ChromaDB vector store for business context documents
- HuggingFace embeddings (all-MiniLM-L6-v2 or similar)
- Retrieval-augmented generation for domain-specific explanations

#### 5. Execution & Storage
**Python Sandbox**:
- Docker container OR Firejail for process isolation
- Whitelisted packages: pandas, numpy, scipy, plotly, scikit-learn
- Resource limits: 512MB RAM, 30s timeout
- No network access (air-gapped)

**PostgreSQL Database**:
- User-uploaded data tables
- Materialized views for common aggregations
- Query result cache table

**Interaction Database**:
- SQLite or PostgreSQL schema
- Tables: `conversations`, `clarifications`, `feedback`, `execution_logs`

---

## Functional Requirements

### FR-1: Data & Context Ingestion
**Priority**: P0 (Must Have)

**Description**: System must accept Excel/CSV data files and TXT/JSON context files, automatically validate context sufficiency.

**Acceptance Criteria**:
1. User can upload CSV/Excel files up to 100MB
2. System parses files and creates PostgreSQL tables automatically
3. User can upload TXT/JSON context files describing:
   - Column meanings and business definitions
   - Metric calculation formulas
   - Business rules and constraints
4. Context Validator analyzes uploaded context against data schema:
   - Identifies unmapped columns (coverage gap)
   - Flags missing metric definitions
   - Generates completeness score (0-100%)
5. If completeness < 95%, system generates specific requests:
   - "Column 'rev_amt' is not defined. Please explain its meaning."
   - "No aggregation rules found for 'customer_segment'. How should this be grouped?"

**Technical Implementation**:
```python
class ContextValidator:
    def __init__(self, semantic_layer_config: dict):
        self.config = semantic_layer_config
        self.min_completeness = 0.95
    
    def validate(self, data_schema: dict, context_docs: list[str]) -> ValidationResult:
        """
        Compare data schema against provided context
        Returns: ValidationResult with gaps and suggested questions
        """
        coverage_map = self._map_columns_to_context(data_schema, context_docs)
        
        unmapped_columns = [col for col, mapped in coverage_map.items() 
                           if not mapped]
        
        completeness_score = 1 - (len(unmapped_columns) / len(coverage_map))
        
        if completeness_score < self.min_completeness:
            questions = self._generate_context_questions(unmapped_columns)
            return ValidationResult(
                is_complete=False,
                score=completeness_score,
                missing_definitions=unmapped_columns,
                suggested_questions=questions
            )
        
        return ValidationResult(is_complete=True, score=completeness_score)
```

---

### FR-2: Uncertainty-Driven Clarification
**Priority**: P0 (Must Have)

**Description**: Before executing any query, system calculates uncertainty score and triggers human clarification if confidence < 95%.

**Acceptance Criteria**:
1. Uncertainty Scorer evaluates three dimensions:
   - **Data Completeness**: null rates, date coverage, expected vs actual columns
   - **Schema Confidence**: unambiguous mapping of query terms to database columns
   - **Query Confidence**: LLM self-assessment of interpretation certainty
2. If overall score < 0.95, system generates clarification questions:
   - Multiple choice (for disambiguation)
   - Open-ended (for missing context)
3. System waits for user response before proceeding
4. User responses are logged and used to enrich context for future queries
5. False positive rate tracked (user marks "this was unnecessary")

**Scoring Algorithm**:
```python
def calculate_uncertainty(query: str, parsed_intent: dict, 
                         data_profile: dict, schema: dict) -> float:
    # Data completeness (35% weight)
    null_rates = [data_profile[col]['null_rate'] 
                  for col in parsed_intent['required_columns']]
    data_score = 1 - np.mean(null_rates)
    
    # Schema confidence (35% weight)
    mapped_fields = 0
    for field in parsed_intent['requested_fields']:
        if field in schema['columns'] or \
           any(field.lower() in syn.lower() 
               for col in schema['columns'].values() 
               for syn in col.get('synonyms', [])):
            mapped_fields += 1
    schema_score = mapped_fields / len(parsed_intent['requested_fields'])
    
    # Query confidence (30% weight) - from LLM
    query_score = parsed_intent.get('llm_confidence', 0.85)
    
    overall = 0.35*data_score + 0.35*schema_score + 0.30*query_score
    return overall
```

**Example Clarification Flow**:
```
User: "Show me sales by region for Q3"

[System calculates uncertainty = 0.82 (< 0.95 threshold)]

System: "I need clarification on a few things:
1. Which 'sales' metric? I found:
   a) gross_revenue (sum of order amounts)
   b) net_revenue (after discounts)
   c) commission_revenue (affiliate only)
   
2. Your data has 'customer_region' and 'shipping_region'. 
   Which region should I use?
   
3. Q3 of which year? I see data from 2024-2025."

[User selects options or provides answers]

System: "Thanks! Proceeding with: net_revenue by customer_region for Q3 2025."
```

---

### FR-3: Hierarchical Planning with Approval
**Priority**: P0 (Must Have)

**Description**: System generates step-by-step execution plan and waits for user approval before starting.

**Acceptance Criteria**:
1. Planning Agent decomposes query into hierarchical tasks:
   - Level 1: Main objective
   - Level 2: Sub-tasks with dependencies
   - Level 3: Atomic operations (SQL query, Python analysis, visualization)
2. Plan displayed in UI with:
   - Task descriptions in plain language
   - Estimated execution time per task
   - Dependencies visualized (Task B depends on Task A result)
3. User can:
   - Approve entire plan ("Execute All")
   - Modify plan (remove/reorder tasks)
   - Request explanation of specific tasks
4. System executes only after explicit approval
5. Plan and approval logged to audit trail

**Plan Structure Example**:
```json
{
  "query": "Analyze sales trends and predict next quarter",
  "plan": {
    "main_objective": "Generate sales forecast with trend analysis",
    "tasks": [
      {
        "id": "task_1",
        "description": "Extract historical sales data (last 12 months)",
        "type": "sql_query",
        "estimated_time": "2s",
        "dependencies": []
      },
      {
        "id": "task_2", 
        "description": "Calculate monthly growth rates and seasonality factors",
        "type": "python_analysis",
        "estimated_time": "5s",
        "dependencies": ["task_1"]
      },
      {
        "id": "task_3",
        "description": "Generate trend visualization with prediction intervals",
        "type": "visualization",
        "estimated_time": "3s",
        "dependencies": ["task_2"]
      },
      {
        "id": "task_4",
        "description": "Produce natural language summary of findings",
        "type": "synthesis",
        "estimated_time": "4s",
        "dependencies": ["task_2", "task_3"]
      }
    ]
  }
}
```

---

### FR-4: Progress Tracking & Execution
**Priority**: P0 (Must Have)

**Description**: Once approved, system executes plan with real-time progress updates.

**Acceptance Criteria**:
1. Progress bar shows overall completion (e.g., "Step 2 of 4: 50%")
2. Each task shows status: Pending → Running → Complete/Failed
3. Intermediate results displayed as they complete:
   - SQL queries show row count returned
   - Python analysis shows output preview
4. If task fails:
   - Error displayed with explanation
   - User can retry, skip, or abort entire plan
5. All execution details logged (queries, code, results, timing)

**UI Display**:
```
Plan Execution: Analyzing Sales Trends
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 50% (2/4 tasks)

✓ Task 1: Extract historical sales    [2.1s] [1,247 rows]
✓ Task 2: Calculate growth rates      [4.8s] [Complete]
⚙ Task 3: Generate visualization      [Running...]
⏸ Task 4: Produce summary             [Pending]

[View Task 2 Output] [Abort Execution]
```

---

### FR-5: Sandboxed Python Execution
**Priority**: P1 (Should Have)

**Description**: Secure, isolated Python code execution for custom analyses.

**Acceptance Criteria**:
1. Python code runs in Docker container OR Firejail sandbox
2. No network access (air-gapped execution)
3. Whitelisted packages only: pandas, numpy, scipy, scikit-learn, plotly, matplotlib
4. Resource limits enforced:
   - 512MB RAM maximum
   - 30 second timeout
   - No file system writes outside /tmp
5. Code validation before execution:
   - Reject dangerous operations: `eval()`, `exec()`, `__import__`
   - Reject network libraries: requests, urllib, socket
6. Execution results include:
   - stdout/stderr
   - Generated artifacts (plots, dataframes)
   - Execution time and memory usage

**Sandbox Implementation Options**:
```python
# Option 1: Docker-based (recommended)
import docker

class DockerSandbox:
    def __init__(self):
        self.client = docker.from_env()
        self.image = "python:3.11-slim"
        self.allowed_packages = ["pandas", "numpy", "scipy", "plotly"]
    
    def execute(self, code: str, data: dict) -> dict:
        container = self.client.containers.run(
            self.image,
            command=["python", "-c", code],
            detach=True,
            network_disabled=True,
            mem_limit="512m",
            cpu_quota=50000,  # 50% CPU
            volumes={
                "/tmp/data": {"bind": "/data", "mode": "ro"}
            }
        )
        
        container.wait(timeout=30)
        logs = container.logs()
        container.remove()
        
        return {"output": logs.decode(), "artifacts": []}

# Option 2: Firejail-based (lighter weight)
import subprocess

class FirejailSandbox:
    def execute(self, code: str) -> dict:
        result = subprocess.run([
            "firejail",
            "--quiet",
            "--private",
            "--net=none",
            "--rlimit-as=512M",
            "python3", "-c", code
        ], capture_output=True, timeout=30, text=True)
        
        return {"output": result.stdout, "errors": result.stderr}
```

---

### FR-6: Interactive Visualizations
**Priority**: P1 (Should Have)

**Description**: Generate Plotly interactive charts with drill-down capabilities.

**Acceptance Criteria**:
1. Visualization Agent automatically selects chart type based on data:
   - Time series → Line chart
   - Categorical comparison → Bar chart
   - Correlations → Scatter plot
   - Distributions → Histogram
2. All charts are Plotly-based with:
   - Zoom/pan controls
   - Hover tooltips showing values
   - Legend toggles
   - Export to PNG/HTML
3. Charts support drill-down (click to filter/expand)
4. User can request specific chart types
5. Charts responsive to window size

**Visualization Selection Logic**:
```python
def select_chart_type(data_profile: dict, query_intent: dict) -> str:
    """Intelligent chart type selection"""
    
    # Check for time dimension
    if any(col['type'] == 'datetime' for col in data_profile['columns'].values()):
        if query_intent.get('show_trend', False):
            return "line_chart"
    
    # Check number of dimensions
    dimensions = [col for col in data_profile['columns'].values() 
                 if col['type'] == 'categorical']
    measures = [col for col in data_profile['columns'].values()
               if col['type'] == 'numeric']
    
    if len(dimensions) == 1 and len(measures) == 1:
        return "bar_chart"
    
    if len(dimensions) == 0 and len(measures) == 2:
        return "scatter_plot"
    
    if len(dimensions) >= 2:
        return "heatmap"
    
    return "table"  # Fallback
```

---

### FR-7: Interaction Logging & Audit Trail
**Priority**: P0 (Must Have)

**Description**: Persistent storage of all user interactions, clarifications, and system decisions.

**Acceptance Criteria**:
1. All conversations stored with:
   - Timestamp
   - User query (original)
   - System interpretation (parsed intent)
   - Uncertainty score
   - Clarification questions asked (if any)
   - User responses
   - Execution plan
   - Results summary
2. Clarifications indexed for future reuse:
   - "User previously clarified 'sales' means 'net_revenue'"
3. Feedback captured:
   - Thumbs up/down on results
   - Comments on accuracy/helpfulness
4. Query performance metrics logged:
   - Execution time per task
   - Data volume processed
5. Export audit trail to CSV/JSON

**Database Schema**:
```sql
-- Conversations table
CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    user_query TEXT NOT NULL,
    parsed_intent JSONB,
    uncertainty_score FLOAT,
    plan JSONB,
    status VARCHAR(20) -- 'completed', 'failed', 'aborted'
);

-- Clarifications table
CREATE TABLE clarifications (
    clarification_id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(conversation_id),
    question_text TEXT NOT NULL,
    question_type VARCHAR(50), -- 'multiple_choice', 'open_ended'
    options JSONB, -- For multiple choice
    user_response TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Feedback table
CREATE TABLE feedback (
    feedback_id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(conversation_id),
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    was_accurate BOOLEAN,
    was_helpful BOOLEAN,
    comments TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Execution logs table
CREATE TABLE execution_logs (
    log_id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(conversation_id),
    task_id VARCHAR(50),
    task_type VARCHAR(50), -- 'sql', 'python', 'visualization'
    executed_code TEXT,
    execution_time_ms INTEGER,
    rows_returned INTEGER,
    status VARCHAR(20), -- 'success', 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### FR-8: Context Learning & Reuse
**Priority**: P2 (Nice to Have)

**Description**: System learns from user clarifications to improve future accuracy.

**Acceptance Criteria**:
1. When user clarifies ambiguous term, system:
   - Updates semantic layer configuration
   - Adds synonym to relevant metric/dimension
   - Stores user preference
2. Future queries using same term skip clarification:
   - "You previously told me 'sales' means 'net_revenue'"
3. User can view and edit learned context:
   - UI shows all stored clarifications
   - User can modify/delete incorrect learnings
4. Context export/import for sharing across instances

**Learning Implementation**:
```python
class ContextLearner:
    def __init__(self, semantic_config_path: str, clarifications_db):
        self.config = self._load_config(semantic_config_path)
        self.db = clarifications_db
    
    def learn_from_clarification(self, term: str, 
                                 canonical_field: str, 
                                 conversation_id: str):
        """Update semantic layer with user clarification"""
        
        # Find matching metric/dimension
        for metric in self.config['metrics']:
            if metric['name'] == canonical_field:
                if term.lower() not in [s.lower() for s in metric.get('synonyms', [])]:
                    metric.setdefault('synonyms', []).append(term)
                    self._save_config()
                    
                    # Log learning event
                    self.db.log_learning(
                        term=term,
                        mapped_to=canonical_field,
                        source_conversation=conversation_id,
                        confidence=1.0
                    )
                    break
    
    def check_previous_clarifications(self, term: str) -> Optional[str]:
        """Check if term was previously clarified"""
        past_clarifications = self.db.query(
            "SELECT canonical_field FROM clarifications WHERE term = %s",
            (term,)
        )
        
        if past_clarifications:
            return past_clarifications[0]['canonical_field']
        return None
```

---

## Data Flow Diagram (Textual Description)

### End-to-End User Journey

**Phase 1: Data & Context Ingestion**
1. User uploads CSV file → System creates PostgreSQL table `user_data_001`
2. User uploads context JSON → System parses business definitions
3. Context Validator compares data schema to context:
   - Identifies 3 unmapped columns out of 15 (80% coverage)
   - Generates questions: "What does 'rev_amt' mean?" "What is 'cust_seg'?"
4. User provides answers → System updates semantic layer config
5. Validator re-runs → 100% coverage achieved
6. Context embedded into ChromaDB for RAG retrieval

**Phase 2: Query Submission**
1. User enters natural language query: "Show top regions by revenue last quarter"
2. Query routed to Planning Agent (Azure OpenAI GPT-4)
3. Planning Agent:
   - Retrieves relevant context from ChromaDB (RAG)
   - Parses intent: `{metrics: ['revenue'], dimensions: ['region'], filters: ['Q4 2025']}`
   - Checks semantic layer for field mappings
   - Returns parsed intent with confidence score

**Phase 3: Uncertainty Evaluation**
1. Uncertainty Scorer receives parsed intent + data profile
2. Calculates scores:
   - Data completeness: 98% (low null rates)
   - Schema confidence: 75% ('revenue' matches 2 metrics: gross_revenue, net_revenue)
   - Query confidence: 90% (LLM self-assessment)
3. Overall score: 0.87 (weighted average)
4. **TRIGGER**: Score < 0.95 threshold → HITL activated

**Phase 4: Human-in-the-Loop Clarification**
1. HITL Controller generates question:
   - "Which revenue metric? (a) Gross Revenue (b) Net Revenue"
2. UI displays clarification prompt
3. User selects: "(b) Net Revenue"
4. Response logged to `clarifications` table
5. Semantic layer updated (if first occurrence)
6. Uncertainty re-evaluated: Now 0.98 (above threshold)

**Phase 5: Hierarchical Planning**
1. Planning Agent generates execution plan:
   ```
   Main Goal: Show top regions by net revenue for Q4 2025
   Task 1: Query PostgreSQL for region-level revenue sums (Q4 2025)
   Task 2: Sort by revenue descending, take top 10
   Task 3: Generate bar chart (Plotly)
   Task 4: Create summary: "Top region: West with $2.4M revenue"
   ```
2. Plan displayed in UI with task dependencies
3. System waits for approval

**Phase 6: User Approval**
1. User reviews plan
2. Clicks "Approve & Execute"
3. Approval logged to `conversations` table with timestamp

**Phase 7: Execution**
1. Task 1: SQL Generator Agent
   - Generates query using semantic layer mappings:
     ```sql
     SELECT customer_region, SUM(net_revenue_amt) as revenue
     FROM user_data_001
     WHERE order_date >= '2025-10-01' AND order_date < '2026-01-01'
     GROUP BY customer_region
     ORDER BY revenue DESC
     LIMIT 10
     ```
   - Executes against PostgreSQL
   - Returns 10 rows
   - Logs query + results to `execution_logs`
   - Updates UI: "Task 1 Complete ✓ (2.1s, 10 rows)"

2. Task 2: Python Analyst Agent (if needed for complex aggregation)
   - Generates pandas code
   - Submits to Docker sandbox for execution
   - Receives results + execution metadata
   - Updates UI: "Task 2 Complete ✓ (4.2s)"

3. Task 3: Visualization Agent
   - Receives data from Task 1
   - Selects chart type: horizontal bar chart
   - Generates Plotly figure with:
     ```python
     fig = px.bar(df, x='revenue', y='customer_region', 
                  orientation='h', title='Top Regions by Revenue')
     ```
   - Returns interactive HTML
   - Updates UI: "Task 3 Complete ✓ (1.8s)"

4. Task 4: Synthesis Agent
   - Analyzes results
   - Generates natural language summary:
     "The West region generated the highest revenue in Q4 2025 with $2.4M, 
      representing 32% of total revenue. East and North regions followed 
      with $1.8M and $1.6M respectively."
   - Updates UI: "Task 4 Complete ✓ (3.1s)"

**Phase 8: Results Presentation**
1. Streamlit displays:
   - Interactive table (AgGrid) with sortable columns
   - Plotly bar chart (zoomable, exportable)
   - Natural language summary
2. User can:
   - Drill down (click region to see customer details)
   - Export data (CSV, Excel)
   - Export chart (PNG, HTML)
   - Provide feedback (thumbs up/down)

**Phase 9: Feedback Loop**
1. User clicks thumbs up
2. Feedback stored with rating=5, was_accurate=True
3. Clarification ("revenue → net_revenue") marked as validated
4. Future queries about "revenue" will use net_revenue without asking

---

## Non-Functional Requirements

### NFR-1: Performance
| Metric | Target | Measurement |
|--------|--------|-------------|
| Query response (cached) | < 2s P95 | Application logs |
| Query response (uncached) | < 10s P95 | PostgreSQL execution time |
| UI responsiveness | < 100ms per interaction | Frontend metrics |
| Sandbox startup | < 2s | Container creation time |
| Context embedding | < 5s for 10 pages | ChromaDB insert latency |

### NFR-2: Scalability
- Support datasets up to 1M rows in PostgreSQL
- Handle 100 concurrent user sessions (future multi-user)
- ChromaDB vector store: up to 10,000 document chunks
- Conversation history: retain 1,000 conversations per user

### NFR-3: Reliability
- System availability: 99% uptime (local deployment)
- Graceful degradation: If LLM API unavailable, show cached results
- Auto-retry on transient errors (max 3 attempts)
- Backup/restore for PostgreSQL and SQLite databases

### NFR-4: Security
- Sandboxed code execution (no filesystem/network access)
- SQL injection prevention (parameterized queries only)
- Rate limiting on LLM API calls (max 100/hour)
- Local data storage (no external data transmission except LLM API)

### NFR-5: Usability
- Onboarding tutorial for new users
- Inline help tooltips for all UI elements
- Error messages in plain language (no technical jargon)
- Keyboard shortcuts for common actions
- Mobile-responsive UI (Streamlit's responsive layout)

### NFR-6: Cost Efficiency
- Total infrastructure cost: $0/month (local)
- LLM API cost target: < $150/month for moderate usage
  - GPT-4 for planning (~10 calls/query): ~$0.15/query
  - GPT-3.5 for validation (~5 calls/query): ~$0.02/query
  - Estimated 500 queries/month: ~$85/month
- Caching strategy to minimize redundant LLM calls

---

## Technical Stack Specification

### Core Technologies

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| **UI Framework** | Streamlit | 1.30+ | Rapid prototyping, built-in interactivity |
| **Backend Language** | Python | 3.11+ | Rich data science ecosystem |
| **Database** | PostgreSQL | 15+ | Robust SQL support, JSON columns |
| **Vector Store** | ChromaDB | 0.4+ | Lightweight, local-first, easy setup |
| **Embeddings** | HuggingFace | sentence-transformers/all-MiniLM-L6-v2 | Free, 384-dim, good quality |
| **LLM API** | Azure OpenAI | GPT-4-Turbo, GPT-3.5-Turbo | Enterprise reliability, fallback options |
| **Alternative LLM** | OpenRouter | Access to Claude, Llama | Backup if Azure unavailable |
| **Code Sandbox** | Docker | 24+ | Industry standard, good isolation |
| **Visualization** | Plotly | 5.18+ | Interactive, web-based, JSON export |
| **Data Tables** | Streamlit-AgGrid | 1.0+ | Interactive tables with sorting/filtering |
| **Orchestration** | Custom Python | - | State machine for agent coordination |

### Python Package Dependencies

```txt
# Core Framework
streamlit==1.30.0
streamlit-aggrid==1.0.5

# Data Processing
pandas==2.1.4
numpy==1.26.2
openpyxl==3.1.2  # Excel support

# Database
psycopg2-binary==2.9.9
sqlalchemy==2.0.25

# Vector Store & Embeddings
chromadb==0.4.22
sentence-transformers==2.3.1

# LLM Integration
openai==1.10.0  # Azure OpenAI SDK
anthropic==0.18.0  # Claude via OpenRouter
httpx==0.26.0

# Visualization
plotly==5.18.0
matplotlib==3.8.2

# Code Execution
docker==7.0.0

# Utilities
pydantic==2.5.3
python-dotenv==1.0.0
uuid==1.30
```

### Environment Configuration

```bash
# .env file structure
# LLM API Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_GPT4_DEPLOYMENT=gpt-4-turbo
AZURE_GPT35_DEPLOYMENT=gpt-35-turbo

# Fallback OpenRouter
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=anthropic/claude-3-sonnet

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=analytics_db
POSTGRES_USER=analyst
POSTGRES_PASSWORD=secure_password

# Application Settings
UNCERTAINTY_THRESHOLD=0.95
MAX_SANDBOX_TIMEOUT=30
MAX_UPLOAD_SIZE_MB=100
CACHE_ENABLED=true

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_db

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

---

## Phased Implementation Roadmap

### Phase 1: Foundation (Weeks 1-3)
**Goal**: Establish core infrastructure and basic query execution

**Deliverables**:
1. Project setup:
   - Repository initialization
   - Development environment (Docker Compose)
   - PostgreSQL database setup
   - Streamlit basic app skeleton

2. Data ingestion pipeline:
   - CSV/Excel file upload
   - Automatic table creation in PostgreSQL
   - Basic schema detection

3. Semantic layer configuration:
   - JSON schema definition
   - Config loader/parser
   - Basic metric/dimension mapping

4. Simple query execution:
   - Text-to-SQL using LLM (Azure OpenAI)
   - SQL execution against PostgreSQL
   - Results display in Streamlit table

**Success Criteria**:
- User can upload CSV and query data with natural language
- System generates and executes correct SQL for simple queries
- Results displayed accurately

**Estimated Effort**: 60 hours (2 engineers × 30 hours)

---

### Phase 2: Context Validation & RAG (Weeks 4-5)
**Goal**: Implement context ingestion, validation, and retrieval

**Deliverables**:
1. Context upload system:
   - TXT/JSON file parser
   - Business context extractor
   - ChromaDB integration

2. Context Validator:
   - Schema-to-context mapping algorithm
   - Completeness scoring
   - Gap identification
   - Question generation for missing context

3. RAG system:
   - HuggingFace embeddings setup
   - Document chunking and embedding
   - Semantic search for context retrieval
   - Context injection into LLM prompts

**Success Criteria**:
- System identifies unmapped columns with >90% accuracy
- Generated context questions are relevant and actionable
- RAG retrieves correct context for queries

**Estimated Effort**: 40 hours

---

### Phase 3: Uncertainty Scoring & HITL (Weeks 6-7)
**Goal**: Implement confidence evaluation and clarification mechanism

**Deliverables**:
1. Uncertainty Scorer:
   - Multi-factor scoring algorithm
   - Data completeness checker
   - Schema alignment validator
   - Query confidence extractor

2. HITL Controller:
   - Clarification question generator
   - Multiple choice UI component
   - User response parser
   - Context enrichment loop

3. Interaction database:
   - SQLite schema for conversations/clarifications
   - CRUD operations
   - Query history UI

**Success Criteria**:
- Uncertainty score correlates with actual errors (validated on test set)
- Clarification questions are clear and unambiguous
- System improves accuracy after clarification

**Estimated Effort**: 50 hours

---

### Phase 4: Hierarchical Planning & Approval (Weeks 8-9)
**Goal**: Implement transparent task decomposition and user approval

**Deliverables**:
1. Planning Agent:
   - Task decomposition using LLM
   - Dependency graph construction
   - Hierarchical plan formatting

2. Plan Approval UI:
   - Interactive task list display
   - Dependency visualization
   - Approve/reject/modify controls

3. Execution engine:
   - Sequential task executor
   - Progress tracking
   - Real-time status updates
   - Error handling and retry logic

**Success Criteria**:
- Plans are logically coherent and executable
- User can understand and validate plans before execution
- Execution follows plan exactly

**Estimated Effort**: 45 hours

---

### Phase 5: Sandboxed Python Execution (Weeks 10-11)
**Goal**: Enable safe, isolated Python code execution

**Deliverables**:
1. Docker sandbox:
   - Python 3.11 base image with data science packages
   - Network isolation configuration
   - Resource limits (memory, CPU, timeout)
   - Volume mounting for data transfer

2. Python Analyst Agent:
   - Code generation using LLM
   - Code validation (AST parsing for dangerous operations)
   - Sandbox execution wrapper
   - Result extraction and parsing

3. Artifact handling:
   - Plotly figure serialization
   - DataFrame to JSON conversion
   - File artifact retrieval

**Success Criteria**:
- Malicious code blocked before execution
- Sandbox escapes prevented (security audit)
- Generated visualizations render correctly

**Estimated Effort**: 40 hours

---

### Phase 6: Visualization & Polish (Week 12)
**Goal**: Production-ready UI and comprehensive testing

**Deliverables**:
1. Visualization Agent:
   - Chart type selection logic
   - Plotly figure generation
   - Interactive features (drill-down, export)

2. UI enhancements:
   - Responsive layout
   - Loading indicators
   - Error messages
   - Help documentation

3. Testing & QA:
   - Unit tests for core components (>80% coverage)
   - Integration tests for end-to-end flows
   - Performance benchmarking
   - Security audit

4. Documentation:
   - User guide
   - Admin setup guide
   - API documentation
   - Architecture diagrams

**Success Criteria**:
- All functional requirements met
- Test coverage >80%
- Performance meets NFR targets
- Documentation complete

**Estimated Effort**: 45 hours

---

### Post-Launch: Iteration & Enhancement

**Phase 7 (Optional - Weeks 13-16)**:
1. Context Learning (FR-8):
   - Automatic synonym extraction from clarifications
   - User-editable context management UI
   - Context export/import

2. Advanced Analytics:
   - Statistical testing (t-tests, ANOVA)
   - Time series forecasting
   - Anomaly detection

3. Multi-user support:
   - User authentication
   - Per-user data isolation
   - Shared context libraries

4. Performance optimization:
   - Query result caching
   - Pre-aggregated views
   - Async processing for long-running queries

---

## Risk Management

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| LLM API costs exceed budget | Medium | High | Implement aggressive caching, use GPT-3.5 for non-critical tasks, set hard spending limits |
| Docker sandbox escapes | Low | Critical | Regular security audits, use minimal base images, disable all unnecessary capabilities |
| PostgreSQL performance degradation on large datasets | Medium | Medium | Implement query optimization, add indexes, consider partitioning |
| Uncertainty Scorer has high false positive rate | Medium | Medium | Collect feedback data, tune thresholds per use case, A/B test scoring algorithms |
| Context Validator misses critical gaps | Medium | High | Manual review of validation results, collect user reports, improve gap detection rules |

### Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Users bypass planning approval | Low | Medium | Make approval mandatory, log bypass attempts, user education |
| Insufficient user-provided context | High | High | Provide context templates, examples, guided wizards |
| Users don't understand clarification questions | Medium | Medium | Simplify language, provide examples, add "I don't know" option |

---

## Success Metrics & KPIs

### Primary Metrics (Measured Monthly)

1. **Query Accuracy**:
   - Target: >90%
   - Measurement: User feedback (thumbs up/down) on 100-query sample
   - Baseline: 65% (no semantic layer)

2. **Clarification Precision**:
   - Target: <15% false positives
   - Measurement: Ratio of "unnecessary" flags on clarifications
   - Baseline: 30% (aggressive triggering)

3. **User Satisfaction**:
   - Target: >4.2/5.0
   - Measurement: Post-interaction survey
   - Baseline: New system (no baseline)

4. **Time to Insight**:
   - Target: <5 minutes from upload to first meaningful result
   - Measurement: Median time in audit logs
   - Baseline: 15 minutes (manual SQL)

### Secondary Metrics

- **Context Completeness**: Average score after validation (target: >95%)
- **Plan Approval Rate**: % of plans approved without modification (target: >80%)
- **Sandbox Security**: Zero escapes or security incidents (mandatory)
- **API Cost Efficiency**: Cost per query (target: <$0.20)

---

## Appendix A: Sample Semantic Layer Configuration

```json
{
  "version": "1.0",
  "last_updated": "2026-01-27",
  "metrics": [
    {
      "name": "total_revenue",
      "display_name": "Total Revenue",
      "description": "Sum of all order amounts after discounts and returns",
      "sql": "SUM(net_order_amount)",
      "aggregation": "sum",
      "format": "currency_usd",
      "synonyms": ["sales", "income", "revenue", "gross sales"],
      "sample_queries": [
        "What was our revenue last quarter?",
        "Show me sales by region"
      ]
    },
    {
      "name": "order_count",
      "display_name": "Total Orders",
      "description": "Count of distinct orders",
      "sql": "COUNT(DISTINCT order_id)",
      "aggregation": "count",
      "format": "number",
      "synonyms": ["number of orders", "order volume"]
    },
    {
      "name": "average_order_value",
      "display_name": "Average Order Value",
      "description": "Average revenue per order",
      "sql": "SUM(net_order_amount) / COUNT(DISTINCT order_id)",
      "aggregation": "calculated",
      "format": "currency_usd",
      "depends_on": ["total_revenue", "order_count"],
      "synonyms": ["AOV", "avg order size"]
    }
  ],
  "dimensions": [
    {
      "name": "customer_region",
      "display_name": "Customer Region",
      "column": "region",
      "type": "categorical",
      "description": "Geographic region of customer billing address",
      "sample_values": ["North America", "Europe", "Asia Pacific", "Latin America"],
      "synonyms": ["region", "geo", "geography"]
    },
    {
      "name": "order_date",
      "display_name": "Order Date",
      "column": "order_timestamp",
      "type": "datetime",
      "description": "Date when order was placed",
      "granularities": ["day", "week", "month", "quarter", "year"]
    },
    {
      "name": "product_category",
      "display_name": "Product Category",
      "column": "category",
      "type": "categorical",
      "description": "Top-level product category",
      "sample_values": ["Electronics", "Apparel", "Home & Garden"],
      "hierarchies": ["category", "subcategory", "product_name"]
    }
  ],
  "relationships": [
    {
      "from_table": "orders",
      "to_table": "customers",
      "join_type": "left",
      "on": "customer_id",
      "description": "Link orders to customer details"
    },
    {
      "from_table": "orders",
      "to_table": "products",
      "join_type": "left",
      "on": "product_id"
    }
  ],
  "business_rules": [
    {
      "name": "exclude_test_orders",
      "applies_to": "all_metrics",
      "filter": "is_test_order = FALSE",
      "description": "Exclude internal test orders from all analyses"
    },
    {
      "name": "revenue_recognition",
      "applies_to": ["total_revenue"],
      "filter": "order_status IN ('completed', 'shipped')",
      "description": "Only count revenue from fulfilled orders"
    }
  ]
}
```

---

## Appendix B: Example Uncertainty Calculation

**User Query**: "Show me sales by region for last quarter"

**Step 1: Parse Intent**
```json
{
  "requested_metrics": ["sales"],
  "requested_dimensions": ["region"],
  "temporal_filter": {
    "period": "last quarter",
    "relative": true
  },
  "llm_confidence": 0.88
}
```

**Step 2: Data Completeness Check**
```python
# Check null rates for required columns
data_profile = {
  "net_order_amount": {"null_rate": 0.02, "coverage": 0.98},
  "region": {"null_rate": 0.08, "coverage": 0.92},
  "order_timestamp": {"null_rate": 0.00, "coverage": 1.00}
}

# Check temporal coverage
current_date = "2026-01-27"
last_quarter_start = "2025-10-01"
latest_data_date = "2026-01-20"

temporal_coverage = 0.99  # Data exists for 99% of target period

data_completeness_score = (0.98 + 0.92 + 1.00 + 0.99) / 4 = 0.97
```

**Step 3: Schema Confidence Check**
```python
# Map "sales" to available metrics
semantic_layer_metrics = ["total_revenue", "net_revenue", "gross_revenue"]

# "sales" matches multiple metrics (ambiguous)
matching_metrics = []
for metric in semantic_layer_metrics:
    if "sales" in metric['synonyms']:
        matching_metrics.append(metric['name'])

# Result: ["total_revenue", "net_revenue"] both match

if len(matching_metrics) > 1:
    schema_confidence_score = 0.60  # Penalize ambiguity
elif len(matching_metrics) == 1:
    schema_confidence_score = 1.00
else:
    schema_confidence_score = 0.30  # No match

# Map "region" to dimensions
"region" in ["customer_region", "shipping_region"]
# Ambiguous again

region_confidence = 0.60

schema_confidence_score = (0.60 + 0.60) / 2 = 0.60
```

**Step 4: Query Confidence**
```python
query_confidence = 0.88  # From LLM self-assessment
```

**Step 5: Calculate Overall Uncertainty**
```python
weights = {"data": 0.35, "schema": 0.35, "query": 0.30}

overall_score = (
    0.35 * 0.97 +  # data completeness
    0.35 * 0.60 +  # schema confidence
    0.30 * 0.88    # query confidence
) = 0.3395 + 0.2100 + 0.2640 = 0.8135
```

**Step 6: Trigger Decision**
```python
if overall_score < 0.95:
    trigger_clarification = True
    
    # Generate questions for low-scoring dimensions
    questions = []
    
    if schema_confidence_score < 0.95:
        questions.append({
            "type": "multiple_choice",
            "text": "Which 'sales' metric should I use?",
            "options": [
                {"value": "total_revenue", "label": "Total Revenue (all orders)"},
                {"value": "net_revenue", "label": "Net Revenue (after returns)"}
            ]
        })
        
        questions.append({
            "type": "multiple_choice", 
            "text": "Which region dimension?",
            "options": [
                {"value": "customer_region", "label": "Customer billing region"},
                {"value": "shipping_region", "label": "Shipping destination region"}
            ]
        })
    
    return ClarificationRequired(
        uncertainty_score=0.81,
        questions=questions
    )
```

**Step 7: User Responds**
```json
{
  "sales_metric": "net_revenue",
  "region_dimension": "customer_region"
}
```

**Step 8: Re-calculate with Clarifications**
```python
# Schema confidence now 1.0 (unambiguous)
schema_confidence_score = 1.00

# Recalculate
overall_score = 0.35*0.97 + 0.35*1.00 + 0.30*0.88 = 0.9535

if overall_score >= 0.95:
    proceed_with_execution = True
```

---

## Appendix C: Docker Sandbox Configuration

**Dockerfile for Python Sandbox**:
```dockerfile
FROM python:3.11-slim

# Install only whitelisted packages
RUN pip install --no-cache-dir \
    pandas==2.1.4 \
    numpy==1.26.2 \
    scipy==1.11.4 \
    scikit-learn==1.3.2 \
    plotly==5.18.0 \
    matplotlib==3.8.2 \
    seaborn==0.13.0

# Create non-root user
RUN useradd -m -u 1000 sandbox_user

# Set working directory
WORKDIR /workspace

# Switch to non-root user
USER sandbox_user

# Default command
CMD ["python3"]
```

**Docker Compose Configuration**:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: analytics_db
      POSTGRES_USER: analyst
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - analytics_network

  python_sandbox:
    build: ./sandbox
    image: analytics-sandbox:latest
    # Resource limits
    mem_limit: 512m
    cpus: 0.5
    # No network access
    network_mode: none
    # Read-only root filesystem
    read_only: true
    # Temporary filesystem for /tmp
    tmpfs:
      - /tmp:size=100M
    # Security options
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL

volumes:
  postgres_data:

networks:
  analytics_network:
    driver: bridge
```

**Sandbox Execution Wrapper**:
```python
import docker
import json
from typing import Dict, Any

class SecureSandbox:
    def __init__(self):
        self.client = docker.from_env()
        self.image = "analytics-sandbox:latest"
    
    def execute_code(self, code: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Python code in isolated container
        
        Args:
            code: Python code string
            input_data: Dict to be available as 'data' variable
        
        Returns:
            Dict with stdout, stderr, and any generated artifacts
        """
        
        # Prepare execution script
        exec_script = f"""
import json
import sys

# Load input data
with open('/tmp/input.json', 'r') as f:
    data = json.load(f)

# Execute user code
try:
{self._indent_code(code, 4)}
    
    # Capture any variables for output
    output = {{}}
    if 'result' in locals():
        output['result'] = result
    if 'fig' in locals():
        output['figure'] = fig.to_json()
    
    with open('/tmp/output.json', 'w') as f:
        json.dump(output, f)
        
except Exception as e:
    print(f"ERROR: {{str(e)}}", file=sys.stderr)
    sys.exit(1)
"""
        
        try:
            # Create container
            container = self.client.containers.create(
                self.image,
                command=["python3", "-c", exec_script],
                detach=True,
                network_disabled=True,
                mem_limit="512m",
                nano_cpus=500_000_000,  # 0.5 CPU
                tmpfs={'/tmp': 'size=100M'},
                security_opt=['no-new-privileges:true']
            )
            
            # Write input data to container
            input_json = json.dumps(input_data).encode()
            container.put_archive('/tmp', self._create_tar({'input.json': input_json}))
            
            # Start and wait
            container.start()
            result = container.wait(timeout=30)
            
            # Retrieve outputs
            stdout = container.logs(stdout=True, stderr=False).decode()
            stderr = container.logs(stdout=False, stderr=True).decode()
            
            # Get output file if exists
            output_data = {}
            try:
                bits, stat = container.get_archive('/tmp/output.json')
                output_tar = b''.join(bits)
                output_data = self._extract_from_tar(output_tar, 'output.json')
            except:
                pass
            
            # Cleanup
            container.remove(force=True)
            
            return {
                "success": result['StatusCode'] == 0,
                "stdout": stdout,
                "stderr": stderr,
                "output": output_data
            }
            
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "output": {}
            }
    
    @staticmethod
    def _indent_code(code: str, spaces: int) -> str:
        """Indent code block"""
        indent = ' ' * spaces
        return '\n'.join(indent + line for line in code.split('\n'))
```

---

**End of Document**

This PRD provides a comprehensive specification for building a production-grade agentic data analyst with local-first architecture, semantic context understanding, and human-in-the-loop validation. All requirements are traceable to the research findings on 2026's leading analytics platforms while adapting to cost-effective, local deployment constraints.
