"""Semantic layer management for metrics, dimensions, and business rules."""

import json
import logging
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Metric(BaseModel):
    """Definition of a business metric."""

    name: str
    display_name: str
    description: str
    sql: str
    aggregation: str = "sum"
    format: str = "number"
    synonyms: list[str] = Field(default_factory=list)
    sample_queries: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)


class Dimension(BaseModel):
    """Definition of a data dimension."""

    name: str
    display_name: str
    column: str
    type: str  # 'categorical', 'datetime', 'numeric'
    description: str = ""
    sample_values: list[str] = Field(default_factory=list)
    granularities: list[str] = Field(default_factory=list)
    hierarchies: list[str] = Field(default_factory=list)
    synonyms: list[str] = Field(default_factory=list)


class Relationship(BaseModel):
    """Definition of a table relationship."""

    from_table: str
    to_table: str
    join_type: str = "left"
    on: str
    description: str = ""


class BusinessRule(BaseModel):
    """Definition of a business rule/filter."""

    name: str
    applies_to: str | list[str]
    filter: str
    description: str = ""


class TimePeriod(BaseModel):
    """Definition of a time period."""

    description: str
    sql_template: str


class SemanticLayerConfig(BaseModel):
    """Complete semantic layer configuration."""

    version: str = "1.0"
    last_updated: str = ""
    metrics: list[Metric] = Field(default_factory=list)
    dimensions: list[Dimension] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    business_rules: list[BusinessRule] = Field(default_factory=list)
    time_periods: dict[str, TimePeriod] = Field(default_factory=dict)


