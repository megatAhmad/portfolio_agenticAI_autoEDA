"""Tests for the Semantic Layer."""

import json
import tempfile
from pathlib import Path

import pytest

from app.knowledge.semantic_layer import SemanticLayer


class TestSemanticLayer:
    """Test suite for SemanticLayer."""

    @pytest.fixture
    def temp_config_file(self, sample_semantic_config):
        """Create a temporary config file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(sample_semantic_config, f)
            return Path(f.name)

    def test_init_with_config_path(self, temp_config_file):
        """Test initialization with config file path."""
        layer = SemanticLayer(config_path=temp_config_file)
        assert layer is not None
        assert len(layer.metrics) > 0

    def test_get_metric(self, temp_config_file):
        """Test getting a metric by name."""
        layer = SemanticLayer(config_path=temp_config_file)
        metric = layer.get_metric("total_revenue")
        assert metric is not None
        assert metric.name == "total_revenue"

    def test_get_metric_by_synonym(self, temp_config_file):
        """Test getting a metric by synonym."""
        layer = SemanticLayer(config_path=temp_config_file)
        metric = layer.get_metric("sales")
        assert metric is not None
        assert metric.name == "total_revenue"

    def test_get_dimension(self, temp_config_file):
        """Test getting a dimension by name."""
        layer = SemanticLayer(config_path=temp_config_file)
        dimension = layer.get_dimension("customer_region")
        assert dimension is not None
        assert dimension.name == "customer_region"

    def test_get_dimension_by_synonym(self, temp_config_file):
        """Test getting a dimension by synonym."""
        layer = SemanticLayer(config_path=temp_config_file)
        dimension = layer.get_dimension("geo")
        assert dimension is not None
        assert dimension.name == "customer_region"

    def test_resolve_term_metric(self, temp_config_file):
        """Test resolving a term to a metric."""
        layer = SemanticLayer(config_path=temp_config_file)
        result = layer.resolve_term("revenue")
        assert result is not None
        assert result["type"] == "metric"

    def test_resolve_term_dimension(self, temp_config_file):
        """Test resolving a term to a dimension."""
        layer = SemanticLayer(config_path=temp_config_file)
        result = layer.resolve_term("region")
        assert result is not None
        assert result["type"] == "dimension"

    def test_resolve_unknown_term(self, temp_config_file):
        """Test resolving an unknown term."""
        layer = SemanticLayer(config_path=temp_config_file)
        result = layer.resolve_term("unknown_metric_xyz")
        assert result is None

    def test_add_synonym(self, temp_config_file):
        """Test adding a synonym to a metric."""
        layer = SemanticLayer(config_path=temp_config_file)
        layer.add_synonym("money", "total_revenue", "metric")

        # Should now resolve
        metric = layer.get_metric("money")
        assert metric is not None
        assert metric.name == "total_revenue"

    def test_to_prompt_context(self, temp_config_file):
        """Test generating prompt context."""
        layer = SemanticLayer(config_path=temp_config_file)
        context = layer.to_prompt_context()

        assert "Total Revenue" in context
        assert "Region" in context
        assert isinstance(context, str)

    def test_list_all_metrics(self, temp_config_file):
        """Test listing all metrics."""
        layer = SemanticLayer(config_path=temp_config_file)
        metrics = layer.list_metrics()

        assert len(metrics) > 0
        assert any(m.name == "total_revenue" for m in metrics)

    def test_list_all_dimensions(self, temp_config_file):
        """Test listing all dimensions."""
        layer = SemanticLayer(config_path=temp_config_file)
        dimensions = layer.list_dimensions()

        assert len(dimensions) > 0
        assert any(d.name == "customer_region" for d in dimensions)
