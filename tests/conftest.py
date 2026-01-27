"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return [
        {"region": "North", "product": "Widget A", "revenue": 1000, "quantity": 10},
        {"region": "North", "product": "Widget B", "revenue": 1500, "quantity": 15},
        {"region": "South", "product": "Widget A", "revenue": 800, "quantity": 8},
        {"region": "South", "product": "Widget B", "revenue": 1200, "quantity": 12},
    ]


@pytest.fixture
def sample_schema():
    """Sample schema for testing."""
    return {
        "columns": {
            "region": {"type": "object", "nullable": False},
            "product": {"type": "object", "nullable": False},
            "revenue": {"type": "int64", "nullable": False},
            "quantity": {"type": "int64", "nullable": True},
        }
    }


@pytest.fixture
def sample_parsed_intent():
    """Sample parsed intent for testing."""
    return {
        "metrics": ["revenue"],
        "dimensions": ["region"],
        "filters": [],
        "time_range": None,
        "aggregation": "sum",
        "intent_type": "aggregation",
        "confidence": 0.9,
    }


@pytest.fixture
def sample_semantic_config():
    """Sample semantic layer configuration."""
    return {
        "version": "1.0",
        "metrics": [
            {
                "name": "total_revenue",
                "display_name": "Total Revenue",
                "sql": "SUM(revenue)",
                "synonyms": ["sales", "income"],
            }
        ],
        "dimensions": [
            {
                "name": "customer_region",
                "display_name": "Region",
                "column": "region",
                "type": "categorical",
                "synonyms": ["geo", "geography"],
            }
        ],
    }
