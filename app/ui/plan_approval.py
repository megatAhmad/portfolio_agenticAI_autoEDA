"""Plan approval UI component for Streamlit."""

import logging
from typing import Any, Callable, Optional

import streamlit as st

from app.orchestration.planning_agent import ExecutionPlan, Task, TaskStatus, TaskType

logger = logging.getLogger(__name__)


class PlanApprovalUI:
    """UI component for displaying and approving execution plans."""

    def __init__(self, key: str = "plan"):
        """Initialize plan approval UI.

        Args:
            key: Unique key for session state
        """
        self.key = key
        self._init_session_state()

    def _init_session_state(self) -> None:
        """Initialize session state."""
        if f"{self.key}_current_plan" not in st.session_state:
            st.session_state[f"{self.key}_current_plan"] = None

        if f"{self.key}_task_selection" not in st.session_state:
            st.session_state[f"{self.key}_task_selection"] = {}

    def render_plan(
        self,
        plan: ExecutionPlan,
        on_approve: Optional[Callable[[list[str]], None]] = None,
        on_reject: Optional[Callable[[str], None]] = None,
        editable: bool = True,
    ) -> Optional[bool]:
        """Render execution plan with approval controls.

        Args:
            plan: Execution plan to display
            on_approve: Callback when approved (receives list of removed task IDs)
            on_reject: Callback when rejected (receives reason)
            editable: Whether tasks can be selected/deselected

        Returns:
            True if approved, False if rejected, None if pending
        """
        st.session_state[f"{self.key}_current_plan"] = plan

        # Header
        st.subheader("Execution Plan")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**Objective:** {plan.main_objective}")
        with col2:
            confidence_color = (
                "green" if plan.confidence >= 0.95
                else "orange" if plan.confidence >= 0.8
                else "red"
            )
            st.markdown(f"**Confidence:** :{confidence_color}[{plan.confidence:.0%}]")

        st.divider()

        # Task list
        removed_tasks = []

        for i, task in enumerate(plan.tasks):
            task_selected = self._render_task(task, i, editable)
            if not task_selected:
                removed_tasks.append(task.id)

        st.divider()

        # Estimated total time
        total_time = self._estimate_total_time(plan.tasks, removed_tasks)
        st.caption(f"Estimated total time: {total_time}")

        # Approval buttons
        if editable:
            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button("Approve & Execute", type="primary", use_container_width=True):
                    if on_approve:
                        on_approve(removed_tasks)
                    return True

            with col2:
                if st.button("Reject", type="secondary", use_container_width=True):
                    reason = st.session_state.get(f"{self.key}_reject_reason", "")
                    if on_reject:
                        on_reject(reason)
                    return False

            with col3:
                st.text_input(
                    "Rejection reason (optional)",
                    key=f"{self.key}_reject_reason",
                    label_visibility="collapsed",
                    placeholder="Reason for rejection...",
                )

        return None

    def _render_task(
        self,
        task: Task,
        index: int,
        editable: bool = True,
    ) -> bool:
        """Render a single task.

        Args:
            task: Task to render
            index: Task index
            editable: Whether task can be deselected

        Returns:
            Whether task is selected
        """
        # Initialize selection state
        if task.id not in st.session_state[f"{self.key}_task_selection"]:
            st.session_state[f"{self.key}_task_selection"][task.id] = True

        col1, col2, col3, col4 = st.columns([0.5, 3, 1, 1])

        with col1:
            if editable:
                selected = st.checkbox(
                    "",
                    value=st.session_state[f"{self.key}_task_selection"][task.id],
                    key=f"{self.key}_task_{task.id}",
                    label_visibility="collapsed",
                )
                st.session_state[f"{self.key}_task_selection"][task.id] = selected
            else:
                selected = True
                self._render_status_icon(task.status)

        with col2:
            # Task description
            task_type_icon = self._get_task_type_icon(task.task_type)
            st.markdown(f"{task_type_icon} **{index + 1}.** {task.description}")

            # Dependencies
            if task.dependencies:
                deps = ", ".join(f"Task {d.split('_')[-1]}" for d in task.dependencies)
                st.caption(f"Depends on: {deps}")

        with col3:
            st.caption(task.task_type.value)

        with col4:
            st.caption(task.estimated_time)

        return selected

    def _render_status_icon(self, status: TaskStatus) -> None:
        """Render task status icon.

        Args:
            status: Task status
        """
        icons = {
            TaskStatus.PENDING: "⏸️",
            TaskStatus.RUNNING: "⚙️",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.SKIPPED: "⊘",
        }
        st.markdown(icons.get(status, "❓"))

    def _get_task_type_icon(self, task_type: TaskType) -> str:
        """Get icon for task type.

        Args:
            task_type: Type of task

        Returns:
            Icon string
        """
        icons = {
            TaskType.SQL_QUERY: "🔍",
            TaskType.PYTHON_ANALYSIS: "🐍",
            TaskType.VISUALIZATION: "📊",
            TaskType.SYNTHESIS: "📝",
        }
        return icons.get(task_type, "📋")

    def _estimate_total_time(
        self,
        tasks: list[Task],
        excluded: list[str],
    ) -> str:
        """Estimate total execution time.

        Args:
            tasks: All tasks
            excluded: Task IDs to exclude

        Returns:
            Formatted time string
        """
        total_seconds = 0

        for task in tasks:
            if task.id in excluded:
                continue

            time_str = task.estimated_time.lower()
            if "s" in time_str:
                total_seconds += int(time_str.replace("s", ""))
            elif "m" in time_str:
                total_seconds += int(time_str.replace("m", "")) * 60

        if total_seconds < 60:
            return f"{total_seconds}s"
        else:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}m {seconds}s"

    def render_execution_progress(
        self,
        plan: ExecutionPlan,
    ) -> None:
        """Render execution progress.

        Args:
            plan: Execution plan with task statuses
        """
        st.subheader("Execution Progress")

        # Overall progress
        completed = sum(1 for t in plan.tasks if t.status == TaskStatus.COMPLETED)
        total = len(plan.tasks)
        progress = completed / total if total > 0 else 0

        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(progress)
        with col2:
            st.markdown(f"**{completed}/{total}** tasks")

        # Task details
        for task in plan.tasks:
            self._render_task_progress(task)

    def _render_task_progress(self, task: Task) -> None:
        """Render progress for a single task.

        Args:
            task: Task to render
        """
        status_colors = {
            TaskStatus.PENDING: "gray",
            TaskStatus.RUNNING: "blue",
            TaskStatus.COMPLETED: "green",
            TaskStatus.FAILED: "red",
            TaskStatus.SKIPPED: "orange",
        }

        color = status_colors.get(task.status, "gray")
        icon = self._get_task_type_icon(task.task_type)
        status_icon = {
            TaskStatus.PENDING: "⏸️",
            TaskStatus.RUNNING: "⚙️",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.SKIPPED: "⊘",
        }.get(task.status, "❓")

        col1, col2, col3 = st.columns([0.5, 3, 1])

        with col1:
            st.markdown(status_icon)

        with col2:
            st.markdown(f"{icon} {task.description}")

            if task.status == TaskStatus.COMPLETED and task.execution_time_ms:
                st.caption(f"Completed in {task.execution_time_ms}ms")
            elif task.status == TaskStatus.FAILED and task.error:
                st.error(task.error)

        with col3:
            if task.status == TaskStatus.RUNNING:
                st.spinner("Running...")


