import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


class ExamSession(Base):
    __tablename__ = "exam_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(String(256), index=True)
    professor_domain: Mapped[str] = mapped_column(Text)
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


def _engine():
    url = get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


engine = _engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def dumps_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)
