"""Main Streamlit application entry point for Agentic Data Analyst."""

import logging
import sys
from pathlib import Path

import streamlit as st

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Agentic Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state() -> None:
    """Initialize session state variables."""
    defaults = {
        "messages": [],
        "current_plan": None,
        "data_uploaded": False,
        "context_uploaded": False,
        "db_manager": None,
        "semantic_layer": None,
        "rag_system": None,
        "conversation_id": None,
        "awaiting_clarification": False,
        "awaiting_approval": False,
        "clarification_session": None,
        "approval_request": None,
        "current_data": None,
        "current_schema": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def init_services() -> None:
    """Initialize backend services."""
    settings = get_settings()

    # Initialize database manager
    if st.session_state.db_manager is None:
        try:
            from app.execution.db_manager import DatabaseManager
            st.session_state.db_manager = DatabaseManager(
                postgres_url=settings.postgres.connection_string,
            )
            logger.info("Database manager initialized")
        except Exception as e:
            logger.warning(f"Could not initialize database manager: {e}")

    # Initialize semantic layer
    if st.session_state.semantic_layer is None:
        try:
            from app.knowledge.semantic_layer import SemanticLayer
            config_path = Path("config/semantic_layer.json")
            st.session_state.semantic_layer = SemanticLayer(config_path)
            logger.info("Semantic layer initialized")
        except Exception as e:
            logger.warning(f"Could not initialize semantic layer: {e}")

    # Initialize RAG system
    if st.session_state.rag_system is None:
        try:
            from app.knowledge.rag_system import RAGSystem
            st.session_state.rag_system = RAGSystem(
                persist_dir=settings.chroma_persist_dir,
            )
            logger.info("RAG system initialized")
        except Exception as e:
            logger.warning(f"Could not initialize RAG system: {e}")


def render_sidebar() -> None:
    """Render sidebar with data upload and settings."""
    with st.sidebar:
        st.title("📊 Agentic Analyst")
        st.caption("Local-first semantic analytics")

        st.divider()

        # Data upload section
        st.subheader("Data")

        uploaded_file = st.file_uploader(
            "Upload data file",
            type=["csv", "xlsx", "xls"],
            help="Upload CSV or Excel file to analyze",
        )

        if uploaded_file:
            handle_data_upload(uploaded_file)

        # Context upload section
        st.divider()
        st.subheader("Business Context")

        context_files = st.file_uploader(
            "Upload context files",
            type=["txt", "json"],
            accept_multiple_files=True,
            help="Upload business definitions and context",
        )

        if context_files:
            handle_context_upload(context_files)

        # Settings
        st.divider()
        st.subheader("Settings")

        settings = get_settings()
        threshold = st.slider(
            "Confidence threshold",
            min_value=0.5,
            max_value=1.0,
            value=settings.uncertainty_threshold,
            step=0.05,
            help="Minimum confidence to proceed without clarification",
        )

        # Status indicators
        st.divider()
        st.subheader("Status")

        col1, col2 = st.columns(2)
        with col1:
            data_status = "✅" if st.session_state.data_uploaded else "❌"
            st.markdown(f"Data: {data_status}")
        with col2:
            context_status = "✅" if st.session_state.context_uploaded else "⚠️"
            st.markdown(f"Context: {context_status}")

        # Clear conversation
        st.divider()
        if st.button("Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.current_plan = None
            st.session_state.awaiting_clarification = False
            st.session_state.awaiting_approval = False
            st.rerun()


def handle_data_upload(uploaded_file) -> None:
    """Handle data file upload.

    Args:
        uploaded_file: Streamlit uploaded file
    """
    import pandas as pd

    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.session_state.current_data = df.to_dict(orient="records")
        st.session_state.current_schema = {
            "columns": {
                col: {"type": str(df[col].dtype), "nullable": df[col].isnull().any()}
                for col in df.columns
            }
        }
        st.session_state.data_uploaded = True

        # Try to create table in PostgreSQL if available
        if st.session_state.db_manager:
            try:
                table_name = Path(uploaded_file.name).stem.lower().replace(" ", "_")
                st.session_state.db_manager.create_table_from_dataframe(df, table_name)
                st.success(f"Data loaded: {len(df)} rows, {len(df.columns)} columns")
            except Exception as e:
                logger.warning(f"Could not create database table: {e}")
                st.info(f"Data loaded in memory: {len(df)} rows")
        else:
            st.info(f"Data loaded in memory: {len(df)} rows")

    except Exception as e:
        st.error(f"Error loading file: {e}")


def handle_context_upload(context_files: list) -> None:
    """Handle context file uploads.

    Args:
        context_files: List of uploaded context files
    """
    if not st.session_state.rag_system:
        st.warning("RAG system not available")
        return

    for file in context_files:
        try:
            content = file.read().decode("utf-8")
            file.seek(0)

            if file.name.endswith(".json"):
                st.session_state.rag_system.add_document(
                    content, file.name, {"type": "json"}
                )
            else:
                st.session_state.rag_system.add_document(
                    content, file.name, {"type": "text"}
                )

            st.session_state.context_uploaded = True

        except Exception as e:
            st.error(f"Error processing {file.name}: {e}")

    if st.session_state.context_uploaded:
        st.success(f"Loaded {len(context_files)} context file(s)")


def process_query(query: str) -> None:
    """Process user query through the pipeline.

    Args:
        query: User's natural language query
    """
    settings = get_settings()

    # Add assistant thinking message
    with st.chat_message("assistant"):
        with st.spinner("Analyzing your query..."):
            try:
                # Step 1: Parse intent
                from app.orchestration.planning_agent import PlanningAgent

                planning_agent = PlanningAgent(
                    azure_endpoint=settings.azure_openai.endpoint,
                    azure_api_key=settings.azure_openai.api_key,
                    azure_deployment=settings.azure_openai.gpt4_deployment,
                    openrouter_api_key=settings.openrouter.api_key,
                )

                # Get context
                semantic_context = ""
                if st.session_state.semantic_layer:
                    semantic_context = st.session_state.semantic_layer.to_prompt_context()

                rag_context = ""
                if st.session_state.rag_system:
                    rag_context = st.session_state.rag_system.get_context_for_query(query)

                parsed_intent = planning_agent.parse_intent(
                    query, semantic_context, rag_context
                )

                # Step 2: Calculate uncertainty
                from app.orchestration.uncertainty_scorer import UncertaintyScorer

                scorer = UncertaintyScorer(threshold=settings.uncertainty_threshold)

                uncertainty_result = scorer.evaluate(
                    parsed_intent,
                    st.session_state.semantic_layer,
                    st.session_state.current_schema,
                )

                # Step 3: Check if clarification needed
                if uncertainty_result.needs_clarification and uncertainty_result.suggested_questions:
                    st.session_state.awaiting_clarification = True
                    st.session_state.clarification_questions = uncertainty_result.suggested_questions
                    st.session_state.parsed_intent = parsed_intent

                    st.markdown(f"**Confidence:** {uncertainty_result.score:.0%}")
                    st.warning("I need some clarification before proceeding.")

                    # Store message
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"I need clarification (confidence: {uncertainty_result.score:.0%})",
                        "metadata": {"needs_clarification": True},
                    })
                    return

                # Step 4: Create execution plan
                plan = planning_agent.create_plan(query, parsed_intent)

                st.markdown(f"**Confidence:** {uncertainty_result.score:.0%}")
                st.markdown(f"**Plan:** {plan.main_objective}")

                # Step 5: Request approval
                st.session_state.awaiting_approval = True
                st.session_state.current_plan = plan

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Ready to execute: {plan.main_objective}\nConfidence: {uncertainty_result.score:.0%}",
                    "metadata": {"plan": plan.model_dump()},
                })

            except Exception as e:
                logger.error(f"Query processing error: {e}")
                st.error(f"Error processing query: {e}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"I encountered an error: {e}",
                })


