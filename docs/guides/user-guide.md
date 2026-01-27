# User Guide

> Step-by-step guide to using Agentic Data Analyst

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Uploading Data](#uploading-data)
3. [Adding Business Context](#adding-business-context)
4. [Asking Questions](#asking-questions)
5. [Understanding Clarifications](#understanding-clarifications)
6. [Reviewing Execution Plans](#reviewing-execution-plans)
7. [Exploring Results](#exploring-results)
8. [Providing Feedback](#providing-feedback)
9. [Tips & Best Practices](#tips--best-practices)

---

## Getting Started

### Launching the Application

```bash
# Start the application
streamlit run app/main.py

# Opens in browser at http://localhost:8501
```

### Interface Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AGENTIC DATA ANALYST                                                        │
├─────────────────┬───────────────────────────────────────────────────────────┤
│                 │                                                           │
│   S I D E B A R │              M A I N   C H A T   A R E A                  │
│                 │                                                           │
│  ┌───────────┐  │  ┌─────────────────────────────────────────────────────┐  │
│  │ Data      │  │  │                                                     │  │
│  │ Upload    │  │  │  Welcome! Upload data and ask questions about it.   │  │
│  │ [Browse]  │  │  │                                                     │  │
│  └───────────┘  │  │  You: What was our revenue last quarter?            │  │
│                 │  │                                                     │  │
│  ┌───────────┐  │  │  AI: I need some clarification...                   │  │
│  │ Business  │  │  │      Which revenue metric did you mean?             │  │
│  │ Context   │  │  │      ○ Total Revenue                                │  │
│  │ [Browse]  │  │  │      ○ Net Revenue                                  │  │
│  └───────────┘  │  │                                                     │  │
│                 │  │  [Results displayed here]                           │  │
│  ┌───────────┐  │  │                                                     │  │
│  │ Settings  │  │  └─────────────────────────────────────────────────────┘  │
│  │           │  │                                                           │
│  │ Threshold │  │  ┌─────────────────────────────────────────────────────┐  │
│  │ [0.95]    │  │  │ Ask a question about your data...              [▶] │  │
│  └───────────┘  │  └─────────────────────────────────────────────────────┘  │
│                 │                                                           │
│  Status:        │                                                           │
│  Data: ✅       │                                                           │
│  Context: ⚠️    │                                                           │
│                 │                                                           │
└─────────────────┴───────────────────────────────────────────────────────────┘
```

---

## Uploading Data

### Supported Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| CSV | `.csv` | Comma-separated values |
| Excel | `.xlsx`, `.xls` | Multiple sheets supported |

### Upload Process

```
Step 1: Click "Upload data file" in sidebar
        ↓
Step 2: Select your file (max 100MB)
        ↓
Step 3: Wait for processing
        ↓
Step 4: See confirmation:
        "Data loaded: 10,000 rows, 15 columns"
```

### Data Requirements

```
✅ GOOD DATA:
   • Clean column headers (no special characters)
   • Consistent data types per column
   • Reasonable file size (< 100MB recommended)

⚠️ POTENTIAL ISSUES:
   • Missing values (system will flag these)
   • Mixed data types in columns
   • Very wide tables (100+ columns)

❌ NOT SUPPORTED:
   • PDF files
   • Images
   • Password-protected files
```

### Example: Loading Sales Data

```
1. Prepare your file: sales_2024.csv

   ┌──────────┬─────────┬──────────┬────────────┐
   │ order_id │ region  │ revenue  │ order_date │
   ├──────────┼─────────┼──────────┼────────────┤
   │ 1001     │ North   │ 1500.00  │ 2024-01-15 │
   │ 1002     │ South   │ 2300.00  │ 2024-01-16 │
   │ ...      │ ...     │ ...      │ ...        │
   └──────────┴─────────┴──────────┴────────────┘

2. Upload via sidebar

3. Confirmation appears:
   ✅ Data loaded: 50,000 rows, 4 columns
```

---

## Adding Business Context

### Why Add Context?

```
WITHOUT CONTEXT:
  Query: "Show me sales"
  AI: "Which column is sales? revenue? amount? total?"

  Confidence: 62% → CLARIFICATION NEEDED

WITH CONTEXT:
  Query: "Show me sales"
  AI: "I understand 'sales' = revenue column"

  Confidence: 95% → PROCEED AUTOMATICALLY
```

### Context File Types

#### JSON Business Glossary

```json
{
  "metrics": [
    {
      "name": "revenue",
      "synonyms": ["sales", "income", "total"],
      "description": "Net order amount after discounts"
    }
  ],
  "dimensions": [
    {
      "name": "region",
      "values": ["North", "South", "East", "West"]
    }
  ]
}
```

#### Text Documents

```text
Business Definitions Document
=============================

Revenue Calculation:
Revenue is calculated as the sum of all order amounts
after applying discounts but before shipping costs.

Regional Structure:
- North: US & Canada
- South: Mexico & Latin America
- East: Europe & Africa
- West: Asia Pacific
```

### Uploading Context

```
1. Click "Upload context files" in sidebar
2. Select one or more files (.txt, .json)
3. Files are processed and embedded
4. Status updates to: Context: ✅
```

---

## Asking Questions

### Question Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SUPPORTED QUESTION TYPES                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  📊 AGGREGATION QUERIES                                                      │
│     "What was the total revenue last quarter?"                               │
│     "How many orders did we have in January?"                                │
│     "What's the average order value by region?"                              │
│                                                                              │
│  📈 TREND ANALYSIS                                                           │
│     "Show me revenue trends over the past year"                              │
│     "How has customer count changed monthly?"                                │
│                                                                              │
│  🔍 COMPARATIVE ANALYSIS                                                     │
│     "Compare North vs South region performance"                              │
│     "Which product category grew fastest?"                                   │
│                                                                              │
│  📉 DISTRIBUTION ANALYSIS                                                    │
│     "Show the distribution of order values"                                  │
│     "What's the breakdown of sales by category?"                             │
│                                                                              │
│  🎯 FILTERING QUERIES                                                        │
│     "Show orders over $1000 from California"                                 │
│     "List top 10 customers by revenue"                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Query Examples

```
SIMPLE QUERIES:
├── "What was our revenue last month?"
├── "How many customers do we have?"
└── "Show me sales by region"

COMPLEX QUERIES:
├── "Compare Q1 vs Q2 revenue by product category and show percentage change"
├── "What's the trend of average order value over the past 6 months by region?"
└── "Find customers who haven't ordered in 90 days but had > $1000 lifetime value"

VISUALIZATION REQUESTS:
├── "Create a bar chart of revenue by region"
├── "Show me a trend line of monthly sales"
└── "Visualize customer distribution by segment"
```

### How the System Processes Your Query

```
                    Your Question
                         │
                         ▼
              ┌──────────────────┐
              │   Parse Intent   │
              │                  │
              │  What metrics?   │
              │  What dimensions?│
              │  What time range?│
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  Score Confidence│
              │                  │
              │  Data: 90%       │
              │  Schema: 85%     │
              │  Query: 88%      │
              │  ─────────────── │
              │  Overall: 88%    │
              └────────┬─────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
     < 95%?│                       │>= 95%
           │                       │
           ▼                       ▼
   ┌───────────────┐      ┌───────────────┐
   │   Clarify     │      │    Create     │
   │   Questions   │      │    Plan       │
   └───────────────┘      └───────────────┘
```

---

## Understanding Clarifications

### When Clarifications Appear

Clarifications are requested when the system's confidence is below 95%:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ⚠️  I need some clarification before proceeding                             │
│                                                                              │
│  Confidence: 78%                                                             │
│                                                                              │
│  ───────────────────────────────────────────────────────────────────────────│
│                                                                              │
│  1. Which "sales" metric did you mean?                                       │
│                                                                              │
│     ○ Total Revenue: Sum of all order amounts after discounts                │
│     ○ Net Sales: Revenue minus returns and refunds                           │
│     ○ Gross Sales: Total before any deductions                               │
│                                                                              │
│  2. Which time period should I use?                                          │
│                                                                              │
│     ○ Last Quarter (Oct-Dec 2024)                                            │
│     ○ Last Month (December 2024)                                             │
│     ○ Year to Date (Jan-Dec 2024)                                            │
│     ○ Last 30 Days                                                           │
│                                                                              │
│  ───────────────────────────────────────────────────────────────────────────│
│                                                                              │
│  [Submit]                                              [Skip Clarification]  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Question Types

| Type | Example | How to Answer |
|------|---------|---------------|
| **Multiple Choice** | "Which metric?" | Click one option |
| **Open Ended** | "Describe the filter" | Type your answer |
| **Confirmation** | "Proceed with X?" | Yes/No |

### System Learning

```
When you answer a clarification question, the system LEARNS:

Before: "sales" → ??? (unknown)
After:  "sales" → "Net Sales" (learned from your answer)

Next time you ask about "sales",
the system will automatically use "Net Sales"
without asking again!
```

---

## Reviewing Execution Plans

### Plan Display

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ═══════════════════════════════════════════════════════════════════════════│
│  EXECUTION PLAN APPROVAL REQUEST                                             │
│  ═══════════════════════════════════════════════════════════════════════════│
│                                                                              │
│  Objective: Analyze total revenue by region for last quarter                 │
│  Confidence: 96%                                                             │
│                                                                              │
│  Tasks to Execute:                                                           │
│                                                                              │
│    ☐ 1. [SQL] Query database for revenue by region for Q4 2024      [2s]    │
│         └─ depends on: none                                                  │
│                                                                              │
│    ☐ 2. [Analysis] Calculate totals and percentages                 [5s]    │
│         └─ depends on: task 1                                                │
│                                                                              │
│    ☐ 3. [Visualization] Create bar chart of regional revenue        [3s]    │
│         └─ depends on: task 1                                                │
│                                                                              │
│    ☐ 4. [Synthesis] Generate summary of findings                    [4s]    │
│         └─ depends on: tasks 2, 3                                            │
│                                                                              │
│  ───────────────────────────────────────────────────────────────────────────│
│                                                                              │
│  Estimated total time: ~14 seconds                                           │
│                                                                              │
│  [✓ Approve]    [✗ Reject]    [Modify Tasks]                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Modifying Plans

You can remove tasks before approving:

```
Example: Skip visualization

Original Plan:
  1. SQL Query ✓
  2. Analysis ✓
  3. Visualization ← REMOVE
  4. Synthesis ✓

Modified Plan:
  1. SQL Query
  2. Analysis
  3. Synthesis (now depends on task 2 only)
```

### Approval Actions

| Action | Effect |
|--------|--------|
| **Approve** | Execute all tasks in order |
| **Approve with Modifications** | Execute selected tasks only |
| **Reject** | Cancel and optionally provide reason |

---

## Exploring Results

### Results Interface

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [Data]  [Visualization]  [Summary]  [Code]                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DATA TAB                                                                    │
│  ────────                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Region   │ Total Revenue  │ % of Total │ Order Count │ Avg Order   │    │
│  ├──────────┼────────────────┼────────────┼─────────────┼─────────────┤    │
│  │ North    │ $2,450,000     │ 35%        │ 12,500      │ $196        │    │
│  │ South    │ $1,890,000     │ 27%        │ 9,800       │ $193        │    │
│  │ East     │ $1,540,000     │ 22%        │ 8,200       │ $188        │    │
│  │ West     │ $1,120,000     │ 16%        │ 5,500       │ $204        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Rows: 4  │  Columns: 5  │  Size: 1.2 KB                                    │
│                                                                              │
│  Export: [CSV]  [Excel]  [JSON]                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tab Contents

| Tab | Contents |
|-----|----------|
| **Data** | Interactive table with sorting, filtering, pagination |
| **Visualization** | Interactive Plotly charts (hover, zoom, download) |
| **Summary** | Natural language insights about the data |
| **Code** | SQL queries and Python code used |

### Export Options

```
┌────────────────────────────────────────────┐
│  EXPORT OPTIONS                            │
├────────────────────────────────────────────┤
│                                            │
│  Data:                                     │
│    [Download CSV]                          │
│    [Download Excel]                        │
│    [Download JSON]                         │
│                                            │
│  Charts:                                   │
│    [Download as HTML]                      │
│    [Download as PNG] (if available)        │
│                                            │
└────────────────────────────────────────────┘
```

---

## Providing Feedback

### Feedback Interface

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FEEDBACK                                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  How helpful was this result?                                                │
│                                                                              │
│  [1] [2] [3] [4] [5]                                                         │
│   😞      😐      😊                                                          │
│                                                                              │
│  Was the result accurate?                                                    │
│                                                                              │
│  ○ Yes   ○ No   ○ Not sure                                                   │
│                                                                              │
│  Additional comments (optional):                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ The regional breakdown was exactly what I needed, but I expected    │    │
│  │ to see month-over-month comparison as well.                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  [Submit Feedback]                                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Feedback Matters

```
Your feedback helps:

1. IMPROVE ACCURACY
   If you mark results as inaccurate, we can identify
   issues with SQL generation or data interpretation

2. TRAIN THE SYSTEM
   Positive feedback reinforces good patterns
   Negative feedback triggers review

3. IDENTIFY GAPS
   Comments help us understand missing features
   or unclear documentation
```

---

## Tips & Best Practices

### Writing Effective Questions

```
✅ GOOD QUESTIONS:

  "What was the total revenue by region for Q4 2024?"
   └─ Specific metric, dimension, and time period

  "Compare monthly sales trends for North vs South regions"
   └─ Clear comparison with temporal dimension

  "Show top 10 customers by lifetime value"
   └─ Specific ranking and metric


❌ VAGUE QUESTIONS:

  "Show me everything"
   └─ Too broad, no specific intent

  "What's happening with sales?"
   └─ Unclear what aspect to analyze

  "Is it good?"
   └─ Subjective, no measurable criteria
```

### Optimizing Performance

```
FASTER RESULTS:
│
├── Use specific time ranges instead of "all time"
│
├── Limit dimensions (2-3 max) in a single query
│
├── Filter large datasets before visualization
│
└── Use cached results when available
```

### When to Add Context

```
ADD CONTEXT WHEN:
│
├── You have business-specific terminology
│   (e.g., "active customer" = ordered in last 90 days)
│
├── You have calculations that aren't obvious
│   (e.g., "revenue" = after discounts and returns)
│
├── You have regional or categorical mappings
│   (e.g., "APAC" includes Japan, Korea, etc.)
│
└── You're getting too many clarification questions
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "Confidence too low" | Add more business context |
| "Column not found" | Check column names in your data |
| "Execution timeout" | Break into smaller queries |
| "No visualization" | Ensure data has numeric columns |
| "Wrong results" | Review generated SQL in Code tab |

---

## Next Steps

- [API Reference](../api/README.md) - For developers
- [Architecture Guide](./architecture.md) - System design deep dive
- [Examples](./examples.md) - More use case examples
