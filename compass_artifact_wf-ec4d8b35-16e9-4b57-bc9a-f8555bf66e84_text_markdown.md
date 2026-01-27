# Agentic No-Code Data Analysts: The 2026 Technical Deep Dive

**AI-powered analytics tools have fundamentally shifted from query generators to genuine "data consultants"**—systems that understand business context, detect ambiguity, and collaborate with humans before committing to answers. Research shows semantic-grounded AI achieves **99.8% accuracy** versus ~20% for raw text-to-SQL approaches, while proactive clarification features boost accuracy from **42.5% to 92.5%** on ambiguous queries. This report examines how leading platforms implement semantic context ingestion and human-in-the-loop feedback, then blueprints a "better than industry" technical architecture.

The transformation is structural, not incremental. Tools like Snowflake Cortex Analyst now return *suggestions instead of SQL* when detecting ambiguity—a mutually exclusive behavior that prevents hallucinated answers. ThoughtSpot's Spotter shows interpreted search tokens above every visualization, enabling instant correction. Omni's AI assistant outlines its task list before execution, creating debuggable transparency. This "consultant pattern" represents the maturation of agentic analytics from demo-ready to production-grade.

---

## How leading tools ingest business context

The semantic layer has become non-negotiable infrastructure for AI accuracy. Gartner predicts **60% of AI projects unsupported by AI-ready data will be abandoned by 2026**, and every major platform now treats semantic modeling as the foundation for natural language querying.

**Omni Analytics** implements a three-layer modeling approach (Schema → Relationships → Topics) with explicit AI context fields. Administrators can encode business logic directly: *"When someone asks about sales, revenue, how much we've sold, etc., they're asking about total revenue."* The platform's Field Values Tool enables automatic resolution of value mismatches—filtering "New York" when the database expects "NYC." Synthesia reports: *"When you constrain AI and give it context, like Omni's semantic layer does, you get predictable, reliable results that drive action."*

**Snowflake Intelligence** introduced Semantic Views as first-class database objects in November 2025, storing business concepts (Logical Tables, Facts, Metrics, Dimensions, Relationships) directly in the database. Their AI-Assisted Generator automatically creates synonyms, sample values, and AI-generated column descriptions. Cortex Analyst then queries these semantic views to generate SQL, achieving **95% accuracy** on verified query repositories according to Q2 FY2026 earnings disclosures.

**Tableau Semantics** (GA 2025) now offers natural language model creation—"create semantic data models in seconds using natural language"—with AI-powered relationship suggestions and agent enrichment capabilities that learn from real-time Q&A interactions. The Data Pro agent automates relationship mapping across tables.

**ThoughtSpot's SpotterModel** takes a generative approach, proposing tables, joins, and logic based on natural-language instructions. The platform documents specific schema requirements: fewer than **50 columns**, user-friendly names rather than abbreviations, and avoiding identical strings in multiple columns. With proper setup, customers report **95% accuracy** versus GPT alone.

| Tool | Context Ingestion Method | Accuracy Claims |
|------|-------------------------|-----------------|
| Omni | `ai_context` field, synonyms, sample queries | "Trusted" with semantic grounding |
| Snowflake | Semantic Views, AI-generated descriptions | 95% on verified repositories |
| Tableau | Agent enrichment, natural language modeling | Not disclosed |
| ThoughtSpot | SpotterModel, column descriptions, feedback loops | 80-95% depending on complexity |

The **Open Semantic Interchange (OSI)** initiative, launched September 2025 by Snowflake, ThoughtSpot, and Omni, establishes vendor-neutral semantic model standards—critical for portability across the fragmented tool landscape.

---

## The consultant feature: When AI asks instead of guesses

The most sophisticated platforms have implemented what researchers call the "halt-and-suggest pattern"—AI that stops execution and requests clarification when facing ambiguity rather than proceeding with assumptions.

**Snowflake Cortex Analyst** returns a `suggestion` content type *instead of* a `sql` content type when queries are ambiguous. This is mutually exclusive behavior: if the response contains suggestions, it will not contain SQL. The API response includes alternative interpretations the user can select:

```json
{
  "type": "suggestions",
  "suggestions": [
    "which company had the most revenue?",
    "which company placed the most orders?"
  ]
}
```

Streaming status events provide real-time visibility: `interpreting_question` → `generating_suggestions` (when ambiguity detected) → `generating_sql` (when proceeding). The platform's promise: *"The multi-agent setup will not query data under ambiguous assumptions."*

