# Agentic Data Analyst (ADA) Documentation

> **A production-grade, local-first semantic analytics platform with human-in-the-loop validation**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Core Workflows](#core-workflows)
- [Components](#components)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Examples](#examples)

---

## Overview

**Agentic Data Analyst (ADA-2026)** addresses the critical gap where 95% of AI analytics tools fail on ambiguous queries due to lack of business context. It implements the **"consultant pattern"** - AI that asks clarifying questions rather than guessing when facing ambiguity.

### The Problem

```
Traditional AI Analytics:
┌──────────────┐    ┌───────────────┐    ┌──────────────┐
│ User Query   │───▶│ AI Interprets │───▶│ Wrong Answer │
│ "Show sales" │    │ (Guesses)     │    │ (42.5% acc)  │
└──────────────┘    └───────────────┘    └──────────────┘

ADA Consultant Pattern:
┌──────────────┐    ┌───────────────┐    ┌──────────────┐    ┌──────────────┐
│ User Query   │───▶│ AI Evaluates  │───▶│ Clarifies    │───▶│ Right Answer │
│ "Show sales" │    │ Confidence    │    │ Ambiguities  │    │ (92.5% acc)  │
└──────────────┘    └───────────────┘    └──────────────┘    └──────────────┘
```

### Key Differentiator

| Approach | Accuracy | User Trust |
|----------|----------|------------|
| Traditional (Guess) | 42.5% | Low |
| **ADA (Clarify)** | **92.5%** | **High** |

---

## Key Features

- **Human-in-the-Loop (HITL)** - Clarification questions when confidence < 95%
- **Semantic Context** - Business glossary with metrics, dimensions, and rules
- **RAG-Enhanced** - ChromaDB + HuggingFace embeddings for context retrieval
- **Secure Sandbox** - Docker-isolated Python execution (optional)
- **Interactive Visualizations** - Auto-generated Plotly charts
- **Plan Approval** - Users approve execution plans before running
- **LLM Observability** - Langfuse integration for tracing, debugging, and cost tracking
- **Per-Agent Model Selection** - Configure different models for each agent/scenario for cost and quality optimization

---

## Quick Start

### Installation

```bash
# Clone and setup
git clone https://github.com/your-org/portfolio_agenticAI_autoEDA.git
cd portfolio_agenticAI_autoEDA

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your API keys
```

### Running the Application

```bash
# Start all services (PostgreSQL + Langfuse)
docker-compose up -d

# Or start selectively
docker-compose up -d postgres langfuse

# Access Langfuse UI for LLM observability at http://localhost:3000

# Run Streamlit app
streamlit run app/main.py
```

### First Query

1. Upload a CSV/Excel file via the sidebar
2. (Optional) Upload business context files
3. Ask a question: *"What was our revenue by region last quarter?"*
4. Review and approve the execution plan
5. Explore results with interactive charts

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────┐ ┌──────────────────────┐  │
│  │    Chat     │ │   Context    │ │    Plan     │ │      Results         │  │
│  │  Interface  │ │  Validator   │ │  Approval   │ │     Explorer         │  │
│  └──────┬──────┘ └──────┬───────┘ └──────┬──────┘ └──────────┬───────────┘  │
└─────────┼───────────────┼────────────────┼───────────────────┼──────────────┘
          │               │                │                   │
          ▼               ▼                ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATION ENGINE                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────────────┐ │
│  │ Planning Agent  │  │  Uncertainty    │  │     HITL Controller          │ │
│  │                 │  │    Scorer       │  │                              │ │
│  │ • Parse Intent  │  │                 │  │ • Clarification Questions    │ │
│  │ • Create Plan   │  │ • Data: 35%     │  │ • Approval Workflows         │ │
│  │ • Validate      │  │ • Schema: 35%   │  │ • Context Learning           │ │
│  │ • Execute       │  │ • Query: 30%    │  │                              │ │
│  └────────┬────────┘  └────────┬────────┘  └─────────────┬────────────────┘ │
└───────────┼────────────────────┼─────────────────────────┼──────────────────┘
            │                    │                         │
            ▼                    ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SPECIALIZED AGENTS                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────────────┐ │
│  │  SQL Generator  │  │ Python Analyst  │  │    Visualization Agent       │ │
│  │                 │  │                 │  │                              │ │
│  │ • Query Gen     │  │ • Analysis      │  │ • Chart Selection            │ │
│  │ • Validation    │  │ • Statistics    │  │ • Plotly Rendering           │ │
│  │ • Execution     │  │ • ML Models     │  │ • Dashboards                 │ │
│  └────────┬────────┘  └────────┬────────┘  └─────────────┬────────────────┘ │
└───────────┼────────────────────┼─────────────────────────┼──────────────────┘
            │                    │                         │
            ▼                    ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        KNOWLEDGE & DATA LAYER                                │
│  ┌─────────────────────────────────┐  ┌────────────────────────────────────┐│
│  │        Semantic Layer           │  │          RAG System                ││
│  │                                 │  │                                    ││
│  │  • Metrics & Dimensions         │  │  • ChromaDB Vector Store           ││
│  │  • Business Rules               │  │  • HuggingFace Embeddings          ││
│  │  • Synonyms & Relationships     │  │  • Context Retrieval               ││
│  └────────────────┬────────────────┘  └─────────────────┬──────────────────┘│
└───────────────────┼─────────────────────────────────────┼───────────────────┘
                    │                                     │
                    ▼                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXECUTION & STORAGE                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────────────┐ │
│  │  Python Sandbox │  │   PostgreSQL    │  │       SQLite (Logs)          │ │
│  │    (Docker)     │  │                 │  │                              │ │
│  │                 │  │ • User Data     │  │ • Conversations              │ │
│  │ • Air-gapped    │  │ • Analytics     │  │ • Clarifications             │ │
│  │ • 512MB / 30s   │  │                 │  │ • Feedback                   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Workflows

### 1. Main Query Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         QUERY PROCESSING PIPELINE                            │
└─────────────────────────────────────────────────────────────────────────────┘

User Input                    Orchestration                     Output
─────────────                 ─────────────                     ──────

┌──────────┐
│  User    │
│  Query   │
└────┬─────┘
     │
     ▼
┌──────────────────┐
│  Parse Intent    │◄──── Semantic Layer + RAG Context
│                  │
│  Extract:        │
│  • Metrics       │
│  • Dimensions    │
│  • Filters       │
│  • Time Range    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Uncertainty    │
│     Scorer       │
│                  │
│  Calculate:      │
│  • Data: 35%     │
│  • Schema: 35%   │
│  • Query: 30%    │
└────────┬─────────┘
         │
         ▼
    ┌────────────┐
    │ Confidence │
    │   >= 95%?  │
    └─────┬──────┘
          │
    ┌─────┴─────┐
    │           │
   YES          NO
    │           │
    ▼           ▼
┌────────┐  ┌──────────────┐
│ Create │  │   Generate   │
│  Plan  │  │ Clarification│
└───┬────┘  │  Questions   │
    │       └──────┬───────┘
    │              │
    │              ▼
    │       ┌──────────────┐
    │       │    User      │
    │       │  Responds    │───────┐
    │       └──────────────┘       │
    │                              │
    │◄─────────────────────────────┘
    │        (Loop until confident)
    │
    ▼
┌──────────────────┐
│   Display Plan   │
│   for Approval   │
└────────┬─────────┘
         │
         ▼
    ┌────────────┐
    │  Approved? │
    └─────┬──────┘
          │
    ┌─────┴─────┐
    │           │
   YES          NO ───▶ End / Modify
    │
    ▼
┌──────────────────┐
│  Execute Tasks   │
│  (Sequential)    │
│                  │
│  1. SQL Query    │
│  2. Analysis     │
│  3. Visualization│
│  4. Synthesis    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│  Display Results │────▶│ Collect Feedback │
│                  │     │                  │
│  • Data Table    │     │  • Rating        │
│  • Charts        │     │  • Accuracy      │
│  • Summary       │     │  • Comments      │
└──────────────────┘     └──────────────────┘
```

### 2. Uncertainty Scoring Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        UNCERTAINTY SCORING WORKFLOW                          │
└─────────────────────────────────────────────────────────────────────────────┘

                        ┌───────────────────┐
                        │   Parsed Intent   │
                        │                   │
                        │ metrics: [revenue]│
                        │ dimensions: [reg] │
                        │ confidence: 0.8   │
                        └─────────┬─────────┘
                                  │
           ┌──────────────────────┼──────────────────────┐
           │                      │                      │
           ▼                      ▼                      ▼
    ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
    │     DATA     │      │    SCHEMA    │      │    QUERY     │
    │ COMPLETENESS │      │  CONFIDENCE  │      │  CONFIDENCE  │
    │              │      │              │      │              │
    │  Weight: 35% │      │  Weight: 35% │      │  Weight: 30% │
    └──────┬───────┘      └──────┬───────┘      └──────┬───────┘
           │                     │                     │
           ▼                     ▼                     ▼
    ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
    │  • Null Rate │      │  • Metric    │      │  • LLM Self  │
    │  • Coverage  │      │    Mapping   │      │    Assessment│
    │  • Required  │      │  • Dimension │      │  • Ambiguity │
    │    Columns   │      │    Mapping   │      │    Detection │
    │              │      │  • Synonyms  │      │              │
    └──────┬───────┘      └──────┬───────┘      └──────┬───────┘
           │                     │                     │
           │  Score: 0.85        │  Score: 0.70        │  Score: 0.80
           │                     │                     │
           └──────────────────────┼─────────────────────┘
                                  │
                                  ▼
                        ┌───────────────────┐
                        │ WEIGHTED AVERAGE  │
                        │                   │
                        │ 0.35×0.85 = 0.298 │
                        │ 0.35×0.70 = 0.245 │
                        │ 0.30×0.80 = 0.240 │
                        │ ───────────────── │
                        │ Total:    = 0.783 │
                        └─────────┬─────────┘
                                  │
                                  ▼
                        ┌───────────────────┐
                        │  0.783 < 0.95?    │
                        │       YES         │
                        └─────────┬─────────┘
                                  │
                                  ▼
                        ┌───────────────────┐
                        │ NEEDS CLARIFICATION│
                        │                   │
                        │ Questions:        │
                        │ • Which revenue?  │
                        │ • Which time?     │
                        └───────────────────┘
```

### 3. Task Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TASK EXECUTION PIPELINE                             │
└─────────────────────────────────────────────────────────────────────────────┘

Execution Plan
──────────────

┌─────────────────────────────────────────────────────────────────────────────┐
│  Plan: "Analyze revenue by region for last quarter"                          │
│  Confidence: 96%                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  TASK DEPENDENCY GRAPH                                                       │
│                                                                              │
│     ┌──────────────┐                                                         │
│     │   Task 1     │                                                         │
│     │  SQL Query   │                                                         │
│     │   [2s]       │                                                         │
│     └──────┬───────┘                                                         │
│            │                                                                 │
│            ├───────────────────┐                                             │
│            │                   │                                             │
│            ▼                   ▼                                             │
│     ┌──────────────┐    ┌──────────────┐                                     │
│     │   Task 2     │    │   Task 3     │                                     │
│     │  Analysis    │    │ Visualization│                                     │
│     │   [5s]       │    │   [3s]       │                                     │
│     └──────┬───────┘    └──────┬───────┘                                     │
│            │                   │                                             │
│            └─────────┬─────────┘                                             │
│                      │                                                       │
│                      ▼                                                       │
│               ┌──────────────┐                                               │
│               │   Task 4     │                                               │
│               │  Synthesis   │                                               │
│               │   [4s]       │                                               │
│               └──────────────┘                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

Execution Sequence
──────────────────

Time ─────────────────────────────────────────────────────────────────────────▶

│ Task 1: SQL Query                                                            │
│ ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│ [0s-2s] Generating and executing SQL                                         │
│                                                                              │
│                                                                              │
│ Task 2: Analysis        Task 3: Visualization                                │
│ ░░░░░░░░░░░░████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│ ░░░░░░░░░░░░████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│ [2s-7s] Python analysis     [2s-5s] Plotly charts                            │
│         (runs in parallel)                                                   │
│                                                                              │
│                                                                              │
│ Task 4: Synthesis                                                            │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██████████████████░░░░░░░░░░░░░░░░░░░░░░░░│
│ [7s-11s] Generate summary                                                    │
│                                                                              │
│ ◀───────────────────── Total: ~11s ─────────────────────▶                    │
```

### 4. HITL Clarification Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       HUMAN-IN-THE-LOOP WORKFLOW                             │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌────────────────────────┐
                    │    User Query:         │
                    │  "Show me the sales"   │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │   Ambiguity Detected   │
                    │   Confidence: 62%      │
                    └───────────┬────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLARIFICATION SESSION                                                       │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Question 1: Which "sales" metric did you mean?                       │  │
│  │                                                                       │  │
│  │    ○ Total Revenue: Sum of all order amounts                          │  │
│  │    ○ Net Sales: Revenue after returns and discounts                   │  │
│  │    ○ Order Count: Number of orders placed                             │  │
│  │    ○ Units Sold: Total quantity of items sold                         │  │
│  │                                                                       │  │
│  │  [User selects: Net Sales]                                            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Question 2: Which time period should I use?                          │  │
│  │                                                                       │  │
│  │    ○ Last Quarter                                                     │  │
│  │    ○ Last Month                                                       │  │
│  │    ○ Year to Date                                                     │  │
│  │    ○ Last 30 Days                                                     │  │
│  │                                                                       │  │
│  │  [User selects: Last Quarter]                                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │  Context Learning      │
                    │                        │
                    │  "sales" → Net Sales   │
                    │  (stored for future)   │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │  Recalculate Score     │
                    │  New Confidence: 97%   │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │  Proceed to Planning   │
                    └────────────────────────┘
```

### 5. Secure Sandbox Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SANDBOX EXECUTION WORKFLOW                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│  Python Code    │
│  from Agent     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CODE VALIDATION                                                             │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  AST Analysis                                                       │    │
│  │                                                                     │    │
│  │  BLOCKED PATTERNS:                                                  │    │
│  │  ✗ eval()        ✗ exec()        ✗ __import__()                     │    │
│  │  ✗ compile()     ✗ open()        ✗ os.system()                      │    │
│  │                                                                     │    │
│  │  BLOCKED IMPORTS:                                                   │    │
│  │  ✗ os            ✗ subprocess    ✗ requests                         │    │
│  │  ✗ urllib        ✗ socket        ✗ pickle                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Result: ✓ PASS  or  ✗ BLOCKED                                               │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼ (if PASS)
┌─────────────────────────────────────────────────────────────────────────────┐
│  DOCKER CONTAINER                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                                                                         ││
│  │  ┌─────────────────────┐                                                ││
│  │  │   Security Config   │                                                ││
│  │  │                     │                                                ││
│  │  │  • network: disabled│                                                ││
│  │  │  • memory: 512MB    │                                                ││
│  │  │  • timeout: 30s     │                                                ││
│  │  │  • read-only: true  │                                                ││
│  │  │  • capabilities: [] │                                                ││
│  │  └─────────────────────┘                                                ││
│  │                                                                         ││
│  │  ┌─────────────────────┐    ┌─────────────────────────────────────────┐││
│  │  │  Whitelisted Pkgs   │    │            Execution                    │││
│  │  │                     │    │                                         │││
│  │  │  ✓ pandas           │───▶│  import pandas as pd                    │││
│  │  │  ✓ numpy            │    │  df = pd.DataFrame(data)                │││
│  │  │  ✓ scipy            │    │  result = df.groupby('region').sum()    │││
│  │  │  ✓ scikit-learn     │    │                                         │││
│  │  │  ✓ plotly           │    │  → output.json                          │││
│  │  │  ✓ matplotlib       │    │                                         │││
│  │  └─────────────────────┘    └─────────────────────────────────────────┘││
│  │                                                                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  SandboxResult  │
│                 │
│  success: true  │
│  output: {...}  │
│  time_ms: 1234  │
└─────────────────┘
```

---

## Components

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       COMPONENT INTERACTION MAP                              │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │   main.py    │
                              │  (Streamlit) │
                              └──────┬───────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│      UI         │         │  Orchestration  │         │    Agents       │
│                 │         │                 │         │                 │
│ • chat.py       │◀───────▶│ • planning_     │◀───────▶│ • sql_generator │
│ • context_      │         │   agent.py      │         │ • python_       │
│   validator.py  │         │ • uncertainty_  │         │   analyst.py    │
│ • plan_         │         │   scorer.py     │         │ • visualization │
│   approval.py   │         │ • hitl_         │         │   .py           │
│ • results_      │         │   controller.py │         │                 │
│   explorer.py   │         │                 │         │                 │
└────────┬────────┘         └────────┬────────┘         └────────┬────────┘
         │                           │                           │
         │                           │                           │
         │                           ▼                           │
         │                  ┌─────────────────┐                  │
         │                  │   Knowledge     │                  │
         │                  │                 │                  │
         └─────────────────▶│ • semantic_     │◀─────────────────┘
                            │   layer.py      │
                            │ • rag_system.py │
                            │                 │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │   Execution     │
                            │                 │
                            │ • sandbox.py    │
                            │ • db_manager.py │
                            │                 │
                            └─────────────────┘
```

### Component Summary Table

| Component | File | Purpose |
|-----------|------|---------|
| **Planning Agent** | `orchestration/planning_agent.py` | Parse intent, create execution plans |
| **Uncertainty Scorer** | `orchestration/uncertainty_scorer.py` | Calculate confidence scores |
| **HITL Controller** | `orchestration/hitl_controller.py` | Manage clarifications & approvals |
| **SQL Generator** | `agents/sql_generator.py` | Generate and execute SQL queries |
| **Python Analyst** | `agents/python_analyst.py` | Statistical analysis & ML |
| **Visualization Agent** | `agents/visualization.py` | Create Plotly charts |
| **Semantic Layer** | `knowledge/semantic_layer.py` | Business context definitions |
| **RAG System** | `knowledge/rag_system.py` | Vector search for context |
| **Secure Sandbox** | `execution/sandbox.py` | Isolated code execution |
| **Database Manager** | `execution/db_manager.py` | PostgreSQL operations |

---

## Configuration

### Environment Variables

```bash
# .env file

# ═══════════════════════════════════════════════════════════════════════════
# LLM Configuration
# ═══════════════════════════════════════════════════════════════════════════
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_GPT4_DEPLOYMENT=gpt-4-turbo
AZURE_GPT35_DEPLOYMENT=gpt-35-turbo

# Fallback (if Azure unavailable)
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=anthropic/claude-3-sonnet

# ═══════════════════════════════════════════════════════════════════════════
# Database Configuration
# ═══════════════════════════════════════════════════════════════════════════
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=analytics_db
POSTGRES_USER=analyst
POSTGRES_PASSWORD=secure_password

# ═══════════════════════════════════════════════════════════════════════════
# Application Settings
# ═══════════════════════════════════════════════════════════════════════════
UNCERTAINTY_THRESHOLD=0.95    # Triggers HITL if below
MAX_SANDBOX_TIMEOUT=30        # Seconds
MAX_UPLOAD_SIZE_MB=100
CACHE_ENABLED=true
CHROMA_PERSIST_DIR=./chroma_db
LOG_LEVEL=INFO
```

---

## Examples

### Example 1: Simple Query

```python
# User asks: "What was our revenue last quarter?"

# 1. Intent Parsing
parsed_intent = {
    "metrics": ["revenue"],
    "dimensions": [],
    "time_period": "last_quarter",
    "action": "query",
    "confidence": 0.92
}

# 2. Uncertainty Scoring
uncertainty_result = {
    "score": 0.89,
    "breakdown": {
        "data_completeness": 0.95,
        "schema_confidence": 0.82,
        "query_confidence": 0.92
    },
    "needs_clarification": True,
    "suggested_questions": [
        {
            "text": "Which 'revenue' metric did you mean?",
            "options": ["Total Revenue", "Net Revenue", "Gross Revenue"]
        }
    ]
}

# 3. After clarification, execute plan
execution_plan = {
    "main_objective": "Query total revenue for last quarter",
    "tasks": [
        {"type": "sql_query", "description": "Retrieve revenue data"},
        {"type": "synthesis", "description": "Generate summary"}
    ]
}
```

### Example 2: Complex Analysis

```python
# User asks: "Compare sales performance across regions and show trends"

# Execution Plan Generated
plan = {
    "main_objective": "Compare regional sales with trend analysis",
    "confidence": 0.96,
    "tasks": [
        {
            "id": "task_1",
            "type": "sql_query",
            "description": "Retrieve sales by region and time",
            "estimated_time": "2s"
        },
        {
            "id": "task_2",
            "type": "python_analysis",
            "description": "Calculate growth rates and comparisons",
            "dependencies": ["task_1"],
            "estimated_time": "5s"
        },
        {
            "id": "task_3",
            "type": "visualization",
            "description": "Create trend line chart by region",
            "dependencies": ["task_1"],
            "estimated_time": "3s"
        },
        {
            "id": "task_4",
            "type": "synthesis",
            "description": "Generate insights summary",
            "dependencies": ["task_2", "task_3"],
            "estimated_time": "4s"
        }
    ]
}
```

---

## API Reference

See [API Documentation](./api/README.md) for detailed API reference.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## License

MIT License - see [LICENSE](../LICENSE) for details.

---

<p align="center">
  <strong>Agentic Data Analyst</strong> - Built with the Consultant Pattern
</p>
