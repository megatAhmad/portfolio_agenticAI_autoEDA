# Architecture Deep Dive

> Comprehensive technical documentation of Agentic Data Analyst's system design

---

## Table of Contents

1. [System Philosophy](#system-philosophy)
2. [Layer Architecture](#layer-architecture)
3. [Data Flow Diagrams](#data-flow-diagrams)
4. [Component Deep Dives](#component-deep-dives)
5. [State Management](#state-management)
6. [Security Architecture](#security-architecture)
7. [Scalability Considerations](#scalability-considerations)
8. [Technology Decisions](#technology-decisions)

---

## System Philosophy

### The Consultant Pattern

ADA implements what we call the **"Consultant Pattern"** - a fundamental shift from traditional AI analytics:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TRADITIONAL AI vs CONSULTANT PATTERN                      │
└─────────────────────────────────────────────────────────────────────────────┘

TRADITIONAL AI (Confident but Often Wrong):
═══════════════════════════════════════════

  User Query ──▶ AI Interprets ──▶ Execute ──▶ Result
                     │
                     └── "I'll guess what you mean"
                         (42.5% accuracy on ambiguous queries)


CONSULTANT PATTERN (Clarifies then Executes):
═════════════════════════════════════════════

  User Query ──▶ Evaluate ──▶ Confident? ──┬──▶ YES ──▶ Execute
                Confidence       │          │
                                 │          └──▶ NO ──▶ Clarify ──┐
                                 │                                │
                                 └────────────────────────────────┘
                                        (92.5% accuracy)
```

### Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Transparency** | Show confidence scores, explain reasoning |
| **User Control** | Require approval before execution |
| **Graceful Degradation** | Fallback to simpler methods when LLM unavailable |
| **Security First** | Air-gapped sandbox, code validation |
| **Local First** | Run entirely on-premise, no cloud dependencies |

---

## Layer Architecture

### Architectural Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: PRESENTATION                                                        │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │    Chat     │  │   Context   │  │    Plan     │  │      Results        │ │
│  │  Interface  │  │  Validator  │  │  Approval   │  │     Explorer        │ │
│  │             │  │             │  │             │  │                     │ │
│  │ Streamlit   │  │ Streamlit   │  │ Streamlit   │  │ Streamlit + AgGrid  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                │                    │            │
└─────────┼────────────────┼────────────────┼────────────────────┼────────────┘
          │                │                │                    │
          ▼                ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: ORCHESTRATION                                                       │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        Main Orchestrator                               │  │
│  │                                                                        │  │
│  │   ┌─────────────────┐   ┌─────────────────┐   ┌────────────────────┐  │  │
│  │   │ Planning Agent  │   │  Uncertainty    │   │  HITL Controller   │  │  │
│  │   │                 │   │    Scorer       │   │                    │  │  │
│  │   │ • Parse Intent  │   │                 │   │ • Clarifications   │  │  │
│  │   │ • Create Plan   │   │ • Data: 35%     │   │ • Approvals        │  │  │
│  │   │ • Coordinate    │   │ • Schema: 35%   │   │ • Learning         │  │  │
│  │   │                 │   │ • Query: 30%    │   │                    │  │  │
│  │   └────────┬────────┘   └────────┬────────┘   └─────────┬──────────┘  │  │
│  │            │                     │                      │             │  │
│  └────────────┼─────────────────────┼──────────────────────┼─────────────┘  │
│               │                     │                      │                │
└───────────────┼─────────────────────┼──────────────────────┼────────────────┘
                │                     │                      │
                ▼                     ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: AGENTS                                                              │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────────────┐ │
│  │  SQL Generator  │  │ Python Analyst  │  │    Visualization Agent       │ │
│  │                 │  │                 │  │                              │ │
│  │ • NL → SQL      │  │ • Statistics    │  │ • Auto Chart Selection       │ │
│  │ • Validation    │  │ • Aggregation   │  │ • Plotly Rendering           │ │
│  │ • Execution     │  │ • ML Tasks      │  │ • Dashboard Composition      │ │
│  └────────┬────────┘  └────────┬────────┘  └──────────────┬───────────────┘ │
│           │                    │                          │                 │
└───────────┼────────────────────┼──────────────────────────┼─────────────────┘
            │                    │                          │
            ▼                    ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 4: KNOWLEDGE                                                           │
│                                                                              │
│  ┌───────────────────────────────────┐  ┌────────────────────────────────┐  │
│  │         Semantic Layer            │  │         RAG System             │  │
│  │                                   │  │                                │  │
│  │  ┌─────────┐  ┌─────────────┐     │  │  ┌──────────────────────────┐  │  │
│  │  │ Metrics │  │ Dimensions  │     │  │  │      ChromaDB            │  │  │
│  │  └─────────┘  └─────────────┘     │  │  │  (Vector Store)          │  │  │
│  │  ┌─────────┐  ┌─────────────┐     │  │  └──────────────────────────┘  │  │
│  │  │ Rules   │  │  Synonyms   │     │  │  ┌──────────────────────────┐  │  │
│  │  └─────────┘  └─────────────┘     │  │  │  HuggingFace Embeddings  │  │  │
│  │                                   │  │  │  (all-MiniLM-L6-v2)      │  │  │
│  └───────────────────────────────────┘  │  └──────────────────────────┘  │  │
│                                         │                                │  │
└─────────────────────────────────────────┴────────────────────────────────┘  │
                                                                              │
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 5: EXECUTION                                                           │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────────────┐ │
│  │  Python Sandbox │  │   PostgreSQL    │  │        SQLite (Logs)         │ │
│  │    (Docker)     │  │                 │  │                              │ │
│  │                 │  │ • User Data     │  │ • conversations              │ │
│  │ • Air-gapped    │  │ • Results       │  │ • clarifications             │ │
│  │ • 512MB / 30s   │  │                 │  │ • feedback                   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Responsibility | Key Decisions |
|-------|---------------|---------------|
| **Presentation** | User interaction, display | Streamlit for rapid development |
| **Orchestration** | Workflow coordination, confidence | State machine pattern |
| **Agents** | Specialized task execution | Single responsibility per agent |
| **Knowledge** | Context and business logic | Hybrid semantic + RAG approach |
| **Execution** | Safe code running, data storage | Docker isolation |

---

## Data Flow Diagrams

### Query Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      QUERY PROCESSING DATA FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

                          ┌─────────────────┐
                          │   User Query    │
                          │  "Show sales    │
                          │   by region"    │
                          └────────┬────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: CONTEXT ENRICHMENT                                                   │
│                                                                              │
│   Query ───▶ Semantic Layer ───▶ + Metric definitions                        │
│         │                        + Dimension mappings                        │
│         │                        + Business rules                            │
│         │                                                                    │
│         └──▶ RAG System ────────▶ + Related documents                        │
│                                   + Historical context                       │
│                                                                              │
│   Output: Enriched Query Context                                             │
└──────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: INTENT PARSING (Planning Agent)                                      │
│                                                                              │
│   Input: Query + Context                                                     │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  LLM Analysis                                                       │   │
│   │                                                                     │   │
│   │  Prompt:                                                            │   │
│   │  "Parse this query: {query}                                         │   │
│   │   Available metrics: {metrics}                                      │   │
│   │   Available dimensions: {dimensions}"                               │   │
│   │                                                                     │   │
│   │  Response:                                                          │   │
│   │  {                                                                  │   │
│   │    "metrics": ["revenue"],                                          │   │
│   │    "dimensions": ["region"],                                        │   │
│   │    "time_period": null,                                             │   │
│   │    "confidence": 0.82                                               │   │
│   │  }                                                                  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   Output: ParsedIntent                                                       │
└──────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: UNCERTAINTY SCORING                                                  │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                                                                     │   │
│   │   Data Completeness (35%)      Schema Confidence (35%)              │   │
│   │   ┌───────────────────┐        ┌───────────────────┐                │   │
│   │   │ Check null rates  │        │ Match metrics     │                │   │
│   │   │ Check coverage    │        │ Match dimensions  │                │   │
│   │   │ Required columns  │        │ Check synonyms    │                │   │
│   │   │                   │        │                   │                │   │
│   │   │ Score: 0.90       │        │ Score: 0.75       │                │   │
│   │   └───────────────────┘        └───────────────────┘                │   │
│   │                                                                     │   │
│   │   Query Confidence (30%)       WEIGHTED TOTAL                       │   │
│   │   ┌───────────────────┐        ┌───────────────────┐                │   │
│   │   │ LLM self-assess   │        │ 0.35 × 0.90 = 0.315│               │   │
│   │   │ Ambiguity check   │        │ 0.35 × 0.75 = 0.263│               │   │
│   │   │                   │        │ 0.30 × 0.82 = 0.246│               │   │
│   │   │ Score: 0.82       │        │ ─────────────────  │               │   │
│   │   └───────────────────┘        │ Total:      0.824  │               │   │
│   │                                └───────────────────┘                │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   Output: UncertaintyResult (score: 0.824, needs_clarification: true)        │
└──────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                          ┌────────────────┐
                          │  0.824 < 0.95  │
                          │      YES       │
                          └───────┬────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: CLARIFICATION (HITL Controller)                                      │
│                                                                              │
│   Generate questions for ambiguous terms:                                    │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Q1: Which "sales" metric did you mean?                             │   │
│   │      ○ Total Revenue    ○ Net Sales    ○ Gross Sales                │   │
│   │                                                                     │   │
│   │  Q2: Which time period?                                             │   │
│   │      ○ Last Quarter    ○ Last Month    ○ YTD                        │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   User responds: "Net Sales", "Last Quarter"                                 │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  LEARNING: Store mapping "sales" → "net_sales" for future queries   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   Recalculate: New score = 0.97 ✓                                            │
└──────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: PLAN CREATION                                                        │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Execution Plan                                                     │   │
│   │                                                                     │   │
│   │  Objective: "Analyze net sales by region for Q4"                    │   │
│   │  Confidence: 97%                                                    │   │
│   │                                                                     │   │
│   │  Tasks:                                                             │   │
│   │  ┌────────────────────────────────────────────────────────────────┐│   │
│   │  │ task_1: SQL Query                                              ││   │
│   │  │   SELECT region, SUM(net_sales) FROM orders                    ││   │
│   │  │   WHERE order_date BETWEEN '2024-10-01' AND '2024-12-31'       ││   │
│   │  │   GROUP BY region                                              ││   │
│   │  │   deps: []                                                     ││   │
│   │  └────────────────────────────────────────────────────────────────┘│   │
│   │  ┌────────────────────────────────────────────────────────────────┐│   │
│   │  │ task_2: Visualization                                          ││   │
│   │  │   Create bar chart of results                                  ││   │
│   │  │   deps: [task_1]                                               ││   │
│   │  └────────────────────────────────────────────────────────────────┘│   │
│   │  ┌────────────────────────────────────────────────────────────────┐│   │
│   │  │ task_3: Synthesis                                              ││   │
│   │  │   Generate summary text                                        ││   │
│   │  │   deps: [task_1, task_2]                                       ││   │
│   │  └────────────────────────────────────────────────────────────────┘│   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   → Present to user for approval                                             │
└──────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                       User approves plan ✓
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: EXECUTION                                                            │
│                                                                              │
│   Execute tasks in dependency order:                                         │
│                                                                              │
│   [task_1] ────▶ SQL Generator ────▶ PostgreSQL ────▶ Data                   │
│                                                           │                  │
│   [task_2] ────▶ Visualization Agent ◀────────────────────┤                  │
│                         │                                 │                  │
│                         ▼                                 │                  │
│                   Plotly Chart                            │                  │
│                                                           │                  │
│   [task_3] ────▶ LLM Synthesis ◀──────────────────────────┘                  │
│                         │                                                    │
│                         ▼                                                    │
│                 "North region led with 35% of sales..."                      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │     Results     │
                          │  + Data Table   │
                          │  + Bar Chart    │
                          │  + Summary      │
                          └─────────────────┘
```

---

## Component Deep Dives

### Planning Agent State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PLANNING AGENT STATE MACHINE                              │
└─────────────────────────────────────────────────────────────────────────────┘

                        ┌─────────────────┐
                        │      IDLE       │
                        │                 │
                        │  Waiting for    │
                        │  user query     │
                        └────────┬────────┘
                                 │
                          receive_query()
                                 │
                                 ▼
                        ┌─────────────────┐
                        │    PARSING      │
                        │                 │
                        │  Extracting     │
              ┌─────────│  intent         │─────────┐
              │         └─────────────────┘         │
              │                                     │
        parse_failed()                        parse_success()
              │                                     │
              ▼                                     ▼
     ┌─────────────────┐                   ┌─────────────────┐
     │   FALLBACK      │                   │   SCORING       │
     │                 │                   │                 │
     │  Use keyword    │                   │  Calculating    │
     │  extraction     │                   │  confidence     │
     └────────┬────────┘                   └────────┬────────┘
              │                                     │
              └──────────────────┬──────────────────┘
                                 │
                          score_complete()
                                 │
                         ┌───────┴───────┐
                         │               │
                   score < 0.95    score >= 0.95
                         │               │
                         ▼               ▼
                ┌─────────────┐  ┌─────────────────┐
                │ CLARIFYING  │  │   PLANNING      │
                │             │  │                 │
                │ Generating  │  │  Creating       │
                │ questions   │  │  execution      │
                └──────┬──────┘  │  plan           │
                       │         └────────┬────────┘
                       │                  │
            user_responds()          plan_ready()
                       │                  │
                       ▼                  ▼
                ┌─────────────┐  ┌─────────────────┐
                │ RESCORING   │  │ AWAITING        │
                │             │  │ APPROVAL        │
                │ Recalculate │  │                 │
                │ with new    │  │ User reviews    │
                │ info        │  │ plan            │
                └──────┬──────┘  └────────┬────────┘
                       │                  │
                       │           ┌──────┴──────┐
                       │           │             │
                       │      rejected()    approved()
                       │           │             │
                       │           ▼             ▼
                       │  ┌─────────────┐ ┌─────────────────┐
                       │  │  REJECTED   │ │   EXECUTING     │
                       │  │             │ │                 │
                       │  │ Return to   │ │  Running tasks  │
                       └──│ IDLE        │ │  in order       │
                          └─────────────┘ └────────┬────────┘
                                                   │
                                          execution_complete()
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │   COMPLETE      │
                                          │                 │
                                          │  Display        │
                                          │  results        │
                                          └────────┬────────┘
                                                   │
                                             feedback()
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │      IDLE       │
                                          └─────────────────┘
```

### Uncertainty Scorer Algorithm

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    UNCERTAINTY SCORING ALGORITHM                             │
└─────────────────────────────────────────────────────────────────────────────┘

INPUTS:
  - parsed_intent: ParsedIntent
  - semantic_layer: SemanticLayer
  - data_profile: dict (optional)

ALGORITHM:

┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. DATA COMPLETENESS SCORE                                                   │
│                                                                              │
│    for each required_column in (intent.metrics + intent.dimensions):         │
│        if column exists in data_profile:                                     │
│            null_rate = data_profile[column].null_rate                        │
│            column_scores.append(1 - null_rate)                               │
│        else:                                                                 │
│            column_scores.append(0)  # Missing column                         │
│            issues.append(f"Column {column} not found")                       │
│                                                                              │
│    data_score = mean(column_scores) or 0.5 if no profile                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. SCHEMA CONFIDENCE SCORE                                                   │
│                                                                              │
│    matched = 0                                                               │
│    total = len(intent.metrics) + len(intent.dimensions)                      │
│                                                                              │
│    for term in intent.metrics:                                               │
│        matches = semantic_layer.find_matching_metrics(term)                  │
│        if len(matches) == 1:                                                 │
│            matched += 1                                                      │
│        elif len(matches) > 1:                                                │
│            matched += 0.5  # Ambiguous                                       │
│            questions.append(create_disambiguation_question(term, matches))   │
│        else:                                                                 │
│            issues.append(f"Metric {term} not found")                         │
│                                                                              │
│    # Same for dimensions...                                                  │
│                                                                              │
│    schema_score = matched / total if total > 0 else 1.0                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. QUERY CONFIDENCE SCORE                                                    │
│                                                                              │
│    query_score = intent.confidence  # From LLM                               │
│                                                                              │
│    # Penalties                                                               │
│    if not intent.metrics:                                                    │
│        query_score *= 0.8                                                    │
│        issues.append("No metrics identified")                                │
│                                                                              │
│    if intent.action == "query" and not intent.dimensions:                    │
│        query_score *= 0.9                                                    │
│        issues.append("No grouping dimensions")                               │
│                                                                              │
│    for ambiguity in intent.ambiguities:                                      │
│        issues.append(ambiguity)                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. WEIGHTED COMBINATION                                                      │
│                                                                              │
│    overall_score = (                                                         │
│        DATA_WEIGHT * data_score +      # 0.35                                │
│        SCHEMA_WEIGHT * schema_score +  # 0.35                                │
│        QUERY_WEIGHT * query_score      # 0.30                                │
│    )                                                                         │
│                                                                              │
│    needs_clarification = overall_score < THRESHOLD  # 0.95                   │
│                                                                              │
│    return UncertaintyResult(                                                 │
│        score=overall_score,                                                  │
│        breakdown=breakdown,                                                  │
│        needs_clarification=needs_clarification,                              │
│        reasons=issues,                                                       │
│        suggested_questions=questions                                         │
│    )                                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

### Sandbox Security Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SECURITY LAYERS                                        │
└─────────────────────────────────────────────────────────────────────────────┘

LAYER 1: CODE VALIDATION (Before Execution)
═══════════════════════════════════════════

   User Code ──▶ AST Parser ──▶ Pattern Matching ──▶ ALLOW/BLOCK

   BLOCKED PATTERNS:
   ┌─────────────────────────────────────────────────────────────────────┐
   │  eval()        exec()        __import__()    compile()              │
   │  open()        os.system()   subprocess.*    requests.*             │
   │  urllib.*      socket.*      pickle.*        marshal.*              │
   └─────────────────────────────────────────────────────────────────────┘


LAYER 2: IMPORT RESTRICTIONS
════════════════════════════

   ALLOWED IMPORTS:                    BLOCKED IMPORTS:
   ┌──────────────────────┐            ┌──────────────────────┐
   │  pandas              │            │  os                  │
   │  numpy               │            │  sys                 │
   │  scipy               │            │  subprocess          │
   │  scikit-learn        │            │  shutil              │
   │  plotly              │            │  requests            │
   │  matplotlib          │            │  urllib              │
   │                      │            │  socket              │
   └──────────────────────┘            │  http                │
                                       │  ftplib              │
                                       │  pickle              │
                                       └──────────────────────┘


LAYER 3: CONTAINER ISOLATION
════════════════════════════

   ┌─────────────────────────────────────────────────────────────────────┐
   │  DOCKER CONTAINER                                                   │
   │                                                                     │
   │  ┌───────────────────────────────────────────────────────────────┐ │
   │  │  Security Configuration                                       │ │
   │  │                                                               │ │
   │  │  network_mode: none          # No network access              │ │
   │  │  read_only: true             # Read-only filesystem           │ │
   │  │  tmpfs: /tmp (100MB)         # Limited writable space         │ │
   │  │  mem_limit: 512MB            # Memory cap                     │ │
   │  │  cpu_quota: 50000            # 50% CPU limit                  │ │
   │  │  security_opt:                                                │ │
   │  │    - no-new-privileges:true  # No privilege escalation        │ │
   │  │  cap_drop: ALL               # Drop all Linux capabilities    │ │
   │  │                                                               │ │
   │  └───────────────────────────────────────────────────────────────┘ │
   │                                                                     │
   │  User: sandbox (uid 1000, non-root)                                │
   │                                                                     │
   └─────────────────────────────────────────────────────────────────────┘


LAYER 4: TIMEOUT ENFORCEMENT
════════════════════════════

   ┌─────────────────────────────────────────────────────────────────────┐
   │                                                                     │
   │  container.wait(timeout=30)                                         │
   │                                                                     │
   │  If timeout exceeded:                                               │
   │    container.kill()                                                 │
   │    return SandboxResult(success=False, error="Timeout exceeded")    │
   │                                                                     │
   └─────────────────────────────────────────────────────────────────────┘
```

### SQL Injection Prevention

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SQL SECURITY MEASURES                                     │
└─────────────────────────────────────────────────────────────────────────────┘

1. PARAMETERIZED QUERIES ONLY
   ════════════════════════════

   ✗ WRONG:
     query = f"SELECT * FROM users WHERE id = {user_id}"

   ✓ CORRECT:
     query = "SELECT * FROM users WHERE id = %s"
     cursor.execute(query, (user_id,))


2. QUERY VALIDATION
   ═════════════════

   Before execution, queries are validated:

   ┌─────────────────────────────────────────────────────────────────────┐
   │  def validate_query(sql: str) -> tuple[bool, list[str]]:           │
   │      issues = []                                                   │
   │                                                                    │
   │      # Check for dangerous patterns                                │
   │      dangerous = ["DROP", "DELETE", "TRUNCATE", "ALTER",           │
   │                   "INSERT", "UPDATE", "CREATE", "GRANT"]           │
   │                                                                    │
   │      for pattern in dangerous:                                     │
   │          if pattern in sql.upper():                                │
   │              issues.append(f"Dangerous pattern: {pattern}")        │
   │                                                                    │
   │      # Check for comment injection                                 │
   │      if "--" in sql or "/*" in sql:                                │
   │          issues.append("SQL comments not allowed")                 │
   │                                                                    │
   │      return len(issues) == 0, issues                               │
   └─────────────────────────────────────────────────────────────────────┘


3. READ-ONLY DATABASE USER
   ═════════════════════════

   The application connects with a user that only has SELECT privileges:

   GRANT SELECT ON ALL TABLES IN SCHEMA public TO analyst;
```

---

## Technology Decisions

### Decision Matrix

| Component | Chosen | Alternatives Considered | Rationale |
|-----------|--------|------------------------|-----------|
| **UI Framework** | Streamlit | Gradio, Dash, FastAPI+React | Rapid prototyping, built-in components |
| **Vector Store** | ChromaDB | Pinecone, Weaviate, Milvus | Local-first, simple setup, good performance |
| **Embeddings** | HuggingFace | OpenAI, Cohere | No API dependency, runs locally |
| **Primary LLM** | Azure OpenAI | OpenAI direct, Anthropic | Enterprise features, data residency |
| **Fallback LLM** | OpenRouter | Multiple providers | Multi-model access, cost optimization |
| **Database** | PostgreSQL | MySQL, SQLite | Rich analytics functions, JSON support |
| **Sandbox** | Docker | Firecracker, gVisor | Mature ecosystem, easy deployment |
| **Visualization** | Plotly | Matplotlib, Altair | Interactive, web-native, good defaults |

### Performance Characteristics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PERFORMANCE BENCHMARKS                                  │
└─────────────────────────────────────────────────────────────────────────────┘

COMPONENT LATENCIES (P95):

  Intent Parsing (LLM)     │████████████████████████████████│  800ms
  Uncertainty Scoring      │███████│                         │  150ms
  SQL Generation (LLM)     │█████████████████████████│       │  600ms
  SQL Execution            │██████████████│                  │  300ms
  Visualization            │███████████│                     │  250ms
  Context Embedding        │████████████████████│            │  450ms
                           └─────────────────────────────────┘
                           0ms                              1000ms

TOTAL QUERY RESPONSE TIME:
  Cached:    < 2s   (semantic layer hit, no LLM calls)
  Uncached:  < 10s  (full pipeline with LLM calls)

MEMORY USAGE:
  Base Application:     ~200MB
  + ChromaDB loaded:    ~350MB
  + Large dataset:      ~500MB (depends on data size)
  Sandbox container:    512MB limit
```

---

## Next Steps

- [User Guide](./user-guide.md) - How to use the application
- [API Reference](../api/README.md) - Detailed API documentation
- [Examples](./examples.md) - Common use cases and patterns
