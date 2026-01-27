"""Chat interface component for Streamlit."""

import logging
from datetime import datetime
from typing import Any, Callable, Optional

import streamlit as st

logger = logging.getLogger(__name__)


class Message:
    """A chat message."""

    def __init__(
        self,
        content: str,
        role: str = "user",
        timestamp: Optional[datetime] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self.content = content
        self.role = role  # 'user', 'assistant', 'system'
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}


class ChatInterface:
    """Streamlit chat interface component."""

    def __init__(self, key: str = "chat"):
        """Initialize chat interface.

        Args:
            key: Unique key for session state
        """
        self.key = key
        self._init_session_state()

    def _init_session_state(self) -> None:
        """Initialize session state for chat."""
        if f"{self.key}_messages" not in st.session_state:
            st.session_state[f"{self.key}_messages"] = []

        if f"{self.key}_input_key" not in st.session_state:
            st.session_state[f"{self.key}_input_key"] = 0

    @property
    def messages(self) -> list[Message]:
        """Get all messages."""
        return st.session_state[f"{self.key}_messages"]

    def add_message(
        self,
        content: str,
        role: str = "user",
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Add a message to the chat.

        Args:
            content: Message content
            role: Message role ('user', 'assistant', 'system')
            metadata: Optional metadata
        """
        message = Message(content=content, role=role, metadata=metadata)
        st.session_state[f"{self.key}_messages"].append(message)

    def add_user_message(self, content: str) -> None:
        """Add a user message."""
        self.add_message(content, role="user")

    def add_assistant_message(
        self,
        content: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Add an assistant message."""
        self.add_message(content, role="assistant", metadata=metadata)

    def add_system_message(self, content: str) -> None:
        """Add a system message."""
        self.add_message(content, role="system")

    def clear_messages(self) -> None:
        """Clear all messages."""
        st.session_state[f"{self.key}_messages"] = []

    def render_messages(self) -> None:
        """Render all messages in the chat."""
        for message in self.messages:
            self._render_message(message)

    def _render_message(self, message: Message) -> None:
        """Render a single message.

        Args:
            message: Message to render
        """
        if message.role == "user":
            with st.chat_message("user"):
                st.markdown(message.content)

        elif message.role == "assistant":
            with st.chat_message("assistant"):
                st.markdown(message.content)

                # Render any metadata/artifacts
                if message.metadata:
                    self._render_metadata(message.metadata)

        elif message.role == "system":
            with st.chat_message("assistant", avatar="ℹ️"):
                st.info(message.content)

    def _render_metadata(self, metadata: dict[str, Any]) -> None:
        """Render message metadata/artifacts.

        Args:
            metadata: Metadata to render
        """
        # Render data table if present
        if "data" in metadata:
            import pandas as pd
            df = pd.DataFrame(metadata["data"])
            st.dataframe(df, use_container_width=True)

        # Render chart if present
        if "chart_html" in metadata:
            import streamlit.components.v1 as components
            components.html(metadata["chart_html"], height=400)

        # Render confidence score if present
        if "confidence" in metadata:
            confidence = metadata["confidence"]
            color = "green" if confidence >= 0.95 else "orange" if confidence >= 0.8 else "red"
            st.markdown(f"Confidence: :{color}[{confidence:.0%}]")

        # Render execution time if present
        if "execution_time_ms" in metadata:
            st.caption(f"Executed in {metadata['execution_time_ms']}ms")

    def render_input(
        self,
        on_submit: Optional[Callable[[str], None]] = None,
        placeholder: str = "Ask a question about your data...",
        disabled: bool = False,
    ) -> Optional[str]:
        """Render chat input box.

        Args:
            on_submit: Callback function when message submitted
            placeholder: Input placeholder text
            disabled: Whether input is disabled

        Returns:
            User input if submitted
        """
        user_input = st.chat_input(
            placeholder,
            disabled=disabled,
            key=f"{self.key}_input_{st.session_state[f'{self.key}_input_key']}",
        )

        if user_input:
            self.add_user_message(user_input)

            if on_submit:
                on_submit(user_input)

            # Increment input key to reset input
            st.session_state[f"{self.key}_input_key"] += 1

        return user_input

    def render_clarification_ui(
        self,
        questions: list[dict[str, Any]],
        on_submit: Callable[[dict[str, str]], None],
    ) -> None:
        """Render clarification questions UI.

        Args:
            questions: List of clarification questions
            on_submit: Callback with responses
        """
        st.info("I need some clarification before proceeding:")

        responses = {}

        with st.form(key=f"{self.key}_clarification_form"):
            for i, question in enumerate(questions):
                q_id = question.get("id", f"q_{i}")
                q_text = question.get("text", "")
                q_type = question.get("type", "multiple_choice")
                options = question.get("options", [])

                st.markdown(f"**{i + 1}. {q_text}**")

                if q_type == "multiple_choice" and options:
                    option_labels = [opt.get("label", opt.get("value", "")) for opt in options]
                    option_values = [opt.get("value", "") for opt in options]

                    selected = st.radio(
                        "Select one:",
                        options=option_labels,
                        key=f"{self.key}_q_{i}",
                        label_visibility="collapsed",
                    )

                    if selected:
                        idx = option_labels.index(selected)
                        responses[q_id] = option_values[idx]

                else:
                    response = st.text_input(
                        "Your answer:",
                        key=f"{self.key}_q_{i}",
                        label_visibility="collapsed",
                    )
                    responses[q_id] = response

                st.divider()

            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("Submit Answers", type="primary")
            with col2:
                skip = st.form_submit_button("Skip (Use Defaults)")

            if submitted:
                on_submit(responses)
            elif skip:
                on_submit({})

    def render_typing_indicator(self) -> None:
        """Render typing indicator while processing."""
        with st.chat_message("assistant"):
            st.markdown("_Thinking..._")

    def render_error(self, error: str) -> None:
        """Render error message.

        Args:
            error: Error message
        """
        st.error(f"Error: {error}")

    def get_conversation_history(self, max_messages: int = 10) -> list[dict[str, str]]:
        """Get recent conversation history for context.

        Args:
            max_messages: Maximum number of messages to return

        Returns:
            List of message dictionaries
        """
        recent = self.messages[-max_messages:]
        return [
            {"role": m.role, "content": m.content}
            for m in recent
            if m.role in ["user", "assistant"]
        ]


def render_chat_sidebar(chat: ChatInterface) -> None:
    """Render chat sidebar with history and controls.

    Args:
        chat: Chat interface instance
    """
    with st.sidebar:
        st.subheader("Chat History")

        if st.button("Clear Chat", use_container_width=True):
            chat.clear_messages()
            st.rerun()

        st.divider()

        # Show message count
        st.caption(f"{len(chat.messages)} messages")

        # Show recent queries
        user_messages = [m for m in chat.messages if m.role == "user"]
        if user_messages:
            st.markdown("**Recent Queries:**")
            for msg in user_messages[-5:]:
                truncated = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                st.caption(f"• {truncated}")


def create_welcome_message() -> str:
    """Create welcome message for new sessions.

    Returns:
        Welcome message string
    """
    return """Welcome to the **Agentic Data Analyst**!

I can help you analyze your data by answering questions in natural language. Here's what I can do:

- **Query your data**: "Show me revenue by region for last quarter"
- **Analyze trends**: "What are the top performing products?"
- **Create visualizations**: "Create a chart showing monthly sales"
- **Compare metrics**: "Compare this year's performance to last year"

To get started:
1. Upload your data file (CSV/Excel) in the sidebar
2. Upload any business context files (optional)
3. Ask me a question about your data!

I'll ask clarifying questions if I'm unsure about your intent, and show you my execution plan before running queries."""