**ThoughtSpot Sage** takes a transparency-first approach, displaying **search tokens (interpreted query phrases)** above every visualization. Users see exactly which measures, attributes, and filters the AI selected, with explicit warnings: *"AI-generated Answers are occasionally inaccurate due to their probabilistic nature. Please verify results by checking the search tokens above the chart."* Upvoting teaches the system to return the same answer; downvoting flags queries for analyst review.

**Omni's coordinator mechanism** outlines its task list before execution, checking off steps as they complete. The result is "a more transparent, trustworthy, and debuggable process" where users can observe reasoning at each phase. The agent explicitly inspects results to verify correctness and tries alternative approaches when initial queries fail.

Research from **AmbiSQL** shows this pattern dramatically improves outcomes. When AI systems generate targeted multiple-choice clarification questions for ambiguous queries, accuracy jumps from **42.5% to 92.5%**. The taxonomy of ambiguity includes database-related issues (unclear schema references, mismatched values, missing keywords) and LLM-related issues (unclear knowledge sources, external knowledge requirements).

---

## The complete workflow: From ingestion to insight

The agentic analytics pipeline follows a consistent pattern across platforms, though implementations vary in sophistication:

**Stage 1: Ingestion & Schema Mapping**
Raw data sources connect to the semantic layer through connectors (Snowflake, BigQuery, Databricks). Schema information is extracted including table names, column types, sample values, and foreign key relationships. Administrators define business-level abstractions: metrics (aggregated measures), dimensions (categorical attributes), and entities (business objects like customers or orders).

**Stage 2: Context Enrichment**
Semantic models are enhanced with natural language descriptions, synonyms, and sample queries. Example from dbt semantic layer:
```yaml
measures:
  - name: total_revenue
    agg: sum
    expr: order_amount
    description: "Sum of transaction amounts after discounts"
    synonyms: ["sales", "income", "earnings"]
```

AI-assisted generators (Snowflake's Autopilot, ThoughtSpot's SpotterModel) can auto-generate initial context from column names and sample data, though human curation remains essential.

**Stage 3: Gap Identification & Confidence Scoring**
Before generating queries, agentic systems assess data completeness. Key factors include null rates, date coverage, schema match against expected columns, and semantic alignment between query terms and available fields. Systems like DataRobot implement explicit **Humble AI** rules that detect uncertain predictions, outlying inputs, and low-observation regions.

**Stage 4: User Inquiry (HITL Trigger)**
When confidence falls below thresholds (typically **85%** for financial or diagnostic queries), the system halts and presents clarification options. Presentation patterns include:
- Multiple-choice questions (Snowflake pattern)
- Token verification with edit capability (ThoughtSpot pattern)
- Task list visibility with reasoning explanation (Omni pattern)

**Stage 5: Query Generation & Execution**
With clarification complete, the semantic layer compiles requests into optimized SQL. Critically, the LLM generates *semantic requests* (metric + dimensions + filters), not raw SQL—the semantic layer handles provably-correct SQL generation. Cube benchmarks show pre-aggregated queries return in **20-50ms** versus **2-10 seconds** for warehouse-executed SQL.

**Stage 6: Result Validation & Synthesis**
Multi-agent systems employ self-reflection—generating SQL, then validating it before returning results. Validation checks include schema reference verification, temporal range validation, and consistency with historical patterns. Natural language explanations accompany results.

---

## Technical specifications and hard limitations

**Input Types Across Platforms:**
- **Structured data**: Universal support for SQL databases, data warehouses (Snowflake, BigQuery, Databricks, Redshift)
- **Semi-structured**: JSON, logs supported via warehouse parsers; CSV/Excel upload in preview (Databricks AI/BI)
- **Unstructured**: Document retrieval via Cortex Search (Snowflake), MCP integrations for Slack/Salesforce/Jira (ThoughtSpot Spotter 3)

**Output Formats:**
- SQL generation visible and read-only across all platforms
- Python code generation available in ThoughtSpot (Spotter 3), Omni
- Interactive visualizations with drill-down (all platforms)
- Dashboard embedding via APIs/SDKs
- Export to Slack, Teams, email for collaboration

