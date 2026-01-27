"""Database management for PostgreSQL and SQLite interaction storage."""

import json
import logging
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Optional

import pandas as pd
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

Base = declarative_base()


class Conversation(Base):
    """Stores user conversations and query metadata."""

    __tablename__ = "conversations"

    conversation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_query = Column(Text, nullable=False)
    parsed_intent = Column(JSONB)
    uncertainty_score = Column(Float)
    plan = Column(JSONB)
    status = Column(String(20), default="pending")
    result_summary = Column(Text)


class Clarification(Base):
    """Stores clarification questions and user responses."""

    __tablename__ = "clarifications"

    clarification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50))
    options = Column(JSONB)
    user_response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    """Stores user feedback on query results."""

    __tablename__ = "feedback"

    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False)
    rating = Column(Integer)
    was_accurate = Column(Boolean)
    was_helpful = Column(Boolean)
    comments = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExecutionLog(Base):
    """Stores execution details for audit trail."""

    __tablename__ = "execution_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False)
    task_id = Column(String(50))
    task_type = Column(String(50))
    executed_code = Column(Text)
    execution_time_ms = Column(Integer)
    rows_returned = Column(Integer)
    status = Column(String(20))
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(
        self,
        postgres_url: Optional[str] = None,
        sqlite_path: Optional[Path] = None,
    ):
        """Initialize database manager.

        Args:
            postgres_url: PostgreSQL connection string for user data
            sqlite_path: Path to SQLite database for interaction storage
        """
        self.postgres_url = postgres_url
        self.sqlite_path = sqlite_path or Path("./data/interactions.db")

        self._postgres_engine: Optional[Engine] = None
        self._sqlite_engine: Optional[Engine] = None

    def _get_postgres_engine(self) -> Engine:
        """Get or create PostgreSQL engine."""
        if self._postgres_engine is None:
            if not self.postgres_url:
                raise ValueError("PostgreSQL URL not configured")
            self._postgres_engine = create_engine(
                self.postgres_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
            )
        return self._postgres_engine

    def _get_sqlite_engine(self) -> Engine:
        """Get or create SQLite engine for interaction storage."""
        if self._sqlite_engine is None:
            self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            self._sqlite_engine = create_engine(
                f"sqlite:///{self.sqlite_path}",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
            # Create tables if they don't exist
            Base.metadata.create_all(self._sqlite_engine)
        return self._sqlite_engine

    @contextmanager
    def postgres_session(self) -> Generator[Session, None, None]:
        """Context manager for PostgreSQL sessions."""
        engine = self._get_postgres_engine()
        session_factory = sessionmaker(bind=engine)
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def sqlite_session(self) -> Generator[Session, None, None]:
        """Context manager for SQLite sessions."""
        engine = self._get_sqlite_engine()
        session_factory = sessionmaker(bind=engine)
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def execute_sql(
        self,
        query: str,
        params: Optional[dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """Execute SQL query against PostgreSQL and return DataFrame.

        Args:
            query: SQL query string (parameterized)
            params: Query parameters

        Returns:
            DataFrame with query results
        """
        engine = self._get_postgres_engine()
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            columns = result.keys()
            data = result.fetchall()
            return pd.DataFrame(data, columns=columns)

    def create_table_from_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        if_exists: str = "replace",
    ) -> None:
        """Create PostgreSQL table from DataFrame.

        Args:
            df: DataFrame to store
            table_name: Target table name
            if_exists: How to handle existing table ('replace', 'append', 'fail')
        """
        engine = self._get_postgres_engine()
        df.to_sql(table_name, engine, if_exists=if_exists, index=False)
        logger.info(f"Created table '{table_name}' with {len(df)} rows")

    def get_table_schema(self, table_name: str) -> dict[str, Any]:
        """Get schema information for a table.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with column names, types, and statistics
        """
        engine = self._get_postgres_engine()

        # Get column information
        query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = :table_name
        ORDER BY ordinal_position
        """

        with engine.connect() as conn:
            result = conn.execute(text(query), {"table_name": table_name})
            columns = {
                row[0]: {"type": row[1], "nullable": row[2] == "YES"}
                for row in result.fetchall()
            }

        return {"table_name": table_name, "columns": columns}

    def get_data_profile(self, table_name: str) -> dict[str, Any]:
        """Generate data profile for a table.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with column statistics
        """
        schema = self.get_table_schema(table_name)
        profile = {"table_name": table_name, "columns": {}}

        for col_name, col_info in schema["columns"].items():
            # Get null rate and basic stats
            query = f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN "{col_name}" IS NULL THEN 1 ELSE 0 END) as nulls
            FROM "{table_name}"
            """

            engine = self._get_postgres_engine()
            with engine.connect() as conn:
                result = conn.execute(text(query)).fetchone()
                total = result[0] or 0
                nulls = result[1] or 0

                profile["columns"][col_name] = {
                    **col_info,
                    "null_rate": nulls / total if total > 0 else 0,
                    "coverage": 1 - (nulls / total) if total > 0 else 0,
                }

        return profile

    def list_tables(self) -> list[str]:
        """List all user tables in PostgreSQL."""
        query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
        """
        engine = self._get_postgres_engine()
        with engine.connect() as conn:
            result = conn.execute(text(query))
            return [row[0] for row in result.fetchall()]

    # Interaction storage methods

    def create_conversation(
        self,
        user_query: str,
        parsed_intent: Optional[dict] = None,
        uncertainty_score: Optional[float] = None,
    ) -> uuid.UUID:
        """Create a new conversation record.

        Args:
            user_query: Original user query
            parsed_intent: Parsed intent from LLM
            uncertainty_score: Calculated uncertainty score

        Returns:
            UUID of the created conversation
        """
        conversation_id = uuid.uuid4()

        with self.sqlite_session() as session:
            conversation = Conversation(
                conversation_id=conversation_id,
                user_query=user_query,
                parsed_intent=parsed_intent,
                uncertainty_score=uncertainty_score,
            )
            session.add(conversation)

        return conversation_id

    def update_conversation(
        self,
        conversation_id: uuid.UUID,
        **kwargs: Any,
    ) -> None:
        """Update conversation fields.

        Args:
            conversation_id: Conversation UUID
            **kwargs: Fields to update
        """
        with self.sqlite_session() as session:
            session.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).update(kwargs)

    def add_clarification(
        self,
        conversation_id: uuid.UUID,
        question_text: str,
        question_type: str,
        options: Optional[list[dict]] = None,
    ) -> uuid.UUID:
        """Add a clarification question.

        Args:
            conversation_id: Parent conversation UUID
            question_text: The clarification question
            question_type: 'multiple_choice' or 'open_ended'
            options: List of options for multiple choice

        Returns:
            UUID of the created clarification
        """
        clarification_id = uuid.uuid4()

        with self.sqlite_session() as session:
            clarification = Clarification(
                clarification_id=clarification_id,
                conversation_id=conversation_id,
                question_text=question_text,
                question_type=question_type,
                options=options,
            )
            session.add(clarification)

        return clarification_id

    def record_clarification_response(
        self,
        clarification_id: uuid.UUID,
        response: str,
    ) -> None:
        """Record user response to clarification.

        Args:
            clarification_id: Clarification UUID
            response: User's response
        """
        with self.sqlite_session() as session:
            session.query(Clarification).filter(
                Clarification.clarification_id == clarification_id
            ).update({"user_response": response})

    def add_execution_log(
        self,
        conversation_id: uuid.UUID,
        task_id: str,
        task_type: str,
        executed_code: str,
        execution_time_ms: int,
        rows_returned: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> uuid.UUID:
        """Log task execution details.

        Args:
            conversation_id: Parent conversation UUID
            task_id: Task identifier
            task_type: Type of task ('sql', 'python', 'visualization')
            executed_code: Code that was executed
            execution_time_ms: Execution time in milliseconds
            rows_returned: Number of rows returned (for SQL)
            status: 'success' or 'failed'
            error_message: Error message if failed

        Returns:
            UUID of the created log entry
        """
        log_id = uuid.uuid4()

        with self.sqlite_session() as session:
            log_entry = ExecutionLog(
                log_id=log_id,
                conversation_id=conversation_id,
                task_id=task_id,
                task_type=task_type,
                executed_code=executed_code,
                execution_time_ms=execution_time_ms,
                rows_returned=rows_returned,
                status=status,
                error_message=error_message,
            )
            session.add(log_entry)

        return log_id

    def add_feedback(
        self,
        conversation_id: uuid.UUID,
        rating: int,
        was_accurate: bool,
        was_helpful: bool,
        comments: Optional[str] = None,
    ) -> uuid.UUID:
        """Record user feedback.

        Args:
            conversation_id: Conversation UUID
            rating: Rating (1-5)
            was_accurate: Whether result was accurate
            was_helpful: Whether result was helpful
            comments: Optional user comments

        Returns:
            UUID of the created feedback entry
        """
        feedback_id = uuid.uuid4()

        with self.sqlite_session() as session:
            feedback = Feedback(
                feedback_id=feedback_id,
                conversation_id=conversation_id,
                rating=rating,
                was_accurate=was_accurate,
                was_helpful=was_helpful,
                comments=comments,
            )
            session.add(feedback)

        return feedback_id

    def get_conversation_history(
        self,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get recent conversation history.

        Args:
            limit: Maximum number of conversations to return

        Returns:
            List of conversation records
        """
        with self.sqlite_session() as session:
            conversations = (
                session.query(Conversation)
                .order_by(Conversation.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "conversation_id": str(c.conversation_id),
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "user_query": c.user_query,
                    "status": c.status,
                    "uncertainty_score": c.uncertainty_score,
                }
                for c in conversations
            ]

    def close(self) -> None:
        """Close all database connections."""
        if self._postgres_engine:
            self._postgres_engine.dispose()
        if self._sqlite_engine:
            self._sqlite_engine.dispose()
