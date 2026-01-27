"""Human-in-the-Loop Controller for managing clarifications and approvals."""

import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.execution.db_manager import DatabaseManager
from app.knowledge.semantic_layer import SemanticLayer
from app.orchestration.planning_agent import ExecutionPlan
from app.orchestration.uncertainty_scorer import UncertaintyResult

logger = logging.getLogger(__name__)


class ClarificationType(str, Enum):
    """Types of clarification questions."""

    MULTIPLE_CHOICE = "multiple_choice"
    OPEN_ENDED = "open_ended"
    CONFIRMATION = "confirmation"


class ClarificationQuestion(BaseModel):
    """A clarification question for the user."""

    id: str = Field(default_factory=lambda: f"q_{uuid.uuid4().hex[:8]}")
    question_type: ClarificationType
    text: str
    term: Optional[str] = None
    term_type: Optional[str] = None
    options: list[dict[str, str]] = Field(default_factory=list)
    required: bool = True
    response: Optional[str] = None
    responded_at: Optional[datetime] = None


class ClarificationSession(BaseModel):
    """A session of clarification questions."""

    session_id: str = Field(default_factory=lambda: f"session_{uuid.uuid4().hex[:8]}")
    conversation_id: Optional[str] = None
    questions: list[ClarificationQuestion] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, in_progress, completed, cancelled


class ApprovalRequest(BaseModel):
    """Request for user approval of execution plan."""

    request_id: str = Field(default_factory=lambda: f"approval_{uuid.uuid4().hex[:8]}")
    plan: ExecutionPlan
    uncertainty_score: float
    message: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved: Optional[bool] = None
    approved_at: Optional[datetime] = None
    modifications: list[str] = Field(default_factory=list)