def render_clarification_ui() -> None:
    """Render clarification questions UI."""
    questions = st.session_state.get("clarification_questions", [])

    if not questions:
        return

    st.info("Please help me understand your query better:")

    responses = {}

    with st.form("clarification_form"):
        for i, q in enumerate(questions):
            st.markdown(f"**{i + 1}. {q.get('text', '')}**")

            options = q.get("options", [])
            if options:
                labels = [opt.get("label", opt.get("value", "")) for opt in options]
                values = [opt.get("value", "") for opt in options]

                selected = st.radio(
                    "Select one:",
                    options=labels,
                    key=f"clarify_{i}",
                    label_visibility="collapsed",
                )

                if selected:
                    idx = labels.index(selected)
                    responses[q.get("term", f"q_{i}")] = values[idx]
            else:
                response = st.text_input(
                    "Your answer:",
                    key=f"clarify_{i}",
                    label_visibility="collapsed",
                )
                responses[q.get("term", f"q_{i}")] = response

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Submit", type="primary"):
                handle_clarification_response(responses)
        with col2:
            if st.form_submit_button("Skip"):
                st.session_state.awaiting_clarification = False
                st.rerun()


def handle_clarification_response(responses: dict) -> None:
    """Handle user clarification responses.

    Args:
        responses: Dictionary of term -> response
    """
    st.session_state.awaiting_clarification = False

    # Learn from clarifications
    if st.session_state.semantic_layer:
        for term, value in responses.items():
            try:
                st.session_state.semantic_layer.add_synonym(term, value, "metric")
            except Exception:
                pass

    # Re-process query with clarifications
    st.session_state.messages.append({
        "role": "user",
        "content": f"Clarification: {responses}",
    })

    st.rerun()