**Critical Limitations:**

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Context window constraints** | Large schemas exceed token limits | Semantic layer abstraction reduces payload |
| **Multi-agent latency** | Tool selection search space grows exponentially | Intent classification routing, model tiering |
| **Hallucination rates** | Up to **46%** on complex multi-dimensional queries | Semantic grounding reduces by 66% |
| **Long conversation degradation** | Performance drops with frequent intent shifts | Conversation scoping, memory management |
| **Accuracy on real-world schemas** | SPIDER2 benchmark shows GPT-4o drops to **10.1%** accuracy | Verified query repositories, HITL validation |

**Cost Drivers:**
Token costs vary **10x** between LLMs. Snowflake bills per message processed (HTTP 200 only). Evaluation costs with LLM-as-judge run **$0.01-$0.10 per sample**. Gartner predicts **40%+ of agentic AI projects will be canceled before production by 2027** due to cost and complexity—semantic layer investment is the primary hedge.

---

## Semantic layer technologies as AI ground truth

The semantic layer has evolved from BI optimization tool to essential AI infrastructure. The 2025 GigaOm Radar classified semantic layers as a **mature category**, and research shows they reduce Gen AI data errors by **66%**.

**Cube.dev** (Leader and Outperformer in 2025 GigaOm Radar) provides a universal semantic layer with OLAP-style caching. The D3 Platform (June 2025) introduced AI Data Analyst and AI Data Engineer agents with native agentic capabilities. The Tesseract Engine handles advanced data modeling, while Cube Store (Rust-based) delivers **sub-50ms cached queries**.

**dbt Semantic Layer** (MetricFlow) takes a transformation-layer approach with version-controlled YAML definitions. MetricFlow was open-sourced under Apache 2.0 in late 2025. The dbt MCP Server exposes semantic models to AI agents, with "Ask dbt" achieving **3x accuracy improvement** versus raw data queries.

**AtScale** offers composable, modular models with their open-source Semantic Modeling Language (SML). Named Leader and Fast Mover in 2025 GigaOm, AtScale integrates with both Databricks Genie and Snowflake Cortex Analyst.

**Warehouse-native options** have emerged: Snowflake Semantic Views (GA August 2025) create semantic definitions as database objects with zero execution overhead; Databricks Unity Catalog Metric Views (GA late 2025) register YAML-defined metrics with native governance.

The critical insight: **AI agents need business context, not just data access**. By providing governed metrics, relationships, and business logic, semantic layers enable LLMs to reason over enterprise data with precision rather than probability.

---

# Builder's Blueprint: "Better Than Industry" Technical Architecture

## Design principles and system overview

This architecture prioritizes **semantic grounding**, **calibrated uncertainty**, and **safe execution**—the three pillars that differentiate production-grade agentic analytics from demo-ready prototypes. The system implements an Uncertainty Scorer that triggers human review when data completeness or query confidence falls below configurable thresholds (default: **95%**).

**Core Architecture Layers:**

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INTERFACE LAYER                         │
│   Conversational UI │ Clarification Prompts │ Result Explorer   │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐│
│  │ Planning │  │Uncertainty│  │ HITL    │  │ Memory Manager  ││
│  │  Agent   │  │  Scorer   │  │ Router  │  │ (Context/State) ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                   SPECIALIZED AGENTS                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────┐ │
│  │Semantic │  │  SQL    │  │ Python  │  │Validation│  │  RAG  │ │
│  │Query Gen│  │ Agent   │  │ Agent   │  │  Agent   │  │ Agent │ │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └───────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                   SEMANTIC LAYER (Ground Truth)                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Cube.dev / dbt Semantic Layer / Custom           │  │
│  │   Metrics │ Dimensions │ Relationships │ Business Logic  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                   EXECUTION ENVIRONMENT                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ E2B Python Sandbox│  │  SQL Warehouse   │  │ Vector Store │ │
│  │ (Firecracker VM) │  │ (Snowflake/BQ)   │  │  (Pinecone)  │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Semantic layer implementation with Cube

The semantic layer serves as the single source of truth for all metrics, eliminating "which number is right?" disputes and providing the governed context AI agents require.

**Recommended Stack: Cube.dev**
- Universal connectivity to Snowflake, BigQuery, Postgres, Databricks
- Pre-aggregation engine for sub-50ms query performance
- Dedicated AI API endpoint for agent consumption
- MCP Server support for standard agent connectivity

**Schema Definition Example:**

