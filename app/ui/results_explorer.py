"""Results explorer UI component for Streamlit."""

import json
import logging
from io import BytesIO
from typing import Any, Optional

import streamlit as st

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    AGGRID_AVAILABLE = True
except ImportError:
    AGGRID_AVAILABLE = False
    logger.warning("streamlit-aggrid not available, using standard dataframe")


class ResultsExplorerUI:
    """UI component for exploring query results."""

    def __init__(self, key: str = "results"):
        """Initialize results explorer UI.

        Args:
            key: Unique key for session state
        """
        self.key = key
        self._init_session_state()

    def _init_session_state(self) -> None:
        """Initialize session state."""
        if f"{self.key}_data" not in st.session_state:
            st.session_state[f"{self.key}_data"] = None

        if f"{self.key}_chart" not in st.session_state:
            st.session_state[f"{self.key}_chart"] = None

    def render_data_table(
        self,
        data: list[dict[str, Any]],
        title: str = "Results",
        enable_filtering: bool = True,
        enable_sorting: bool = True,
        page_size: int = 20,
    ) -> None:
        """Render interactive data table.

        Args:
            data: Data to display
            title: Table title
            enable_filtering: Enable column filtering
            enable_sorting: Enable column sorting
            page_size: Rows per page
        """
        if not PANDAS_AVAILABLE:
            st.error("Pandas not available")
            return

        df = pd.DataFrame(data)
        st.session_state[f"{self.key}_data"] = df

        st.subheader(title)

        # Summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows", len(df))
        with col2:
            st.metric("Columns", len(df.columns))
        with col3:
            memory = df.memory_usage(deep=True).sum() / 1024
            st.metric("Size", f"{memory:.1f} KB")

        # Render table
        if AGGRID_AVAILABLE and enable_filtering:
            self._render_aggrid_table(df, enable_filtering, enable_sorting, page_size)
        else:
            self._render_standard_table(df)

        # Export options
        self._render_export_options(df)

    def _render_aggrid_table(
        self,
        df: Any,
        enable_filtering: bool,
        enable_sorting: bool,
        page_size: int,
    ) -> None:
        """Render table using AgGrid.

        Args:
            df: DataFrame to display
            enable_filtering: Enable filtering
            enable_sorting: Enable sorting
            page_size: Page size
        """
        gb = GridOptionsBuilder.from_dataframe(df)

        gb.configure_default_column(
            filterable=enable_filtering,
            sortable=enable_sorting,
            resizable=True,
        )

        gb.configure_pagination(
            paginationAutoPageSize=False,
            paginationPageSize=page_size,
        )

        gb.configure_selection(
            selection_mode="multiple",
            use_checkbox=True,
        )

        grid_options = gb.build()

        AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            fit_columns_on_grid_load=True,
            theme="streamlit",
        )

    def _render_standard_table(self, df: Any) -> None:
        """Render table using standard Streamlit dataframe.

        Args:
            df: DataFrame to display
        """
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

    def _render_export_options(self, df: Any) -> None:
        """Render data export options.

        Args:
            df: DataFrame to export
        """
        st.markdown("**Export Data:**")

        col1, col2, col3 = st.columns(3)

        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                file_name="results.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col2:
            # Excel export
            buffer = BytesIO()
            df.to_excel(buffer, index=False, engine="openpyxl")
            buffer.seek(0)

            st.download_button(
                "Download Excel",
                buffer,
                file_name="results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with col3:
            json_str = df.to_json(orient="records", indent=2)
            st.download_button(
                "Download JSON",
                json_str,
                file_name="results.json",
                mime="application/json",
                use_container_width=True,
            )

    def render_chart(
        self,
        chart_html: Optional[str] = None,
        chart_json: Optional[str] = None,
        title: str = "Visualization",
        height: int = 400,
    ) -> None:
        """Render interactive chart.

        Args:
            chart_html: Plotly chart HTML
            chart_json: Plotly chart JSON
            title: Chart title
            height: Chart height in pixels
        """
        st.subheader(title)

        if chart_html:
            st.session_state[f"{self.key}_chart"] = chart_html

            import streamlit.components.v1 as components
            components.html(chart_html, height=height)

            # Export options
            col1, col2 = st.columns(2)

            with col1:
                st.download_button(
                    "Download Chart HTML",
                    chart_html,
                    file_name="chart.html",
                    mime="text/html",
                    use_container_width=True,
                )

            with col2:
                if chart_json:
                    st.download_button(
                        "Download Chart JSON",
                        chart_json,
                        file_name="chart.json",
                        mime="application/json",
                        use_container_width=True,
                    )

        elif chart_json:
            # Render from JSON using Plotly
            try:
                import plotly.io as pio

                fig = pio.from_json(chart_json)
                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Failed to render chart: {e}")

        else:
            st.info("No visualization available")

    def render_summary(
        self,
        summary: str,
        title: str = "Summary",
    ) -> None:
        """Render natural language summary.

        Args:
            summary: Summary text
            title: Section title
        """
        st.subheader(title)
        st.markdown(summary)

    def render_statistics(
        self,
        data: list[dict[str, Any]],
    ) -> None:
        """Render descriptive statistics for numeric columns.

        Args:
            data: Data to analyze
        """
        if not PANDAS_AVAILABLE:
            return

        df = pd.DataFrame(data)
        numeric_df = df.select_dtypes(include=["number"])

        if numeric_df.empty:
            st.info("No numeric columns to analyze")
            return

        st.subheader("Descriptive Statistics")
        st.dataframe(numeric_df.describe(), use_container_width=True)

    def render_feedback_section(
        self,
        on_feedback: Optional[callable] = None,
    ) -> Optional[dict[str, Any]]:
        """Render feedback collection section.

        Args:
            on_feedback: Callback when feedback submitted

        Returns:
            Feedback data if submitted
        """
        st.subheader("Feedback")

        col1, col2 = st.columns(2)

        with col1:
            rating = st.slider(
                "How helpful was this result?",
                min_value=1,
                max_value=5,
                value=4,
                key=f"{self.key}_rating",
            )

        with col2:
            accurate = st.radio(
                "Was the result accurate?",
                options=["Yes", "No", "Not sure"],
                horizontal=True,
                key=f"{self.key}_accurate",
            )

        comments = st.text_area(
            "Additional comments (optional)",
            key=f"{self.key}_comments",
            height=80,
        )

        if st.button("Submit Feedback", key=f"{self.key}_submit"):
            feedback = {
                "rating": rating,
                "was_accurate": accurate == "Yes",
                "was_helpful": rating >= 4,
                "comments": comments,
            }

            if on_feedback:
                on_feedback(feedback)

            st.success("Thank you for your feedback!")
            return feedback

        return None

    def render_drill_down_options(
        self,
        data: list[dict[str, Any]],
        on_drill_down: callable,
    ) -> None:
        """Render drill-down options for data exploration.

        Args:
            data: Current data
            on_drill_down: Callback when drill-down selected
        """
        if not PANDAS_AVAILABLE or not data:
            return

        df = pd.DataFrame(data)
        categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()

        if not categorical_cols:
            return

        st.markdown("**Drill Down:**")

        col1, col2 = st.columns(2)

        with col1:
            selected_col = st.selectbox(
                "Select dimension",
                options=categorical_cols,
                key=f"{self.key}_drill_col",
            )

        with col2:
            if selected_col:
                unique_values = df[selected_col].unique().tolist()
                selected_value = st.selectbox(
                    "Select value",
                    options=unique_values,
                    key=f"{self.key}_drill_val",
                )

                if st.button("Drill Down", key=f"{self.key}_drill_btn"):
                    on_drill_down(selected_col, selected_value)


def render_results_tabs(
    data: Optional[list[dict[str, Any]]] = None,
    chart_html: Optional[str] = None,
    summary: Optional[str] = None,
    sql_query: Optional[str] = None,
    python_code: Optional[str] = None,
) -> None:
    """Render results in tabbed interface.

    Args:
        data: Table data
        chart_html: Chart HTML
        summary: Summary text
        sql_query: SQL query used
        python_code: Python code used
    """
    tabs = st.tabs(["Data", "Visualization", "Summary", "Code"])

    with tabs[0]:
        if data:
            explorer = ResultsExplorerUI()
            explorer.render_data_table(data)
        else:
            st.info("No data available")

    with tabs[1]:
        if chart_html:
            explorer = ResultsExplorerUI()
            explorer.render_chart(chart_html)
        else:
            st.info("No visualization available")

    with tabs[2]:
        if summary:
            st.markdown(summary)
        else:
            st.info("No summary available")

    with tabs[3]:
        if sql_query:
            st.markdown("**SQL Query:**")
            st.code(sql_query, language="sql")

        if python_code:
            st.markdown("**Python Code:**")
            st.code(python_code, language="python")

        if not sql_query and not python_code:
            st.info("No code to display")