class SemanticLayer:
    """Manages semantic layer configuration and term resolution."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize semantic layer.

        Args:
            config_path: Path to semantic layer JSON configuration
        """
        self.config_path = config_path
        self.config: Optional[SemanticLayerConfig] = None
        self._synonym_index: dict[str, tuple[str, str]] = {}  # term -> (type, name)

        if config_path and config_path.exists():
            self.load_config(config_path)

    def load_config(self, config_path: Path) -> None:
        """Load semantic layer configuration from JSON file.

        Args:
            config_path: Path to configuration file
        """
        with open(config_path) as f:
            data = json.load(f)

        self.config = SemanticLayerConfig(**data)
        self._build_synonym_index()
        logger.info(f"Loaded semantic layer with {len(self.config.metrics)} metrics, "
                    f"{len(self.config.dimensions)} dimensions")

    def _build_synonym_index(self) -> None:
        """Build index for quick synonym lookup."""
        self._synonym_index = {}

        if not self.config:
            return

        # Index metrics
        for metric in self.config.metrics:
            self._synonym_index[metric.name.lower()] = ("metric", metric.name)
            self._synonym_index[metric.display_name.lower()] = ("metric", metric.name)
            for syn in metric.synonyms:
                self._synonym_index[syn.lower()] = ("metric", metric.name)

        # Index dimensions
        for dim in self.config.dimensions:
            self._synonym_index[dim.name.lower()] = ("dimension", dim.name)
            self._synonym_index[dim.display_name.lower()] = ("dimension", dim.name)
            self._synonym_index[dim.column.lower()] = ("dimension", dim.name)
            for syn in dim.synonyms:
                self._synonym_index[syn.lower()] = ("dimension", dim.name)

    def resolve_term(self, term: str) -> Optional[tuple[str, str]]:
        """Resolve a term to its canonical metric or dimension.

        Args:
            term: User term to resolve

        Returns:
            Tuple of (type, canonical_name) or None if not found
        """
        return self._synonym_index.get(term.lower())

    def find_matching_metrics(self, term: str) -> list[Metric]:
        """Find all metrics that might match a term.

        Args:
            term: Search term

        Returns:
            List of matching metrics
        """
        if not self.config:
            return []

        term_lower = term.lower()
        matches = []

        for metric in self.config.metrics:
            if (term_lower in metric.name.lower() or
                term_lower in metric.display_name.lower() or
                any(term_lower in syn.lower() for syn in metric.synonyms)):
                matches.append(metric)

        return matches

    def find_matching_dimensions(self, term: str) -> list[Dimension]:
        """Find all dimensions that might match a term.

        Args:
            term: Search term

        Returns:
            List of matching dimensions
        """
        if not self.config:
            return []

        term_lower = term.lower()
        matches = []

        for dim in self.config.dimensions:
            if (term_lower in dim.name.lower() or
                term_lower in dim.display_name.lower() or
                term_lower in dim.column.lower() or
                any(term_lower in syn.lower() for syn in dim.synonyms)):
                matches.append(dim)

        return matches

    def get_metric(self, name: str) -> Optional[Metric]:
        """Get metric by name.

        Args:
            name: Metric name

        Returns:
            Metric or None
        """
        if not self.config:
            return None

        for metric in self.config.metrics:
            if metric.name == name:
                return metric
        return None

    def get_dimension(self, name: str) -> Optional[Dimension]:
        """Get dimension by name.

        Args:
            name: Dimension name

        Returns:
            Dimension or None
        """
        if not self.config:
            return None

        for dim in self.config.dimensions:
            if dim.name == name:
                return dim
        return None

    def get_applicable_rules(self, metric_names: list[str]) -> list[BusinessRule]:
        """Get business rules applicable to given metrics.

        Args:
            metric_names: List of metric names

        Returns:
            List of applicable business rules
        """
        if not self.config:
            return []

        applicable = []
        for rule in self.config.business_rules:
            applies_to = rule.applies_to
            if isinstance(applies_to, str):
                if applies_to == "all_metrics" or applies_to in metric_names:
                    applicable.append(rule)
            else:
                if any(m in metric_names for m in applies_to):
                    applicable.append(rule)

        return applicable

    def get_relationship(self, from_table: str, to_table: str) -> Optional[Relationship]:
        """Get relationship between two tables.

        Args:
            from_table: Source table
            to_table: Target table

        Returns:
            Relationship or None
        """
        if not self.config:
            return None

        for rel in self.config.relationships:
            if rel.from_table == from_table and rel.to_table == to_table:
                return rel
        return None

    def resolve_time_period(self, period_name: str) -> Optional[str]:
        """Resolve time period name to SQL.

        Args:
            period_name: Time period name (e.g., 'last_quarter')

        Returns:
            SQL template or None
        """
        if not self.config:
            return None

        period = self.config.time_periods.get(period_name)
        return period.sql_template if period else None

    def add_synonym(self, term: str, canonical_name: str, term_type: str) -> None:
        """Add a new synonym mapping.

        Args:
            term: New synonym
            canonical_name: Canonical metric/dimension name
            term_type: 'metric' or 'dimension'
        """
        if not self.config:
            return

        self._synonym_index[term.lower()] = (term_type, canonical_name)

        # Update the config
        if term_type == "metric":
            for metric in self.config.metrics:
                if metric.name == canonical_name:
                    if term not in metric.synonyms:
                        metric.synonyms.append(term)
                    break
        elif term_type == "dimension":
            for dim in self.config.dimensions:
                if dim.name == canonical_name:
                    if term not in dim.synonyms:
                        dim.synonyms.append(term)
                    break

    def save_config(self, path: Optional[Path] = None) -> None:
        """Save semantic layer configuration to JSON.

        Args:
            path: Output path (uses original path if not specified)
        """
        if not self.config:
            return

        output_path = path or self.config_path
        if not output_path:
            raise ValueError("No output path specified")

        with open(output_path, "w") as f:
            json.dump(self.config.model_dump(), f, indent=2)

        logger.info(f"Saved semantic layer to {output_path}")

    def get_schema_coverage(self, data_columns: list[str]) -> dict[str, Any]:
        """Calculate how well the semantic layer covers data columns.

        Args:
            data_columns: List of column names from data

        Returns:
            Coverage analysis with mapped and unmapped columns
        """
        if not self.config:
            return {"coverage": 0, "mapped": [], "unmapped": data_columns}

        # Get all column names from dimensions
        dimension_columns = {dim.column.lower() for dim in self.config.dimensions}

        mapped = []
        unmapped = []

        for col in data_columns:
            col_lower = col.lower()
            if col_lower in dimension_columns or col_lower in self._synonym_index:
                mapped.append(col)
            else:
                unmapped.append(col)

        total = len(data_columns)
        coverage = len(mapped) / total if total > 0 else 1.0

        return {
            "coverage": coverage,
            "mapped": mapped,
            "unmapped": unmapped,
            "total_columns": total,
        }

    def generate_context_questions(self, unmapped_columns: list[str]) -> list[dict[str, str]]:
        """Generate questions for unmapped columns.

        Args:
            unmapped_columns: List of column names not in semantic layer

        Returns:
            List of question dictionaries
        """
        questions = []
        for col in unmapped_columns:
            questions.append({
                "column": col,
                "question": f"What does the column '{col}' represent? Please provide a description.",
                "type": "open_ended",
            })
        return questions

    def to_prompt_context(self) -> str:
        """Generate context string for LLM prompts.

        Returns:
            Formatted context string
        """
        if not self.config:
            return "No semantic layer configured."

        lines = ["Available Metrics:"]
        for m in self.config.metrics:
            synonyms = f" (also known as: {', '.join(m.synonyms)})" if m.synonyms else ""
            lines.append(f"- {m.display_name}: {m.description}{synonyms}")

        lines.append("\nAvailable Dimensions:")
        for d in self.config.dimensions:
            synonyms = f" (also known as: {', '.join(d.synonyms)})" if d.synonyms else ""
            lines.append(f"- {d.display_name}: {d.description}{synonyms}")

        lines.append("\nBusiness Rules:")
        for r in self.config.business_rules:
            lines.append(f"- {r.name}: {r.description}")

        return "\n".join(lines)