```javascript
// cube/schema/Orders.js
cube('Orders', {
  sql: `SELECT * FROM ${CUBE}.fct_orders`,
  
  measures: {
    totalRevenue: {
      type: 'sum',
      sql: 'order_amount',
      description: 'Sum of all order amounts after discounts',
      meta: {
        ai_context: 'When users ask about revenue, sales, or income, use this metric',
        synonyms: ['sales', 'income', 'earnings', 'GMV']
      }
    },
    
    avgOrderValue: {
      type: 'number',
      sql: `${totalRevenue} / ${orderCount}`,
      description: 'Average revenue per order'
    }
  },
  
  dimensions: {
    orderDate: {
      type: 'time',
      sql: 'order_date',
      description: 'Date when order was placed'
    },
    
    customerRegion: {
      type: 'string',
      sql: 'customer_region',
      meta: {
        sample_values: ['North America', 'EMEA', 'APAC', 'LATAM']
      }
    }
  },
  
  preAggregations: {
    dailyByRegion: {
      measures: [totalRevenue, orderCount],
      dimensions: [customerRegion],
      timeDimension: orderDate,
      granularity: 'day',
      refreshKey: { every: '1 hour' }
    }
  }
});
```

**AI API Integration:**

```python
# Service connecting orchestrator to Cube semantic layer
import httpx

class SemanticLayerClient:
    def __init__(self, cube_url: str, api_token: str):
        self.cube_url = cube_url
        self.headers = {"Authorization": f"Bearer {api_token}"}
    
    async def get_schema(self) -> dict:
        """Retrieve full semantic schema for agent context"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.cube_url}/cubejs-api/v1/meta",
                headers=self.headers
            )
            return response.json()
    
    async def execute_query(self, measures: list, dimensions: list, 
                           filters: list = None, time_range: dict = None) -> dict:
        """Execute semantic query (NOT raw SQL)"""
        query = {
            "measures": measures,
            "dimensions": dimensions,
            "filters": filters or [],
            "timeDimensions": [{
                "dimension": time_range.get("dimension"),
                "dateRange": time_range.get("range")
            }] if time_range else []
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.cube_url}/cubejs-api/v1/load",
                headers=self.headers,
                json={"query": query}
            )
            return response.json()
```

---

## Uncertainty Scorer implementation

The Uncertainty Scorer evaluates multiple signals to determine whether to proceed autonomously or trigger human review. The system maintains calibrated confidence that correlates with actual accuracy.

**Scoring Components:**