def render_quick_approval_dialog(
    plan: ExecutionPlan,
    on_approve: Callable[[], None],
    on_reject: Callable[[], None],
) -> None:
    """Render quick approval dialog.

    Args:
        plan: Execution plan
        on_approve: Callback when approved
        on_reject: Callback when rejected
    """
    with st.container():
        st.markdown("---")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(
                f"Ready to execute **{len(plan.tasks)} tasks** "
                f"(Confidence: {plan.confidence:.0%})"
            )

        with col2:
            if st.button("✓ Approve", type="primary"):
                on_approve()

        with col3:
            if st.button("✗ Reject"):
                on_reject()


def render_task_result(
    task: Task,
    result: dict[str, Any],
) -> None:
    """Render task result.

    Args:
        task: Completed task
        result: Task result data
    """
    with st.expander(f"Task Result: {task.description}", expanded=True):
        if task.task_type == TaskType.SQL_QUERY:
            # Show SQL and data
            if "query" in result:
                st.code(result["query"], language="sql")

            if "data" in result:
                import pandas as pd
                df = pd.DataFrame(result["data"])
                st.dataframe(df, use_container_width=True)

                st.caption(f"{len(df)} rows returned")

        elif task.task_type == TaskType.PYTHON_ANALYSIS:
            # Show code and output
            if "code" in result:
                st.code(result["code"], language="python")

            if "output" in result:
                st.json(result["output"])

        elif task.task_type == TaskType.VISUALIZATION:
            # Show chart
            if "chart_html" in result:
                import streamlit.components.v1 as components
                components.html(result["chart_html"], height=400)

        elif task.task_type == TaskType.SYNTHESIS:
            # Show summary text
            if "summary" in result:
                st.markdown(result["summary"])

        # Execution time
        if task.execution_time_ms:
            st.caption(f"Executed in {task.execution_time_ms}ms")
