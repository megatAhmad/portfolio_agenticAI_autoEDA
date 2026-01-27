"""Uncertainty Scorer for evaluating query confidence."""

import logging
from typing import Any, Optional

import numpy as np
from pydantic import BaseModel, Field

from app.knowledge.semantic_layer import SemanticLayer
from app.orchestration.planning_agent import ParsedIntent

logger = logging.getLogger(__name__)


class UncertaintyBreakdown(BaseModel):
    """Detailed breakdown of uncertainty scores."""

    data_completeness: float = Field(ge=0, le=1)
    schema_confidence: float = Field(ge=0, le=1)
    query_confidence: float = Field(ge=0, le=1)
    overall: float = Field(ge=0, le=1)


class UncertaintyResult(BaseModel):
    """Result of uncertainty evaluation."""

    score: float = Field(ge=0, le=1)
    breakdown: UncertaintyBreakdown
    needs_clarification: bool
    reasons: list[str] = Field(default_factory=list)
    suggested_questions: list[dict[str, Any]] = Field(default_factory=list)


class UncertaintyScorer:
    """Evaluates uncertainty/confidence for query execution."""

    def __init__(
        self,
        threshold: float = 0.95,
        data_weight: float = 0.35,
        schema_weight: float = 0.35,
        query_weight: float = 0.30,
    ):
        """Initialize Uncertainty Scorer.

        Args:
            threshold: Confidence threshold for proceeding without clarification
            data_weight: Weight for data completeness score
            schema_weight: Weight for schema confidence score
            query_weight: Weight for query confidence score
        """
        self.threshold = threshold
        self.data_weight = data_weight
        self.schema_weight = schema_weight
        self.query_weight = query_weight

    def calculate_data_completeness(
        self,
        data_profile: dict[str, Any],
        required_columns: list[str],
    ) -> tuple[float, list[str]]:
        """Calculate data completeness score.

        Args:
            data_profile: Profile of the data with null rates
            required_columns: Columns needed for the query

        Returns:
            Tuple of (score, list of issues)
        """
        issues = []

        if not data_profile or "columns" not in data_profile:
            return 0.5, ["Data profile not available"]

        columns = data_profile.get("columns", {})

        if not required_columns:
            # Calculate average null rate across all columns
            null_rates = [
                col_info.get("null_rate", 0)
                for col_info in columns.values()
            ]
            if null_rates:
                avg_null_rate = np.mean(null_rates)
                score = 1 - avg_null_rate
            else:
                score = 0.8
            return score, issues

        # Check required columns
        null_rates = []
        for col in required_columns:
            col_lower = col.lower()
            matched = False

            for col_name, col_info in columns.items():
                if col_lower == col_name.lower():
                    null_rate = col_info.get("null_rate", 0)
                    null_rates.append(null_rate)
                    matched = True

                    if null_rate > 0.1:
                        issues.append(f"Column '{col}' has {null_rate:.0%} missing values")
                    break

            if not matched:
                issues.append(f"Required column '{col}' not found in data")
                null_rates.append(1.0)  # Treat as completely missing

        score = 1 - np.mean(null_rates) if null_rates else 0.5
        return max(0, min(1, score)), issues

    def calculate_schema_confidence(
        self,
        parsed_intent: ParsedIntent,
        semantic_layer: SemanticLayer,
    ) -> tuple[float, list[str], list[dict[str, Any]]]:
        """Calculate schema mapping confidence.

        Args:
            parsed_intent: Parsed query intent
            semantic_layer: Semantic layer for term resolution

        Returns:
            Tuple of (score, issues, suggested questions)
        """
        issues = []
        questions = []

        if not semantic_layer.config:
            return 0.5, ["Semantic layer not configured"], questions

        total_terms = 0
        matched_terms = 0
        ambiguous_terms = []

        # Check metrics
        for metric in parsed_intent.metrics:
            total_terms += 1
            matches = semantic_layer.find_matching_metrics(metric)

            if len(matches) == 1:
                matched_terms += 1
            elif len(matches) > 1:
                # Ambiguous - multiple matches
                ambiguous_terms.append((metric, "metric", matches))
                matched_terms += 0.5  # Partial credit
            else:
                issues.append(f"Metric '{metric}' not found in semantic layer")

        # Check dimensions
        for dimension in parsed_intent.dimensions:
            total_terms += 1
            matches = semantic_layer.find_matching_dimensions(dimension)

            if len(matches) == 1:
                matched_terms += 1
            elif len(matches) > 1:
                ambiguous_terms.append((dimension, "dimension", matches))
                matched_terms += 0.5
            else:
                issues.append(f"Dimension '{dimension}' not found in semantic layer")

        # Generate questions for ambiguous terms
        for term, term_type, matches in ambiguous_terms:
            options = [
                {
                    "value": m.name,
                    "label": f"{m.display_name}: {m.description[:50]}..."
                    if len(m.description) > 50 else f"{m.display_name}: {m.description}"
                }
                for m in matches[:5]  # Limit to 5 options
            ]

            questions.append({
                "type": "multiple_choice",
                "text": f"Which '{term}' {term_type} did you mean?",
                "term": term,
                "term_type": term_type,
                "options": options,
            })

            issues.append(f"Term '{term}' matches multiple {term_type}s")

        score = matched_terms / total_terms if total_terms > 0 else 1.0
        return max(0, min(1, score)), issues, questions

    def calculate_query_confidence(
        self,
        parsed_intent: ParsedIntent,
    ) -> tuple[float, list[str]]:
        """Get query interpretation confidence from parsed intent.

        Args:
            parsed_intent: Parsed query intent

        Returns:
            Tuple of (score, issues)
        """
        issues = []
        score = parsed_intent.confidence

        # Add issues from ambiguities
        for ambiguity in parsed_intent.ambiguities:
            issues.append(ambiguity)

        # Penalize if no metrics identified
        if not parsed_intent.metrics:
            score *= 0.8
            issues.append("No specific metrics identified in query")

        # Penalize if action is unclear
        if parsed_intent.action == "query" and not parsed_intent.dimensions:
            score *= 0.9
            issues.append("Query intent unclear - no grouping dimensions specified")

        return max(0, min(1, score)), issues

    def evaluate(
        self,
        parsed_intent: ParsedIntent,
        semantic_layer: SemanticLayer,
        data_profile: Optional[dict[str, Any]] = None,
    ) -> UncertaintyResult:
        """Evaluate overall uncertainty for a query.

        Args:
            parsed_intent: Parsed query intent
            semantic_layer: Semantic layer for validation
            data_profile: Data profile with statistics

        Returns:
            UncertaintyResult with scores and recommendations
        """
        all_issues = []
        all_questions = []

        # Calculate data completeness
        required_cols = parsed_intent.metrics + parsed_intent.dimensions
        data_score, data_issues = self.calculate_data_completeness(
            data_profile or {}, required_cols
        )
        all_issues.extend(data_issues)

        # Calculate schema confidence
        schema_score, schema_issues, schema_questions = self.calculate_schema_confidence(
            parsed_intent, semantic_layer
        )
        all_issues.extend(schema_issues)
        all_questions.extend(schema_questions)

        # Calculate query confidence
        query_score, query_issues = self.calculate_query_confidence(parsed_intent)
        all_issues.extend(query_issues)

        # Calculate weighted overall score
        overall_score = (
            self.data_weight * data_score +
            self.schema_weight * schema_score +
            self.query_weight * query_score
        )

        breakdown = UncertaintyBreakdown(
            data_completeness=data_score,
            schema_confidence=schema_score,
            query_confidence=query_score,
            overall=overall_score,
        )

        needs_clarification = overall_score < self.threshold

        # Add time period clarification if needed
        if parsed_intent.time_period is None and any(
            word in " ".join(parsed_intent.filters).lower()
            for word in ["last", "previous", "this", "current"]
        ):
            all_questions.append({
                "type": "multiple_choice",
                "text": "Which time period should I use?",
                "term": "time_period",
                "term_type": "filter",
                "options": [
                    {"value": "last_quarter", "label": "Last Quarter"},
                    {"value": "last_month", "label": "Last Month"},
                    {"value": "ytd", "label": "Year to Date"},
                    {"value": "last_30_days", "label": "Last 30 Days"},
                ],
            })

        return UncertaintyResult(
            score=overall_score,
            breakdown=breakdown,
            needs_clarification=needs_clarification,
            reasons=all_issues,
            suggested_questions=all_questions,
        )

    def recalculate_with_clarifications(
        self,
        original_result: UncertaintyResult,
        clarifications: dict[str, str],
    ) -> UncertaintyResult:
        """Recalculate uncertainty after user clarifications.

        Args:
            original_result: Original uncertainty result
            clarifications: Dictionary of clarified values

        Returns:
            Updated UncertaintyResult
        """
        # Remove questions that have been answered
        remaining_questions = [
            q for q in original_result.suggested_questions
            if q.get("term") not in clarifications
        ]

        # Recalculate scores
        # Assume clarifications improve schema confidence
        improvement = len(clarifications) * 0.1

        new_schema_score = min(1.0, original_result.breakdown.schema_confidence + improvement)

        new_overall = (
            self.data_weight * original_result.breakdown.data_completeness +
            self.schema_weight * new_schema_score +
            self.query_weight * original_result.breakdown.query_confidence
        )

        # Remove clarified issues
        remaining_issues = [
            issue for issue in original_result.reasons
            if not any(term in issue for term in clarifications.keys())
        ]

        return UncertaintyResult(
            score=new_overall,
            breakdown=UncertaintyBreakdown(
                data_completeness=original_result.breakdown.data_completeness,
                schema_confidence=new_schema_score,
                query_confidence=original_result.breakdown.query_confidence,
                overall=new_overall,
            ),
            needs_clarification=new_overall < self.threshold,
            reasons=remaining_issues,
            suggested_questions=remaining_questions,
        )

    def format_for_display(self, result: UncertaintyResult) -> str:
        """Format uncertainty result for user display.

        Args:
            result: Uncertainty result

        Returns:
            Formatted string
        """
        lines = [
            f"Confidence Score: {result.score:.0%}",
            "",
            "Score Breakdown:",
            f"  - Data Completeness: {result.breakdown.data_completeness:.0%}",
            f"  - Schema Confidence: {result.breakdown.schema_confidence:.0%}",
            f"  - Query Confidence: {result.breakdown.query_confidence:.0%}",
        ]

        if result.reasons:
            lines.append("")
            lines.append("Issues Identified:")
            for reason in result.reasons[:5]:  # Limit to 5
                lines.append(f"  - {reason}")

        if result.needs_clarification:
            lines.append("")
            lines.append(f"⚠️ Confidence below {self.threshold:.0%} threshold - clarification recommended")

        return "\n".join(lines)