```python
from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass
class UncertaintyAssessment:
    overall_score: float  # 0-1, higher = more confident
    data_completeness: float
    schema_confidence: float
    query_confidence: float
    should_clarify: bool
    clarification_questions: list[str]
    risk_factors: list[str]

class UncertaintyScorer:
    def __init__(self, 
                 clarification_threshold: float = 0.95,
                 warning_threshold: float = 0.80):
        self.clarification_threshold = clarification_threshold
        self.warning_threshold = warning_threshold
    
    async def assess(self, 
                     user_query: str,
                     parsed_intent: dict,
                     semantic_schema: dict,
                     data_profile: dict) -> UncertaintyAssessment:
        
        # 1. Data Completeness Score
        data_completeness = self._score_data_completeness(
            parsed_intent, data_profile
        )
        
        # 2. Schema Confidence Score
        schema_confidence = self._score_schema_alignment(
            parsed_intent, semantic_schema
        )
        
        # 3. Query Interpretation Confidence
        query_confidence = await self._score_query_interpretation(
            user_query, parsed_intent
        )
        
        # Weighted combination
        weights = {
            'data': 0.35,
            'schema': 0.35, 
            'query': 0.30
        }
        
        overall_score = (
            weights['data'] * data_completeness +
            weights['schema'] * schema_confidence +
            weights['query'] * query_confidence
        )
        
        # Generate clarification questions if needed
        clarification_questions = []
        risk_factors = []
        
        if data_completeness < self.clarification_threshold:
            clarification_questions.extend(
                self._generate_data_clarifications(data_profile)
            )
            risk_factors.append(f"Data completeness: {data_completeness:.1%}")
        
        if schema_confidence < self.clarification_threshold:
            clarification_questions.extend(
                self._generate_schema_clarifications(parsed_intent, semantic_schema)
            )
            risk_factors.append(f"Ambiguous field references detected")
        
        should_clarify = overall_score < self.clarification_threshold
        
        return UncertaintyAssessment(
            overall_score=overall_score,
            data_completeness=data_completeness,
            schema_confidence=schema_confidence,
            query_confidence=query_confidence,
            should_clarify=should_clarify,
            clarification_questions=clarification_questions,
            risk_factors=risk_factors
        )
    
    def _score_data_completeness(self, intent: dict, profile: dict) -> float:
        """Assess whether required data exists and is complete"""
        required_fields = intent.get('required_fields', [])
        
        scores = []
        for field in required_fields:
            field_profile = profile.get(field, {})
            
            # Null rate penalty
            null_rate = field_profile.get('null_rate', 0)
            null_score = 1 - null_rate
            
            # Date coverage (if temporal)
            if field_profile.get('is_temporal'):
                expected_range = intent.get('date_range', {})
                actual_coverage = field_profile.get('date_coverage', 1.0)
                temporal_score = actual_coverage
                scores.append((null_score + temporal_score) / 2)
            else:
                scores.append(null_score)
        
        return np.mean(scores) if scores else 1.0
    
    def _score_schema_alignment(self, intent: dict, schema: dict) -> float:
        """Check if requested fields map unambiguously to schema"""
        requested_metrics = intent.get('metrics', [])
        requested_dimensions = intent.get('dimensions', [])
        
        available_metrics = {m['name']: m for cube in schema.get('cubes', []) 
                           for m in cube.get('measures', [])}
        available_dimensions = {d['name']: d for cube in schema.get('cubes', [])
                               for d in cube.get('dimensions', [])}
        
        metric_scores = []
        for metric in requested_metrics:
            if metric in available_metrics:
                metric_scores.append(1.0)
            else:
                # Check synonyms
                matched = any(
                    metric.lower() in (m.get('meta', {}).get('synonyms', []))
                    for m in available_metrics.values()
                )
                metric_scores.append(0.8 if matched else 0.3)
        
        dimension_scores = []
        for dim in requested_dimensions:
            if dim in available_dimensions:
                dimension_scores.append(1.0)
            else:
                # Check for partial matches (ambiguity)
                partial_matches = [d for d in available_dimensions 
                                  if dim.lower() in d.lower()]
                if len(partial_matches) == 1:
                    dimension_scores.append(0.9)
                elif len(partial_matches) > 1:
                    dimension_scores.append(0.5)  # Ambiguous
                else:
                    dimension_scores.append(0.2)
        
        all_scores = metric_scores + dimension_scores
        return np.mean(all_scores) if all_scores else 1.0
    
    async def _score_query_interpretation(self, query: str, intent: dict) -> float:
        """Use sampling-based confidence for query interpretation"""
        # Generate multiple interpretations and measure consistency
        # (Simplified - production would use actual LLM sampling)
        interpretation_confidence = intent.get('llm_confidence', 0.85)
        
        # Penalty for detected ambiguity markers
        ambiguity_markers = ['or', 'maybe', 'either', 'could be']
        ambiguity_penalty = sum(
            0.1 for marker in ambiguity_markers 
            if marker in query.lower()
        )
        
        return max(0, interpretation_confidence - ambiguity_penalty)
    
    def _generate_schema_clarifications(self, intent: dict, schema: dict) -> list[str]:
        """Generate specific clarification questions for ambiguous references"""
        questions = []
        
        # Example: Multiple matching dimensions
        if intent.get('ambiguous_dimensions'):
            for dim, options in intent['ambiguous_dimensions'].items():
                options_str = ', '.join(options[:3])
                questions.append(
                    f"When you say '{dim}', do you mean: {options_str}?"
                )
        
        return questions
```

---

## E2B Python sandbox integration

For safe code execution, E2B provides Firecracker-based microVMs with **sub-200ms startup** and hardware-level isolation.

**Sandbox Service Implementation:**

