"""Visualization Agent for generating interactive charts."""

import json
import logging
from typing import Any, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.utils import PlotlyJSONEncoder
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly not available")

try:
    from openai import AzureOpenAI, OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class ChartConfig(BaseModel):
    """Configuration for a chart."""

    chart_type: str
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    color_column: Optional[str] = None
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    show_legend: bool = True
    height: int = 400


class VisualizationResult(BaseModel):
    """Result of visualization generation."""

    success: bool
    chart_type: str = ""
    chart_json: Optional[str] = None
    chart_html: Optional[str] = None
    error: Optional[str] = None


class VisualizationAgent:
    """Agent for generating interactive visualizations."""

    CHART_TYPE_MAP = {
        "bar": "bar_chart",
        "line": "line_chart",
        "scatter": "scatter_plot",
        "pie": "pie_chart",
        "histogram": "histogram",
        "heatmap": "heatmap",
        "box": "box_plot",
        "area": "area_chart",
        "table": "table",
    }

    def __init__(
        self,
        azure_endpoint: Optional[str] = None,
        azure_api_key: Optional[str] = None,
        azure_deployment: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
    ):
        """Initialize Visualization Agent.

        Args:
            azure_endpoint: Azure OpenAI endpoint
            azure_api_key: Azure OpenAI API key
            azure_deployment: Azure deployment name
            openrouter_api_key: OpenRouter API key for fallback
        """
        self._llm_client: Optional[Any] = None
        self._model: str = ""

        if azure_endpoint and azure_api_key and OPENAI_AVAILABLE:
            self._llm_client = AzureOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=azure_api_key,
                api_version="2024-02-15-preview",
            )
            self._model = azure_deployment or "gpt-35-turbo"

        elif openrouter_api_key and OPENAI_AVAILABLE:
            self._llm_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_api_key,
            )
            self._model = "anthropic/claude-3-haiku"

    def select_chart_type(
        self,
        data: list[dict[str, Any]],
        query_intent: Optional[dict[str, Any]] = None,
    ) -> str:
        """Automatically select appropriate chart type based on data.

        Args:
            data: Data to visualize
            query_intent: Optional parsed query intent

        Returns:
            Chart type string
        """
        if not data:
            return "table"

        # Analyze data structure
        sample = data[0]
        columns = list(sample.keys())

        # Detect column types
        datetime_cols = []
        numeric_cols = []
        categorical_cols = []

        for col in columns:
            values = [row.get(col) for row in data[:100] if row.get(col) is not None]
            if not values:
                continue

            sample_val = values[0]

            # Check if datetime
            if isinstance(sample_val, str):
                if any(x in sample_val for x in ["-", "/", ":"]) and len(sample_val) >= 8:
                    datetime_cols.append(col)
                    continue

            # Check if numeric
            try:
                float(sample_val)
                numeric_cols.append(col)
            except (ValueError, TypeError):
                categorical_cols.append(col)

        # Decision logic
        num_rows = len(data)

        # Check query intent for hints
        if query_intent:
            if query_intent.get("show_trend"):
                return "line_chart"
            if query_intent.get("show_distribution"):
                return "histogram"
            if query_intent.get("show_comparison"):
                return "bar_chart"
            if query_intent.get("show_composition"):
                return "pie_chart"

        # Time series data
        if datetime_cols and numeric_cols:
            return "line_chart"

        # Single categorical + single numeric
        if len(categorical_cols) == 1 and len(numeric_cols) >= 1:
            unique_cats = len(set(row.get(categorical_cols[0]) for row in data))
            if unique_cats <= 10:
                return "bar_chart"
            return "table"

        # Two numeric columns - scatter
        if len(numeric_cols) >= 2 and len(categorical_cols) == 0:
            return "scatter_plot"

        # Multiple categories - heatmap
        if len(categorical_cols) >= 2 and len(numeric_cols) >= 1:
            return "heatmap"

        # Distribution analysis
        if len(numeric_cols) == 1 and len(categorical_cols) == 0:
            return "histogram"

        # Default to table
        return "table"

    def create_chart(
        self,
        data: list[dict[str, Any]],
        config: ChartConfig,
    ) -> VisualizationResult:
        """Create a chart based on configuration.

        Args:
            data: Data to visualize
            config: Chart configuration

        Returns:
            VisualizationResult with chart
        """
        if not PLOTLY_AVAILABLE:
            return VisualizationResult(
                success=False,
                error="Plotly not installed",
            )

        if not data:
            return VisualizationResult(
                success=False,
                error="No data provided",
            )

        try:
            import pandas as pd
            df = pd.DataFrame(data)

            fig = self._create_plotly_figure(df, config)

            # Convert to JSON and HTML
            chart_json = json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder)
            chart_html = fig.to_html(include_plotlyjs="cdn", full_html=False)

            return VisualizationResult(
                success=True,
                chart_type=config.chart_type,
                chart_json=chart_json,
                chart_html=chart_html,
            )

        except Exception as e:
            logger.error(f"Chart creation failed: {e}")
            return VisualizationResult(
                success=False,
                chart_type=config.chart_type,
                error=str(e),
            )

    def _create_plotly_figure(
        self,
        df: Any,  # pd.DataFrame
        config: ChartConfig,
    ) -> Any:
        """Create Plotly figure based on chart type.

        Args:
            df: DataFrame with data
            config: Chart configuration

        Returns:
            Plotly figure
        """
        chart_type = config.chart_type
        x = config.x_column
        y = config.y_column
        color = config.color_column

        # Auto-detect columns if not specified
        if not x and not y:
            columns = df.columns.tolist()
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            non_numeric = [c for c in columns if c not in numeric_cols]

            if non_numeric:
                x = non_numeric[0]
            if numeric_cols:
                y = numeric_cols[0]

        # Create figure based on type
        if chart_type == "bar_chart":
            fig = px.bar(
                df, x=x, y=y, color=color,
                title=config.title,
                labels={x: config.x_label or x, y: config.y_label or y} if x and y else None,
            )

        elif chart_type == "line_chart":
            fig = px.line(
                df, x=x, y=y, color=color,
                title=config.title,
                labels={x: config.x_label or x, y: config.y_label or y} if x and y else None,
            )

        elif chart_type == "scatter_plot":
            fig = px.scatter(
                df, x=x, y=y, color=color,
                title=config.title,
                labels={x: config.x_label or x, y: config.y_label or y} if x and y else None,
            )

        elif chart_type == "pie_chart":
            values_col = y or (df.select_dtypes(include=["number"]).columns[0]
                              if len(df.select_dtypes(include=["number"]).columns) > 0 else None)
            names_col = x or (df.select_dtypes(exclude=["number"]).columns[0]
                             if len(df.select_dtypes(exclude=["number"]).columns) > 0 else None)
            fig = px.pie(
                df, values=values_col, names=names_col,
                title=config.title,
            )

        elif chart_type == "histogram":
            fig = px.histogram(
                df, x=x or y, color=color,
                title=config.title,
            )

        elif chart_type == "heatmap":
            # Need to pivot data for heatmap
            if x and y and color:
                pivot = df.pivot_table(values=color, index=y, columns=x, aggfunc="mean")
                fig = px.imshow(
                    pivot,
                    title=config.title,
                    labels={"color": color},
                )
            else:
                # Correlation heatmap
                numeric_df = df.select_dtypes(include=["number"])
                corr = numeric_df.corr()
                fig = px.imshow(
                    corr,
                    title=config.title or "Correlation Heatmap",
                    labels={"color": "Correlation"},
                )

        elif chart_type == "box_plot":
            fig = px.box(
                df, x=x, y=y, color=color,
                title=config.title,
            )

        elif chart_type == "area_chart":
            fig = px.area(
                df, x=x, y=y, color=color,
                title=config.title,
            )

        else:
            # Default to table representation
            fig = go.Figure(data=[go.Table(
                header=dict(values=list(df.columns)),
                cells=dict(values=[df[col].tolist() for col in df.columns]),
            )])
            fig.update_layout(title=config.title or "Data Table")

        # Apply common styling
        fig.update_layout(
            height=config.height,
            showlegend=config.show_legend,
            template="plotly_white",
        )

        return fig

    def auto_visualize(
        self,
        data: list[dict[str, Any]],
        title: str = "",
        query_intent: Optional[dict[str, Any]] = None,
    ) -> VisualizationResult:
        """Automatically create appropriate visualization.

        Args:
            data: Data to visualize
            title: Chart title
            query_intent: Optional query intent for hints

        Returns:
            VisualizationResult
        """
        chart_type = self.select_chart_type(data, query_intent)

        # Infer columns
        import pandas as pd
        df = pd.DataFrame(data)

        x_col = None
        y_col = None
        color_col = None

        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

        if categorical_cols:
            x_col = categorical_cols[0]
            if len(categorical_cols) > 1:
                color_col = categorical_cols[1]

        if numeric_cols:
            y_col = numeric_cols[0]

        config = ChartConfig(
            chart_type=chart_type,
            x_column=x_col,
            y_column=y_col,
            color_column=color_col,
            title=title,
        )

        return self.create_chart(data, config)

    def suggest_chart_type(
        self,
        query: str,
        data_description: str,
    ) -> str:
        """Use LLM to suggest best chart type.

        Args:
            query: User's visualization query
            data_description: Description of the data

        Returns:
            Suggested chart type
        """
        if not self._llm_client:
            return "bar_chart"

        prompt = f"""
Based on the user's request and data, suggest the best chart type.

User Request: {query}
Data Description: {data_description}

Available chart types: bar_chart, line_chart, scatter_plot, pie_chart, histogram, heatmap, box_plot, area_chart, table

Respond with ONLY the chart type name, nothing else.
"""

        try:
            response = self._llm_client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=50,
            )

            suggestion = response.choices[0].message.content or "bar_chart"
            suggestion = suggestion.strip().lower()

            # Validate suggestion
            if suggestion in self.CHART_TYPE_MAP:
                return self.CHART_TYPE_MAP[suggestion]
            if suggestion in self.CHART_TYPE_MAP.values():
                return suggestion

            return "bar_chart"

        except Exception as e:
            logger.error(f"Chart suggestion failed: {e}")
            return "bar_chart"

    def create_dashboard(
        self,
        charts: list[VisualizationResult],
        title: str = "Dashboard",
        cols: int = 2,
    ) -> str:
        """Create a dashboard HTML with multiple charts.

        Args:
            charts: List of visualization results
            title: Dashboard title
            cols: Number of columns

        Returns:
            Dashboard HTML string
        """
        if not PLOTLY_AVAILABLE:
            return "<p>Plotly not available</p>"

        valid_charts = [c for c in charts if c.success and c.chart_html]

        if not valid_charts:
            return "<p>No valid charts to display</p>"

        # Build HTML grid
        html_parts = [
            f"<h2>{title}</h2>",
            '<div style="display: grid; grid-template-columns: repeat({}, 1fr); gap: 20px;">'.format(cols),
        ]

        for chart in valid_charts:
            html_parts.append(f'<div style="border: 1px solid #ddd; padding: 10px;">{chart.chart_html}</div>')

        html_parts.append("</div>")

        return "\n".join(html_parts)