def render_approval_ui() -> None:
    """Render plan approval UI."""
    plan = st.session_state.current_plan

    if not plan:
        return

    from app.ui.plan_approval import PlanApprovalUI

    approval_ui = PlanApprovalUI()

    def on_approve(removed_tasks):
        st.session_state.awaiting_approval = False
        execute_plan(plan, removed_tasks)

    def on_reject(reason):
        st.session_state.awaiting_approval = False
        st.session_state.current_plan = None
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Plan rejected. {reason}" if reason else "Plan rejected.",
        })
        st.rerun()

    approval_ui.render_plan(plan, on_approve, on_reject)


def execute_plan(plan, removed_tasks: list) -> None:
    """Execute approved plan.

    Args:
        plan: Execution plan
        removed_tasks: Task IDs to skip
    """
    settings = get_settings()

    with st.spinner("Executing plan..."):
        results = {}

        for task in plan.tasks:
            if task.id in removed_tasks:
                continue

            try:
                if task.task_type.value == "sql_query":
                    # Execute SQL
                    from app.agents.sql_generator import SQLGeneratorAgent

                    sql_agent = SQLGeneratorAgent(
                        db_manager=st.session_state.db_manager,
                        semantic_layer=st.session_state.semantic_layer,
                        azure_endpoint=settings.azure_openai.endpoint,
                        azure_api_key=settings.azure_openai.api_key,
                        azure_deployment=settings.azure_openai.gpt4_deployment,
                    )

                    gen_result, exec_result = sql_agent.generate_and_execute(
                        plan.query,
                        additional_context=st.session_state.semantic_layer.to_prompt_context()
                        if st.session_state.semantic_layer else None,
                    )

                    if exec_result and exec_result.success:
                        results["data"] = exec_result.data
                        results["query"] = gen_result.query

                elif task.task_type.value == "visualization":
                    # Create visualization
                    if "data" in results:
                        from app.agents.visualization import VisualizationAgent

                        viz_agent = VisualizationAgent()
                        viz_result = viz_agent.auto_visualize(
                            results["data"],
                            title=plan.main_objective,
                        )

                        if viz_result.success:
                            results["chart_html"] = viz_result.chart_html

                elif task.task_type.value == "synthesis":
                    # Generate summary
                    if "data" in results:
                        results["summary"] = f"Query returned {len(results['data'])} rows."

            except Exception as e:
                logger.error(f"Task {task.id} failed: {e}")
                results[f"error_{task.id}"] = str(e)

    # Display results
    display_results(results)

    st.session_state.current_plan = None
    st.rerun()


def display_results(results: dict) -> None:
    """Display execution results.

    Args:
        results: Dictionary of results
    """
    from app.ui.results_explorer import render_results_tabs

    st.session_state.messages.append({
        "role": "assistant",
        "content": "Here are your results:",
        "metadata": results,
    })


def render_main_content() -> None:
    """Render main content area."""
    st.title("Agentic Data Analyst")

    # Show welcome message if no messages
    if not st.session_state.messages:
        from app.ui.chat import create_welcome_message
        st.markdown(create_welcome_message())

    # Render chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            # Render metadata/results
            metadata = msg.get("metadata", {})
            if "data" in metadata:
                import pandas as pd
                df = pd.DataFrame(metadata["data"])
                st.dataframe(df.head(20), use_container_width=True)

            if "chart_html" in metadata:
                import streamlit.components.v1 as components
                components.html(metadata["chart_html"], height=400)

    # Handle special states
    if st.session_state.awaiting_clarification:
        render_clarification_ui()
    elif st.session_state.awaiting_approval:
        render_approval_ui()

    # Chat input
    if not st.session_state.awaiting_clarification and not st.session_state.awaiting_approval:
        if prompt := st.chat_input("Ask a question about your data..."):
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            process_query(prompt)


def main() -> None:
    """Main application entry point."""
    init_session_state()
    init_services()
    render_sidebar()
    render_main_content()


if __name__ == "__main__":
    main()