```python
from e2b_code_interpreter import Sandbox
from typing import Optional
import asyncio

class SecurePythonExecutor:
    def __init__(self, 
                 template: str = "python-data-analysis",
                 timeout_seconds: int = 60,
                 max_memory_mb: int = 512):
        self.template = template
        self.timeout = timeout_seconds
        self.max_memory = max_memory_mb
        
        # Allowed packages for analytics
        self.allowed_packages = {
            'pandas', 'numpy', 'scipy', 'statsmodels',
            'scikit-learn', 'matplotlib', 'seaborn', 'plotly'
        }
    
    async def execute_analysis(self, 
                               code: str, 
                               data_context: dict) -> dict:
        """Execute Python code in isolated sandbox"""
        
        # Validate code before execution
        validation_result = self._validate_code(code)
        if not validation_result['safe']:
            return {
                'success': False,
                'error': f"Code validation failed: {validation_result['reason']}",
                'output': None
            }
        
        try:
            with Sandbox(template=self.template) as sandbox:
                # Inject data context as pre-loaded DataFrame
                if data_context.get('dataframe'):
                    setup_code = f"""
import pandas as pd
import json

data = json.loads('''{json.dumps(data_context['dataframe'])}''')
df = pd.DataFrame(data)
"""
                    sandbox.run_code(setup_code)
                
                # Execute user analysis code
                execution = sandbox.run_code(
                    code,
                    timeout=self.timeout
                )
                
                return {
                    'success': True,
                    'output': execution.text,
                    'logs': execution.logs,
                    'artifacts': self._extract_artifacts(execution)
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': None
            }
    
    def _validate_code(self, code: str) -> dict:
        """Pre-execution security validation"""
        dangerous_patterns = [
            'subprocess', 'os.system', 'eval(', 'exec(',
            'open(', '__import__', 'importlib',
            'requests', 'urllib', 'socket'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in code:
                return {
                    'safe': False,
                    'reason': f"Disallowed operation: {pattern}"
                }
        
        return {'safe': True}
    
    def _extract_artifacts(self, execution) -> list:
        """Extract generated visualizations and files"""
        artifacts = []
        if hasattr(execution, 'results'):
            for result in execution.results:
                if hasattr(result, 'png'):
                    artifacts.append({
                        'type': 'image',
                        'format': 'png',
                        'data': result.png
                    })
        return artifacts
```

---

## Complete project requirements document

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Natural language query input with multi-turn conversation support | P0 |
| FR-2 | Semantic layer integration (Cube/dbt) serving as ground truth | P0 |
| FR-3 | Uncertainty scoring with configurable thresholds (default 95%) | P0 |
| FR-4 | Clarification prompt generation for ambiguous queries | P0 |
| FR-5 | Python code execution in isolated sandbox (E2B) | P1 |
| FR-6 | Interactive visualization generation | P1 |
| FR-7 | Audit logging of all queries and agent actions | P0 |
| FR-8 | Role-based access control inherited from semantic layer | P0 |
| FR-9 | Feedback collection (thumbs up/down with comments) | P1 |
| FR-10 | Export to multiple formats (charts, SQL, Python notebooks) | P2 |

### Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1 | Query response latency (cached) | < 500ms P95 |
| NFR-2 | Query response latency (warehouse) | < 5s P95 |
| NFR-3 | Sandbox startup time | < 250ms |
| NFR-4 | System availability | 99.9% |
| NFR-5 | Query accuracy (with semantic layer) | > 95% |
| NFR-6 | False positive rate for clarification triggers | < 10% |

### Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Orchestration | LangGraph / Custom | Stateful multi-agent workflows |
| LLM | Claude 4 / GPT-4.1 | Best-in-class reasoning |
| Semantic Layer | Cube.dev | Pre-aggregation, AI API, MCP support |
| Code Sandbox | E2B | Firecracker isolation, fast startup |
| Vector Store | Pinecone / Chroma | RAG for documentation context |
| Warehouse | Snowflake / BigQuery | Customer's existing infrastructure |
| Frontend | React + Plotly | Interactive visualizations |
| API Layer | FastAPI | Async support, OpenAPI docs |

### Security Requirements

- Code sandbox with network isolation (no outbound connections)
- Resource limits: 512MB memory, 60s execution timeout
- Package whitelist enforcement
- RBAC integration with semantic layer permissions
- Audit logging of all generated queries with user attribution
- No customer data used for model training
- SOC 2 Type II compliance required

---

## Conclusion: The architecture advantage

Production-grade agentic analytics requires three non-negotiable components that separate demo-ready from enterprise-ready systems. First, a **semantic layer as ground truth**—without governed metrics and business logic, LLMs hallucinate at rates up to 46% on complex queries. With semantic grounding, accuracy approaches 99.8%. Second, **calibrated uncertainty scoring** that triggers human collaboration rather than confident mistakes. The research shows clarification improves accuracy from 42.5% to 92.5% on ambiguous queries—the ROI of asking is immense. Third, **sandboxed execution** via Firecracker microVMs or equivalent, providing hardware-level isolation for Python analysis without compromising sub-second responsiveness.

The Open Semantic Interchange initiative signals where the industry is heading: portable, vendor-neutral semantic models that AI agents can consume across any tool. Organizations building this infrastructure today are positioning for the agentic analytics era—where AI doesn't just answer questions, but collaborates as a genuine analytical partner.