class HITLController:
    """Controller for human-in-the-loop interactions."""

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        semantic_layer: Optional[SemanticLayer] = None,
    ):
        """Initialize HITL Controller.

        Args:
            db_manager: Database manager for logging interactions
            semantic_layer: Semantic layer for context learning
        """
        self.db_manager = db_manager
        self.semantic_layer = semantic_layer
        self._active_sessions: dict[str, ClarificationSession] = {}
        self._pending_approvals: dict[str, ApprovalRequest] = {}

    def create_clarification_session(
        self,
        uncertainty_result: UncertaintyResult,
        conversation_id: Optional[str] = None,
    ) -> ClarificationSession:
        """Create a clarification session from uncertainty result.

        Args:
            uncertainty_result: Result from uncertainty scorer
            conversation_id: Optional conversation ID for logging

        Returns:
            ClarificationSession with questions
        """
        questions = []

        for q_data in uncertainty_result.suggested_questions:
            question_type = ClarificationType(q_data.get("type", "multiple_choice"))

            question = ClarificationQuestion(
                question_type=question_type,
                text=q_data.get("text", ""),
                term=q_data.get("term"),
                term_type=q_data.get("term_type"),
                options=q_data.get("options", []),
            )
            questions.append(question)

        session = ClarificationSession(
            conversation_id=conversation_id,
            questions=questions,
        )

        self._active_sessions[session.session_id] = session

        # Log to database if available
        if self.db_manager and conversation_id:
            for q in questions:
                try:
                    self.db_manager.add_clarification(
                        conversation_id=uuid.UUID(conversation_id),
                        question_text=q.text,
                        question_type=q.question_type.value,
                        options=q.options if q.options else None,
                    )
                except Exception as e:
                    logger.warning(f"Failed to log clarification: {e}")

        return session

    def get_session(self, session_id: str) -> Optional[ClarificationSession]:
        """Get an active clarification session.

        Args:
            session_id: Session ID

        Returns:
            ClarificationSession or None
        """
        return self._active_sessions.get(session_id)

    def record_response(
        self,
        session_id: str,
        question_id: str,
        response: str,
    ) -> bool:
        """Record user response to a clarification question.

        Args:
            session_id: Session ID
            question_id: Question ID
            response: User's response

        Returns:
            True if response recorded successfully
        """
        session = self._active_sessions.get(session_id)
        if not session:
            return False

        for question in session.questions:
            if question.id == question_id:
                question.response = response
                question.responded_at = datetime.utcnow()

                # Learn from clarification if semantic layer available
                if self.semantic_layer and question.term and question.term_type:
                    self._learn_from_clarification(question, response)

                break

        # Check if all required questions answered
        all_answered = all(
            q.response is not None
            for q in session.questions
            if q.required
        )

        if all_answered:
            session.status = "completed"

        return True

    def record_responses_batch(
        self,
        session_id: str,
        responses: dict[str, str],
    ) -> dict[str, str]:
        """Record multiple responses at once.

        Args:
            session_id: Session ID
            responses: Dictionary of question_id -> response

        Returns:
            Dictionary of clarified terms
        """
        session = self._active_sessions.get(session_id)
        if not session:
            return {}

        clarified_terms = {}

        for question in session.questions:
            if question.id in responses:
                question.response = responses[question.id]
                question.responded_at = datetime.utcnow()

                if question.term:
                    clarified_terms[question.term] = question.response

                if self.semantic_layer and question.term and question.term_type:
                    self._learn_from_clarification(question, question.response)

        # Update session status
        all_answered = all(
            q.response is not None
            for q in session.questions
            if q.required
        )

        if all_answered:
            session.status = "completed"

        return clarified_terms

    def _learn_from_clarification(
        self,
        question: ClarificationQuestion,
        response: str,
    ) -> None:
        """Update semantic layer with clarification.

        Args:
            question: The clarification question
            response: User's response
        """
        if not self.semantic_layer or not question.term:
            return

        try:
            self.semantic_layer.add_synonym(
                term=question.term,
                canonical_name=response,
                term_type=question.term_type or "metric",
            )
            logger.info(f"Learned: '{question.term}' -> '{response}'")
        except Exception as e:
            logger.warning(f"Failed to learn from clarification: {e}")

    def create_approval_request(
        self,
        plan: ExecutionPlan,
        uncertainty_score: float,
    ) -> ApprovalRequest:
        """Create an approval request for an execution plan.

        Args:
            plan: Execution plan to approve
            uncertainty_score: Confidence score

        Returns:
            ApprovalRequest
        """
        message = f"Ready to execute plan with {uncertainty_score:.0%} confidence."

        if uncertainty_score < 0.8:
            message += " Note: Confidence is below 80%, please review carefully."

        request = ApprovalRequest(
            plan=plan,
            uncertainty_score=uncertainty_score,
            message=message,
        )

        self._pending_approvals[request.request_id] = request
        return request

    def get_approval_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a pending approval request.

        Args:
            request_id: Request ID

        Returns:
            ApprovalRequest or None
        """
        return self._pending_approvals.get(request_id)

    def approve_plan(
        self,
        request_id: str,
        modifications: Optional[list[str]] = None,
    ) -> Optional[ExecutionPlan]:
        """Approve an execution plan.

        Args:
            request_id: Approval request ID
            modifications: Optional list of task IDs to remove

        Returns:
            Approved ExecutionPlan or None
        """
        request = self._pending_approvals.get(request_id)
        if not request:
            return None

        request.approved = True
        request.approved_at = datetime.utcnow()

        plan = request.plan

        # Apply modifications
        if modifications:
            request.modifications = modifications
            plan.tasks = [t for t in plan.tasks if t.id not in modifications]

        return plan

    def reject_plan(self, request_id: str, reason: str = "") -> bool:
        """Reject an execution plan.

        Args:
            request_id: Approval request ID
            reason: Reason for rejection

        Returns:
            True if rejected successfully
        """
        request = self._pending_approvals.get(request_id)
        if not request:
            return False

        request.approved = False
        request.approved_at = datetime.utcnow()
        request.message = reason or "Plan rejected by user"

        return True

    def generate_clarification_prompt(
        self,
        session: ClarificationSession,
    ) -> str:
        """Generate formatted prompt for clarification questions.

        Args:
            session: Clarification session

        Returns:
            Formatted prompt string
        """
        lines = ["I need some clarification before proceeding:\n"]

        for i, question in enumerate(session.questions, 1):
            lines.append(f"{i}. {question.text}")

            if question.question_type == ClarificationType.MULTIPLE_CHOICE:
                for j, option in enumerate(question.options, ord('a')):
                    lines.append(f"   {chr(j)}) {option.get('label', option.get('value', ''))}")

            lines.append("")

        return "\n".join(lines)

    def parse_clarification_responses(
        self,
        session: ClarificationSession,
        user_input: str,
    ) -> dict[str, str]:
        """Parse user responses from natural language input.

        Args:
            session: Clarification session
            user_input: User's response text

        Returns:
            Dictionary of question_id -> response
        """
        responses = {}
        lines = user_input.strip().split("\n")

        for question in session.questions:
            # Try to find response in input
            for line in lines:
                line_lower = line.lower().strip()

                if question.question_type == ClarificationType.MULTIPLE_CHOICE:
                    # Check if user selected an option letter (a, b, c...)
                    for i, option in enumerate(question.options):
                        letter = chr(ord('a') + i)
                        if line_lower.startswith(f"{letter})") or line_lower == letter:
                            responses[question.id] = option.get("value", "")
                            break
                        # Check if they typed the option value
                        if option.get("value", "").lower() in line_lower:
                            responses[question.id] = option.get("value", "")
                            break
                        if option.get("label", "").lower() in line_lower:
                            responses[question.id] = option.get("value", "")
                            break

                elif question.question_type == ClarificationType.OPEN_ENDED:
                    # For open-ended, take the whole response
                    if question.term and question.term.lower() in line_lower:
                        # Extract the explanation after the term
                        responses[question.id] = line.strip()
                        break

                elif question.question_type == ClarificationType.CONFIRMATION:
                    if any(word in line_lower for word in ["yes", "approve", "ok", "proceed"]):
                        responses[question.id] = "yes"
                        break
                    elif any(word in line_lower for word in ["no", "reject", "cancel"]):
                        responses[question.id] = "no"
                        break

        return responses

    def format_approval_request(self, request: ApprovalRequest) -> str:
        """Format approval request for display.

        Args:
            request: Approval request

        Returns:
            Formatted string
        """
        lines = [
            "=" * 50,
            "EXECUTION PLAN APPROVAL REQUEST",
            "=" * 50,
            "",
            f"Objective: {request.plan.main_objective}",
            f"Confidence: {request.uncertainty_score:.0%}",
            "",
            "Tasks to Execute:",
        ]

        for i, task in enumerate(request.plan.tasks, 1):
            deps = f" (depends on: {', '.join(task.dependencies)})" if task.dependencies else ""
            lines.append(f"  {i}. [{task.task_type.value}] {task.description} [{task.estimated_time}]{deps}")

        lines.extend([
            "",
            request.message,
            "",
            "Do you approve this plan? (yes/no, or specify task numbers to remove)",
        ])

        return "\n".join(lines)

    def cleanup_session(self, session_id: str) -> None:
        """Clean up a completed session.

        Args:
            session_id: Session ID to clean up
        """
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]

    def cleanup_approval(self, request_id: str) -> None:
        """Clean up a processed approval request.

        Args:
            request_id: Request ID to clean up
        """
        if request_id in self._pending_approvals:
            del self._pending_approvals[request_id]

    def get_all_active_sessions(self) -> list[ClarificationSession]:
        """Get all active clarification sessions.

        Returns:
            List of active sessions
        """
        return list(self._active_sessions.values())

    def get_all_pending_approvals(self) -> list[ApprovalRequest]:
        """Get all pending approval requests.

        Returns:
            List of pending approvals
        """
        return [r for r in self._pending_approvals.values() if r.approved is None]
