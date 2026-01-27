"""Context validator UI component for Streamlit."""

import json
import logging
from pathlib import Path
from typing import Any, Optional

import streamlit as st

logger = logging.getLogger(__name__)


class ContextValidatorUI:
    """UI component for validating business context."""

    def __init__(self, key: str = "context"):
        """Initialize context validator UI.

        Args:
            key: Unique key for session state
        """
        self.key = key
        self._init_session_state()

    def _init_session_state(self) -> None:
        """Initialize session state."""
        if f"{self.key}_uploaded_files" not in st.session_state:
            st.session_state[f"{self.key}_uploaded_files"] = []

        if f"{self.key}_validation_result" not in st.session_state:
            st.session_state[f"{self.key}_validation_result"] = None

        if f"{self.key}_context_responses" not in st.session_state:
            st.session_state[f"{self.key}_context_responses"] = {}

    def render_upload_section(self) -> list[Any]:
        """Render file upload section.

        Returns:
            List of uploaded files
        """
        st.subheader("Business Context")

        uploaded_files = st.file_uploader(
            "Upload context files (TXT, JSON)",
            type=["txt", "json"],
            accept_multiple_files=True,
            key=f"{self.key}_uploader",
            help="Upload files that describe your business context, "
                 "column meanings, and metric definitions.",
        )

        if uploaded_files:
            st.session_state[f"{self.key}_uploaded_files"] = uploaded_files
            st.success(f"Uploaded {len(uploaded_files)} file(s)")

            # Preview uploaded files
            with st.expander("Preview Uploaded Context"):
                for file in uploaded_files:
                    st.markdown(f"**{file.name}**")
                    content = file.read().decode("utf-8")
                    file.seek(0)  # Reset for later use

                    if file.name.endswith(".json"):
                        try:
                            data = json.loads(content)
                            st.json(data)
                        except json.JSONDecodeError:
                            st.text(content[:500])
                    else:
                        st.text(content[:500])

                    st.divider()

        return uploaded_files or []

    def render_validation_result(
        self,
        coverage: float,
        mapped_columns: list[str],
        unmapped_columns: list[str],
    ) -> None:
        """Render validation result.

        Args:
            coverage: Coverage percentage (0-1)
            mapped_columns: List of mapped column names
            unmapped_columns: List of unmapped column names
        """
        st.subheader("Context Validation")

        # Coverage meter
        col1, col2 = st.columns([2, 1])

        with col1:
            coverage_pct = coverage * 100
            color = "green" if coverage >= 0.95 else "orange" if coverage >= 0.8 else "red"

            st.metric(
                "Context Coverage",
                f"{coverage_pct:.0f}%",
                delta=f"{coverage_pct - 95:.0f}% from target" if coverage < 0.95 else "Target met!",
            )

            st.progress(coverage)

        with col2:
            st.metric("Mapped Columns", len(mapped_columns))
            st.metric("Unmapped Columns", len(unmapped_columns))

        # Show details
        if mapped_columns:
            with st.expander(f"Mapped Columns ({len(mapped_columns)})", expanded=False):
                for col in mapped_columns:
                    st.markdown(f"✓ {col}")

        if unmapped_columns:
            with st.expander(f"Unmapped Columns ({len(unmapped_columns)})", expanded=True):
                st.warning(
                    "The following columns don't have context definitions. "
                    "Please provide descriptions below."
                )
                for col in unmapped_columns:
                    st.markdown(f"⚠️ {col}")

    def render_context_questions(
        self,
        questions: list[dict[str, str]],
    ) -> dict[str, str]:
        """Render context questions for unmapped columns.

        Args:
            questions: List of question dictionaries

        Returns:
            Dictionary of column -> response
        """
        if not questions:
            return {}

        st.subheader("Additional Context Needed")

        responses = st.session_state[f"{self.key}_context_responses"].copy()

        with st.form(key=f"{self.key}_context_form"):
            for question in questions:
                col = question.get("column", "")
                q_text = question.get("question", f"What does '{col}' represent?")

                response = st.text_area(
                    q_text,
                    key=f"{self.key}_q_{col}",
                    height=80,
                    placeholder=f"Describe what the '{col}' column contains...",
                )

                if response:
                    responses[col] = response

            submitted = st.form_submit_button("Save Context", type="primary")

            if submitted:
                st.session_state[f"{self.key}_context_responses"] = responses
                st.success("Context saved!")

        return responses

    def render_semantic_layer_editor(
        self,
        config: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        """Render semantic layer configuration editor.

        Args:
            config: Current semantic layer config

        Returns:
            Updated config if modified, None otherwise
        """
        st.subheader("Semantic Layer Configuration")

        tabs = st.tabs(["Metrics", "Dimensions", "Relationships", "Business Rules"])

        updated_config = config.copy()
        modified = False

        # Metrics tab
        with tabs[0]:
            st.markdown("**Defined Metrics:**")

            for i, metric in enumerate(config.get("metrics", [])):
                with st.expander(f"{metric.get('display_name', metric.get('name', 'Unknown'))}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.text_input(
                            "Name",
                            value=metric.get("name", ""),
                            key=f"metric_name_{i}",
                            disabled=True,
                        )
                        st.text_area(
                            "Description",
                            value=metric.get("description", ""),
                            key=f"metric_desc_{i}",
                            height=80,
                        )

                    with col2:
                        st.text_input(
                            "SQL Formula",
                            value=metric.get("sql", ""),
                            key=f"metric_sql_{i}",
                        )
                        st.text_input(
                            "Synonyms",
                            value=", ".join(metric.get("synonyms", [])),
                            key=f"metric_syn_{i}",
                            help="Comma-separated list of alternative names",
                        )

        # Dimensions tab
        with tabs[1]:
            st.markdown("**Defined Dimensions:**")

            for i, dim in enumerate(config.get("dimensions", [])):
                with st.expander(f"{dim.get('display_name', dim.get('name', 'Unknown'))}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.text_input(
                            "Name",
                            value=dim.get("name", ""),
                            key=f"dim_name_{i}",
                            disabled=True,
                        )
                        st.text_input(
                            "Column",
                            value=dim.get("column", ""),
                            key=f"dim_col_{i}",
                        )

                    with col2:
                        st.selectbox(
                            "Type",
                            options=["categorical", "datetime", "numeric"],
                            index=["categorical", "datetime", "numeric"].index(
                                dim.get("type", "categorical")
                            ),
                            key=f"dim_type_{i}",
                        )
                        st.text_input(
                            "Synonyms",
                            value=", ".join(dim.get("synonyms", [])),
                            key=f"dim_syn_{i}",
                        )

        # Relationships tab
        with tabs[2]:
            st.markdown("**Table Relationships:**")

            for i, rel in enumerate(config.get("relationships", [])):
                st.markdown(
                    f"• `{rel.get('from_table')}` → `{rel.get('to_table')}` "
                    f"({rel.get('join_type', 'left')} join on `{rel.get('on')}`)"
                )

        # Business Rules tab
        with tabs[3]:
            st.markdown("**Business Rules:**")

            for i, rule in enumerate(config.get("business_rules", [])):
                with st.expander(rule.get("name", f"Rule {i + 1}")):
                    st.markdown(f"**Description:** {rule.get('description', 'N/A')}")
                    st.markdown(f"**Applies to:** {rule.get('applies_to', 'all')}")
                    st.code(rule.get("filter", ""), language="sql")

        return updated_config if modified else None

    def render_coverage_progress(
        self,
        current: float,
        target: float = 0.95,
    ) -> None:
        """Render coverage progress indicator.

        Args:
            current: Current coverage (0-1)
            target: Target coverage (0-1)
        """
        progress = min(current / target, 1.0)

        if current >= target:
            st.success(f"Context coverage target reached! ({current:.0%})")
        else:
            st.warning(
                f"Context coverage: {current:.0%} (target: {target:.0%}). "
                "Please provide more context for better results."
            )

        st.progress(progress)


def render_data_upload_section() -> Optional[Any]:
    """Render data file upload section.

    Returns:
        Uploaded file or None
    """
    st.subheader("Data Upload")

    uploaded_file = st.file_uploader(
        "Upload your data file",
        type=["csv", "xlsx", "xls"],
        help="Upload a CSV or Excel file to analyze",
    )

    if uploaded_file:
        st.success(f"Uploaded: {uploaded_file.name}")

        # Preview data
        import pandas as pd

        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            uploaded_file.seek(0)  # Reset for later use

            with st.expander("Preview Data", expanded=True):
                st.dataframe(df.head(10), use_container_width=True)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Rows", len(df))
                with col2:
                    st.metric("Columns", len(df.columns))
                with col3:
                    st.metric("Size", f"{uploaded_file.size / 1024:.1f} KB")

        except Exception as e:
            st.error(f"Error reading file: {e}")
            return None

    return uploaded_file


def render_schema_summary(schema: dict[str, Any]) -> None:
    """Render data schema summary.

    Args:
        schema: Schema dictionary with column information
    """
    st.subheader("Data Schema")

    columns = schema.get("columns", {})

    if not columns:
        st.info("No schema information available")
        return

    # Create summary table
    import pandas as pd

    schema_df = pd.DataFrame([
        {
            "Column": col,
            "Type": info.get("type", "unknown"),
            "Nullable": "Yes" if info.get("nullable", True) else "No",
            "Null Rate": f"{info.get('null_rate', 0):.1%}" if "null_rate" in info else "N/A",
        }
        for col, info in columns.items()
    ])

    st.dataframe(schema_df, use_container_width=True, hide_index=True)
