# CLAUDE.md - Agentic Data Analyst Project Guide

## Project Overview

**Agentic Data Analyst (ADA-2026)**: A production-grade, local-first semantic analytics platform that combines semantic context understanding with human-in-the-loop (HITL) validation. The system addresses the critical gap where 95% of AI analytics tools fail on ambiguous queries due to lack of business context.

**Key differentiator**: Implements the "consultant pattern" - AI that asks clarifying questions rather than guessing when facing ambiguity (improves accuracy from 42.5% to 92.5% on complex queries).

## Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| UI Framework | Streamlit | 1.30+ |
| Backend | Python | 3.11+ |
| Database | PostgreSQL | 15+ |
| Vector Store | ChromaDB | 0.4+ |
| Embeddings | HuggingFace, Azure OpenAI, OpenRouter | sentence-transformers/all-MiniLM-L6-v2, OpenAI Embedding Models, Other Embedding Models |
| LLM | Azure OpenAI, OpenRouter | GPT-4, Claude, Llama |
| Fallback LLM | OpenRouter | Claude/Llama |
| Code Sandbox | Docker | 24+ |
| Visualization | Plotly | 5.18+ |
| Data Tables | Streamlit-AgGrid | 1.0+ |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          STREAMLIT UI LAYER                          │
│  Chat Interface │ Context Validator │ Plan Approval │ Results Explorer│
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION ENGINE                            │
│  Planning Agent │ Uncertainty Scorer │ HITL Controller               │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SPECIALIZED AGENTS                              │
│  SQL Generator Agent │ Python Analyst Agent │ Visualization Agent    │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     KNOWLEDGE & DATA LAYER                           │
│  Semantic Layer (JSON) │ RAG System (ChromaDB + HF Embeddings)       │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EXECUTION & STORAGE                             │
│  Python Sandbox (Docker) │ PostgreSQL │ Interaction DB (SQLite)      │
└─────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Context Validator
- Compares data schema against provided context
- Minimum completeness threshold: 95%
- Generates specific questions for unmapped columns

### 2. Uncertainty Scorer
Three-factor confidence calculation:
- **Data Completeness (35%)**: null rates, coverage
- **Schema Confidence (35%)**: field mapping accuracy
- **Query Confidence (30%)**: LLM self-assessment

Threshold: 95% - triggers HITL clarification if below.

### 3. HITL Controller
- Generates clarification questions (multiple choice / open-ended)
- Manages approval workflows
- Context enrichment loop

### 4. Planning Agent
- Decomposes queries into hierarchical tasks
- Creates dependency graphs
- Requires user approval before execution

### 5. Python Sandbox
- Docker-based isolated execution
- No network access (air-gapped)
- Whitelisted packages: pandas, numpy, scipy, scikit-learn, plotly, matplotlib
- Resource limits: 512MB RAM, 30s timeout

## Project Structure (Target)

```
portfolio_agenticAI_autoEDA/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Streamlit entry point
│   ├── ui/
│   │   ├── chat.py             # Chat interface
│   │   ├── context_validator.py
│   │   ├── plan_approval.py
│   │   └── results_explorer.py
│   ├── orchestration/
│   │   ├── planning_agent.py
│   │   ├── uncertainty_scorer.py
│   │   └── hitl_controller.py
│   ├── agents/
│   │   ├── sql_generator.py
│   │   ├── python_analyst.py
│   │   └── visualization.py
│   ├── knowledge/
│   │   ├── semantic_layer.py
│   │   └── rag_system.py
│   └── execution/
│       ├── sandbox.py
│       └── db_manager.py
├── config/
│   ├── semantic_layer.json
│   └── settings.py
├── sandbox/
│   └── Dockerfile
├── tests/
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── CLAUDE.md
```

## Development Guidelines

### Code Style
- Use type hints for all function signatures
- Use Pydantic for data validation
- Follow PEP 8 conventions
- Docstrings for public functions

### Security Requirements
- Sandboxed code execution (no filesystem/network access)
- SQL injection prevention (parameterized queries only)
- Code validation before execution (reject eval, exec, __import__)
- No network libraries in sandbox (requests, urllib, socket)

### Error Handling
- Graceful degradation when LLM API unavailable
- Auto-retry on transient errors (max 3 attempts)
- Plain language error messages (no technical jargon for users)

## Key Configurations

### Environment Variables
```bash
# LLM API
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_GPT4_DEPLOYMENT=gpt-4-turbo
AZURE_GPT35_DEPLOYMENT=gpt-35-turbo

# Fallback
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=anthropic/claude-3-sonnet

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=analytics_db
POSTGRES_USER=analyst
POSTGRES_PASSWORD=secure_password

# Application
UNCERTAINTY_THRESHOLD=0.95
MAX_SANDBOX_TIMEOUT=30
MAX_UPLOAD_SIZE_MB=100
CACHE_ENABLED=true
CHROMA_PERSIST_DIR=./chroma_db
LOG_LEVEL=INFO
```

### Semantic Layer Schema
Metrics, dimensions, relationships, and business rules defined in JSON.
See `config/semantic_layer.json` for structure.

## Database Schema

### Core Tables
- `conversations` - User queries, parsed intents, plans, status
- `clarifications` - Questions asked, user responses
- `feedback` - Ratings, accuracy, helpfulness
- `execution_logs` - Task execution details, timing, errors

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and services
docker-compose up -d

# Run the Streamlit app
streamlit run app/main.py

# Run tests
pytest tests/ -v

# Build sandbox image
docker build -t analytics-sandbox:latest ./sandbox
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Query response (cached) | < 2s P95 |
| Query response (uncached) | < 10s P95 |
| UI responsiveness | < 100ms |
| Sandbox startup | < 2s |
| Context embedding | < 5s for 10 pages |

## Success Metrics

| Metric | Target |
|--------|--------|
| Query Accuracy | > 90% |
| Clarification Precision | < 15% false positives |
| Context Gap Detection | > 85% recall |
| User Satisfaction | > 4.2/5.0 |

## Implementation Phases

1. **Phase 1 (Weeks 1-3)**: Foundation - data ingestion, basic query execution
2. **Phase 2 (Weeks 4-5)**: Context validation & RAG
3. **Phase 3 (Weeks 6-7)**: Uncertainty scoring & HITL
4. **Phase 4 (Weeks 8-9)**: Hierarchical planning & approval
5. **Phase 5 (Weeks 10-11)**: Sandboxed Python execution
6. **Phase 6 (Week 12)**: Visualization & polish

## Testing Requirements

- Unit tests for core components (>80% coverage)
- Integration tests for end-to-end flows
- Security audit for sandbox escapes
- Performance benchmarking

## References

- Primary PRD: `agentic_analyst_prd.md`
- Research: `compass_artifact_wf-*.md`
