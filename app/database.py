import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from app.config import get_settings
from app.education_levels import DEFAULT_EDUCATION_LEVEL_ID


class Base(DeclarativeBase):
    pass


class ExamSession(Base):
    __tablename__ = "exam_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(String(256), index=True)
    professor_domain: Mapped[str] = mapped_column(Text)
    education_level: Mapped[str] = mapped_column(String(64), default=DEFAULT_EDUCATION_LEVEL_ID)
    use_mock_llm: Mapped[bool] = mapped_column(Boolean, default=True)
    num_questions_planned: Mapped[int] = mapped_column(Integer, default=1)
    current_question_index: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(64), default="in_progress")  # in_progress | completed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    final_grade_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    questions: Mapped[list["ExamQuestion"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    final_grade_row: Mapped["FinalGrade | None"] = relationship(back_populates="session", uselist=False)


class ExamQuestion(Base):
    __tablename__ = "exam_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("exam_sessions.id", ondelete="CASCADE"), index=True)
    question_index: Mapped[int] = mapped_column(Integer)
    background_information: Mapped[str] = mapped_column(Text)
    essay_question: Mapped[str] = mapped_column(Text)
    grading_rubric: Mapped[str] = mapped_column(Text)  # JSON list or text
    domain_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    student_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    seconds_on_question: Mapped[int | None] = mapped_column(Integer, nullable=True)
    graded_state_p_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # state P from spec

    session: Mapped["ExamSession"] = relationship(back_populates="questions")


class FinalGrade(Base):
    __tablename__ = "final_grades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("exam_sessions.id", ondelete="CASCADE"), unique=True)
    total_grade_percent: Mapped[float] = mapped_column()
    explanation: Mapped[str] = mapped_column(Text)
    summary_json: Mapped[str] = mapped_column(Text)  # full LLM payload

    session: Mapped["ExamSession"] = relationship(back_populates="final_grade_row")


class PerformanceLog(Base):
    """Diagnostics: HTTP request duration, LLM call duration, client-reported UX timing."""

    __tablename__ = "performance_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    category: Mapped[str] = mapped_column(String(32), index=True)  # http | llm | client
    event_name: Mapped[str] = mapped_column(String(512))
    duration_ms: Mapped[float] = mapped_column(Float)
    exam_session_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    meta_json: Mapped[str | None] = mapped_column(Text, nullable=True)


def _engine():
    url = get_settings().database_url
    connect_args = (
        {
            "check_same_thread": False,
            "timeout": 20,
        }
        if url.startswith("sqlite")
        else {}
    )
    eng = create_engine(url, connect_args=connect_args)
    if url.startswith("sqlite"):
        @event.listens_for(eng, "connect")
        def _set_sqlite_pragmas(dbapi_connection, _connection_record):
            cur = dbapi_connection.cursor()
            # WAL + busy timeout reduces "database is locked" during rapid writes.
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA synchronous=NORMAL")
            cur.execute("PRAGMA busy_timeout=20000")
            cur.close()
    return eng


engine = _engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _migrate_sqlite_schema() -> None:
    if not str(engine.url).startswith("sqlite"):
        return
    with engine.begin() as conn:
        try:
            conn.execute(
                text(
                    "ALTER TABLE exam_sessions ADD COLUMN education_level VARCHAR(64) NOT NULL DEFAULT '"
                    + DEFAULT_EDUCATION_LEVEL_ID
                    + "'"
                )
            )
        except Exception as e:
            msg = str(e).lower()
            if "duplicate column" not in msg and "already exists" not in msg:
                raise
        try:
            conn.execute(
                text("ALTER TABLE exam_sessions ADD COLUMN use_mock_llm INTEGER NOT NULL DEFAULT 1")
            )
        except Exception as e:
            msg = str(e).lower()
            if "duplicate column" not in msg and "already exists" not in msg:
                raise


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_sqlite_schema()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def dumps_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)
