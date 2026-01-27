"""Tests for the Uncertainty Scorer."""

import pytest

from app.orchestration.uncertainty_scorer import (
    UncertaintyResult,
    UncertaintyScorer,
)


class TestUncertaintyScorer:
    """Test suite for UncertaintyScorer."""

    def test_init_default_threshold(self):
        """Test default threshold initialization."""
        scorer = UncertaintyScorer()
        assert scorer.threshold == 0.95

    def test_init_custom_threshold(self):
        """Test custom threshold initialization."""
        scorer = UncertaintyScorer(threshold=0.8)
        assert scorer.threshold == 0.8

    def test_calculate_data_completeness_full(self):
        """Test data completeness with no null values."""
        scorer = UncertaintyScorer()
        schema = {
            "columns": {
                "id": {"type": "int64", "nullable": False},
                "name": {"type": "object", "nullable": False},
            }
        }
        score = scorer._calculate_data_completeness(schema)
        assert score == 1.0

    def test_calculate_data_completeness_partial(self):
        """Test data completeness with some nullable columns."""
        scorer = UncertaintyScorer()
        schema = {
            "columns": {
                "id": {"type": "int64", "nullable": False},
                "name": {"type": "object", "nullable": True},
            }
        }
        score = scorer._calculate_data_completeness(schema)
        assert score == 0.5

    def test_calculate_data_completeness_no_schema(self):
        """Test data completeness when no schema provided."""
        scorer = UncertaintyScorer()
        score = scorer._calculate_data_completeness(None)
        assert score == 0.5

    def test_needs_clarification_below_threshold(self):
        """Test that clarification is needed when score is below threshold."""
        result = UncertaintyResult(
            score=0.7,
            data_completeness=0.8,
            schema_confidence=0.6,
            query_confidence=0.7,
            needs_clarification=True,
            suggested_questions=[],
        )
        assert result.needs_clarification is True

    def test_no_clarification_above_threshold(self):
        """Test that no clarification needed when score is above threshold."""
        result = UncertaintyResult(
            score=0.98,
            data_completeness=1.0,
            schema_confidence=0.95,
            query_confidence=0.99,
            needs_clarification=False,
            suggested_questions=[],
        )
        assert result.needs_clarification is False


class TestUncertaintyResult:
    """Test suite for UncertaintyResult model."""

    def test_create_result(self):
        """Test creating an UncertaintyResult."""
        result = UncertaintyResult(
            score=0.85,
            data_completeness=0.9,
            schema_confidence=0.8,
            query_confidence=0.85,
            needs_clarification=True,
            suggested_questions=[{"text": "What metric?", "type": "multiple_choice"}],
        )

        assert result.score == 0.85
        assert result.needs_clarification is True
        assert len(result.suggested_questions) == 1

    def test_result_with_ambiguous_terms(self):
        """Test result with ambiguous terms."""
        result = UncertaintyResult(
            score=0.6,
            data_completeness=0.7,
            schema_confidence=0.5,
            query_confidence=0.6,
            needs_clarification=True,
            suggested_questions=[],
            ambiguous_terms=["revenue", "sales"],
        )

        assert len(result.ambiguous_terms) == 2
        assert "revenue" in result.ambiguous_terms
