import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import ExamQuestion, ExamSession, FinalGrade, PerformanceLog, get_db, init_db
from app.perf_logging import log_performance_event
from app.errors import TogetherApiError
from app.education_levels import (
    ALLOWED_LEVEL_IDS,
    DEFAULT_EDUCATION_LEVEL_ID,
    EDUCATION_LEVELS,
    label_for_level,
)
from app.llm_service import generate_question, grade_and_final_combined, grade_and_next_question_combined

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.filters["fromjson"] = lambda s: json.loads(s)
templates.env.filters["level_label"] = label_for_level

_EXAM_ID_IN_PATH = re.compile(r"^/(?:exam|professor/exam)/(\d+)(?:/|$)")


def _exam_session_id_from_path(path: str) -> int | None:
    m = _EXAM_ID_IN_PATH.match(path or "")
    return int(m.group(1)) if m else None


def _exam_session_id_for_http_log(path: str, response: Response | None) -> int | None:
    sid = _exam_session_id_from_path(path)
    if sid is not None:
        return sid
    if response is not None and path == "/exam/start":
        loc = response.headers.get("location") or response.headers.get("Location")
        if loc:
            pth = urlparse(loc).path if "://" in loc else loc.split("?", 1)[0]
            return _exam_session_id_from_path(pth)
    return None


app = FastAPI(title="Modular Oral-Style Exam System", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.middleware("http")
async def log_http_timing(request: Request, call_next):
    if request.url.path.startswith("/static"):
        return await call_next(request)
    start = time.perf_counter()
    status: int | str = "error"
    path = request.url.path
    response: Response | None = None
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        exam_session_id = _exam_session_id_for_http_log(path, response)
        log_performance_event(
            "http",
            f"{request.method} {path}",
            (time.perf_counter() - start) * 1000,
            exam_session_id=exam_session_id,
            meta={"status_code": status},
        )

POINTS_PER_QUESTION = 10.0


@app.exception_handler(TogetherApiError)
async def together_api_error_handler(request: Request, exc: TogetherApiError):
    """Return friendly HTML for Together.ai failures."""
    return templates.TemplateResponse(
        request,
        "error.html",
        {"message": "We could not complete that action right now. Please try again."},
        status_code=exc.http_status,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Render HTML error pages so users never see raw API JSON errors."""
    status_code = exc.status_code if isinstance(exc.status_code, int) else 500
    message = "We could not complete that action. Please try again."
    if status_code == 404:
        message = "We could not find that page."
    elif status_code < 500:
        message = "There was a problem with that request. Please check your input and try again."
    return templates.TemplateResponse(
        request,
        "error.html",
        {"message": message},
        status_code=status_code,
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    """Return friendly HTML for validation issues."""
    return templates.TemplateResponse(
        request,
        "error.html",
        {"message": "Some required information is missing or invalid. Please try again."},
        status_code=422,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Final safety net to avoid exposing internal errors to users."""
    return templates.TemplateResponse(
        request,
        "error.html",
        {"message": "Something went wrong on our side. Please try again in a moment."},
        status_code=500,
    )


@app.on_event("startup")
def _startup():
    init_db()


def _rubric_to_stored(rubric: list | str) -> str:
    if isinstance(rubric, list):
        return json.dumps(rubric, ensure_ascii=False)
    return str(rubric)


def _prior_summary(session: ExamSession, db: Session) -> str:
    rows = (
        db.query(ExamQuestion)
        .filter(ExamQuestion.session_id == session.id)
        .order_by(ExamQuestion.question_index.asc())
        .all()
    )
    if not rows:
        return ""
    parts = []
    for r in rows:
        parts.append(f"[Q{r.question_index + 1}] {r.essay_question[:400]}")
    return "\n".join(parts)


def _earlier_graded_blob(db: Session, session: ExamSession, before_index: int) -> str:
    """Text block of essay + response + grade JSON for questions before index (for combined final prompt)."""
    rows = (
        db.query(ExamQuestion)
        .filter(
            ExamQuestion.session_id == session.id,
            ExamQuestion.question_index < before_index,
        )
        .order_by(ExamQuestion.question_index.asc())
        .all()
    )
    if not rows:
        return ""
    parts = []
    for r in rows:
        parts.append(
            f"--- Question {r.question_index + 1} ---\n"
            f"Essay: {r.essay_question}\n"
            f"Student response: {r.student_response or ''}\n"
            f"Grading JSON: {r.graded_state_p_json or '(none)'}"
        )
    return "\n\n".join(parts)


def _safe_json_dict(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _rubric_items(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed if str(x).strip()]
    except json.JSONDecodeError:
        pass
    text = str(raw).strip()
    return [text] if text else []


def _best_dimension_match(dimension_scores: dict, criterion: str, index: int) -> tuple[str, float | None]:
    if not isinstance(dimension_scores, dict) or not dimension_scores:
        return (f"Criterion {index + 1}", None)
    criterion_words = {w for w in criterion.lower().split() if len(w) > 3}
    for key, value in dimension_scores.items():
        key_words = {w for w in str(key).lower().replace("_", " ").split() if len(w) > 3}
        if criterion_words and key_words and criterion_words.intersection(key_words):
            try:
                return (str(key).replace("_", " ").title(), float(value))
            except (TypeError, ValueError):
                return (str(key).replace("_", " ").title(), None)
    key = list(dimension_scores.keys())[index % len(dimension_scores)]
    try:
        return (str(key).replace("_", " ").title(), float(dimension_scores[key]))
    except (TypeError, ValueError):
        return (str(key).replace("_", " ").title(), None)


def _reference_answer_text(grade_payload: dict, rubric: list[str]) -> str:
    for key in ("reference_answer", "ideal_answer", "model_answer", "expected_answer"):
        value = grade_payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if not rubric:
        return "A strong answer should be clear, accurate, and directly address the question prompt."
    joined = "; ".join(rubric)
    return f"A strong answer should cover: {joined}."


def _first_nonempty_str(payload: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _list_or_text(payload: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, list):
            items = [str(v).strip() for v in value if str(v).strip()]
            if items:
                return "\n".join(f"- {item}" for item in items)
    return ""


def _rubric_feedback_sections(
    grade_payload: dict, rubric_breakdown: list[dict], rubric: list[str]
) -> dict[str, str]:
    strengths = _list_or_text(
        grade_payload,
        (
            "strengths",
            "strength",
            "what_went_well",
            "positive_feedback",
            "strong_points",
        ),
    )
    improvements = _list_or_text(
        grade_payload,
        (
            "areas_for_improvement",
            "improvements",
            "weaknesses",
            "gaps",
            "needs_improvement",
        ),
    )
    suggestions = _list_or_text(
        grade_payload,
        ("suggestions", "recommendations", "next_steps", "study_suggestions"),
    )
    if not strengths:
        strong_rows = [
            row for row in rubric_breakdown if row.get("score") is not None and float(row["score"]) >= 80
        ]
        if strong_rows:
            strengths = "\n".join(
                f"- {row['criterion']} ({float(row['score']):.1f}%)"
                for row in strong_rows[:3]
            )
        elif rubric:
            strengths = f"- {rubric[0]}"
        else:
            overall = grade_payload.get("overall_percent")
            if isinstance(overall, (int, float)) and float(overall) >= 70:
                strengths = "- Demonstrates a solid baseline understanding of the prompt."
            else:
                strengths = "- Attempts to address the prompt and key concepts."
    if not improvements:
        low_rows = [
            row for row in rubric_breakdown if row.get("score") is not None and float(row["score"]) < 80
        ]
        if low_rows:
            improvements = "\n".join(
                f"- {row['criterion']} ({float(row['score']):.1f}%)"
                for row in low_rows[:3]
            )
        elif rubric:
            improvements = f"- {rubric[min(1, len(rubric) - 1)]}"
        else:
            improvements = "- Needs clearer evidence and tighter alignment to the prompt."
    if not suggestions:
        suggestion_lines = []
        for row in rubric_breakdown:
            if row.get("score") is not None and float(row["score"]) < 80:
                suggestion_lines.append(f"{row['criterion']}.")
        if suggestion_lines:
            suggestions = "- Add clearer support for:\n\n" + "\n".join(suggestion_lines[:3])
        else:
            suggestions = (
                "- Keep the response structure clear and focused.\n"
                "- Support each claim with concrete examples.\n"
                "- Map each paragraph directly to rubric criteria."
            )
    return {
        "strengths": strengths or "No strengths were explicitly returned by the grader.",
        "areas_for_improvement": improvements,
        "suggestions": suggestions,
    }


def _overall_final_summary(final_grade_row: FinalGrade | None) -> str:
    if not final_grade_row:
        return "Final summary is not available yet."
    parsed = _safe_json_dict(final_grade_row.summary_json)
    text = _first_nonempty_str(
        parsed,
        ("overall_final_summary", "final_summary", "summary", "explanation"),
    )
    if text:
        return text
    if final_grade_row.explanation:
        return final_grade_row.explanation
    return "Final summary is not available yet."


def _points_from_percent(percent: float | int | None, points_possible: float) -> float:
    if percent is None:
        return 0.0
    try:
        pct = float(percent)
    except (TypeError, ValueError):
        pct = 0.0
    pct = max(0.0, min(100.0, pct))
    return round((pct / 100.0) * points_possible, 1)


def _is_sqlite_locked_error(exc: Exception) -> bool:
    return "database is locked" in str(exc).lower()


@app.post("/exam/{session_id}/client-timing")
def exam_client_timing(
    session_id: int,
    client_ms_wall: str = Form(...),
    db: Session = Depends(get_db),
):
    session = db.get(ExamSession, session_id)
    if not session:
        raise HTTPException(404, "Exam not found")
    try:
        ms = float(client_ms_wall)
    except (TypeError, ValueError):
        raise HTTPException(400, "Invalid timing value")
    ms = max(0.0, min(ms, 3_600_000.0))
    log_performance_event(
        "client",
        "generate_click_to_first_question_visible",
        ms,
        exam_session_id=session_id,
        meta={
            "description": "Wall-clock ms from Generate first question click until first question page runs in the browser.",
        },
    )
    return Response(status_code=204)


@app.get("/performance-log", response_class=HTMLResponse)
def performance_log(request: Request, db: Session = Depends(get_db)):
    rows = (
        db.query(PerformanceLog)
        .order_by(PerformanceLog.id.desc())
        .limit(400)
        .all()
    )
    return templates.TemplateResponse(
        request,
        "performance_log.html",
        {"rows": rows},
    )


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    s = get_settings()
    has_key = bool(str(s.together_api_key or "").strip())
    default_toggle_mock = not has_key or s.mock_llm
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "education_levels": EDUCATION_LEVELS,
            "default_level": DEFAULT_EDUCATION_LEVEL_ID,
            "api_key_configured": has_key,
            "default_toggle_mock": default_toggle_mock,
        },
    )


@app.post("/exam/start", response_class=HTMLResponse)
def exam_start(
    request: Request,
    student_id: str = Form(...),
    professor_domain: str = Form(...),
    education_level: str = Form(DEFAULT_EDUCATION_LEVEL_ID),
    llm_mode: str = Form("mock"),
    num_questions: int = Form(1),
    db: Session = Depends(get_db),
):
    student_id = student_id.strip()
    if not student_id:
        raise HTTPException(400, "Student ID required")
    level_key = education_level.strip().lower()
    if level_key not in ALLOWED_LEVEL_IDS:
        raise HTTPException(400, "Invalid education level")
    mode = llm_mode.strip().lower()
    use_mock = mode != "live"
    if not use_mock and not str(get_settings().together_api_key or "").strip():
        raise HTTPException(
            400,
            "Production mode requires TOGETHER_API_KEY in the server .env file.",
        )
    n = max(1, min(20, int(num_questions)))

    session = ExamSession(
        student_id=student_id,
        professor_domain=professor_domain.strip(),
        education_level=level_key,
        use_mock_llm=use_mock,
        num_questions_planned=n,
        current_question_index=0,
        status="in_progress",
    )
    db.add(session)
    try:
        db.flush()
        payload = generate_question(
            session.professor_domain,
            "",
            question_index=0,
            education_level=session.education_level,
            use_mock=session.use_mock_llm,
            exam_session_id=session.id,
        )
    except TogetherApiError:
        db.rollback()
        raise
    eq = ExamQuestion(
        session_id=session.id,
        question_index=0,
        background_information=payload.get("background_information", ""),
        essay_question=payload.get("essay_question", ""),
        grading_rubric=_rubric_to_stored(payload.get("grading_rubric", [])),
        domain_notes=payload.get("domain_notes"),
    )
    db.add(eq)
    db.commit()

    return RedirectResponse(url=f"/exam/{session.id}/question", status_code=303)


@app.get("/exam/{session_id}/question", response_class=HTMLResponse)
def exam_question(request: Request, session_id: int, db: Session = Depends(get_db)):
    session = db.get(ExamSession, session_id)
    if not session:
        raise HTTPException(404, "Exam not found")
    if session.status != "in_progress":
        return RedirectResponse(url=f"/exam/{session_id}/results", status_code=303)

    idx = session.current_question_index
    q = (
        db.query(ExamQuestion)
        .filter(ExamQuestion.session_id == session.id, ExamQuestion.question_index == idx)
        .one_or_none()
    )
    if not q:
        raise HTTPException(404, "Question not found")

    rubric_display = q.grading_rubric
    try:
        rubric_display = json.loads(q.grading_rubric)
        if isinstance(rubric_display, list):
            rubric_display = rubric_display
        else:
            rubric_display = q.grading_rubric
    except json.JSONDecodeError:
        rubric_display = q.grading_rubric

    return templates.TemplateResponse(
        request,
        "question.html",
        {
            "session": session,
            "question": q,
            "question_number": idx + 1,
            "total_planned": session.num_questions_planned,
            "rubric_display": rubric_display,
            "education_label": label_for_level(session.education_level),
            "llm_mode_label": "Mock" if session.use_mock_llm else "Production",
        },
    )


@app.post("/exam/{session_id}/answer", response_class=HTMLResponse)
def exam_answer(
    request: Request,
    session_id: int,
    answer: str = Form(...),
    seconds_on_question: str = Form(""),
    db: Session = Depends(get_db),
):
    session = db.get(ExamSession, session_id)
    if not session:
        raise HTTPException(404, "Exam not found")
    # Idempotent: duplicate POST after exam is finished → send user to results (no error).
    if session.status == "completed":
        return RedirectResponse(url=f"/exam/{session_id}/results", status_code=303)
    if session.status != "in_progress":
        raise HTTPException(400, "Invalid session")

    idx = session.current_question_index
    q = (
        db.query(ExamQuestion)
        .filter(ExamQuestion.session_id == session.id, ExamQuestion.question_index == idx)
        .one_or_none()
    )
    if not q:
        raise HTTPException(404, "Question not found")

    sec = None
    if seconds_on_question.strip().isdigit():
        sec = int(seconds_on_question.strip())

    q.student_response = answer.strip()
    q.seconds_on_question = sec

    next_index = idx + 1

    if next_index < session.num_questions_planned:
        # Idempotent: another request may have already created the next question (double-submit).
        existing_next = (
            db.query(ExamQuestion)
            .filter(
                ExamQuestion.session_id == session.id,
                ExamQuestion.question_index == next_index,
            )
            .one_or_none()
        )
        if existing_next:
            db.refresh(session)
            if session.current_question_index != next_index:
                session.current_question_index = next_index
                db.add(session)
                db.commit()
            return RedirectResponse(url=f"/exam/{session_id}/question", status_code=303)

        try:
            db.flush()
        except OperationalError as exc:
            db.rollback()
            if _is_sqlite_locked_error(exc):
                return RedirectResponse(url=f"/exam/{session_id}/question", status_code=303)
            raise

        try:
            prior = _prior_summary(session, db)
            grade_payload, payload = grade_and_next_question_combined(
                session.professor_domain,
                prior,
                next_question_index=next_index,
                background_information=q.background_information,
                essay_question=q.essay_question,
                grading_rubric=q.grading_rubric,
                student_response=q.student_response,
                seconds_on_question=sec,
                education_level=session.education_level,
                use_mock=session.use_mock_llm,
                exam_session_id=session.id,
            )
        except TogetherApiError:
            db.rollback()
            raise
        q.graded_state_p_json = json.dumps(grade_payload, ensure_ascii=False)
        db.add(q)
        nq = ExamQuestion(
            session_id=session.id,
            question_index=next_index,
            background_information=payload.get("background_information", ""),
            essay_question=payload.get("essay_question", ""),
            grading_rubric=_rubric_to_stored(payload.get("grading_rubric", [])),
            domain_notes=payload.get("domain_notes"),
        )
        db.add(nq)
        session.current_question_index = next_index
        db.add(session)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return RedirectResponse(url=f"/exam/{session_id}/question", status_code=303)
        except OperationalError as exc:
            db.rollback()
            if _is_sqlite_locked_error(exc):
                return RedirectResponse(url=f"/exam/{session_id}/question", status_code=303)
            raise
        return RedirectResponse(url=f"/exam/{session_id}/question", status_code=303)

    # Last question: one API call for this answer’s grade + overall final grade (was two calls)
    existing_fg = (
        db.query(FinalGrade).filter(FinalGrade.session_id == session.id).one_or_none()
    )
    if existing_fg:
        session.status = "completed"
        session.final_grade_json = existing_fg.summary_json
        db.add(session)
        db.commit()
        return RedirectResponse(url=f"/exam/{session_id}/results", status_code=303)

    try:
        db.flush()
    except OperationalError as exc:
        db.rollback()
        if _is_sqlite_locked_error(exc):
            return RedirectResponse(url=f"/exam/{session_id}/question", status_code=303)
        raise
    earlier = _earlier_graded_blob(db, session, idx)
    try:
        grade_payload, final_payload = grade_and_final_combined(
            earlier,
            q.background_information,
            q.essay_question,
            q.grading_rubric,
            q.student_response,
            sec,
            education_level=session.education_level,
            use_mock=session.use_mock_llm,
            exam_session_id=session.id,
        )
    except TogetherApiError:
        db.rollback()
        raise
    q.graded_state_p_json = json.dumps(grade_payload, ensure_ascii=False)
    db.add(q)
    fg = FinalGrade(
        session_id=session.id,
        total_grade_percent=float(final_payload.get("total_grade_percent", 0)),
        explanation=final_payload.get("explanation", ""),
        summary_json=json.dumps(final_payload, ensure_ascii=False),
    )
    db.add(fg)
    session.status = "completed"
    session.final_grade_json = fg.summary_json
    db.add(session)
    try:
        db.commit()
    except IntegrityError:
        # Concurrent last answer: another request inserted final_grades first.
        db.rollback()
        if db.query(FinalGrade).filter(FinalGrade.session_id == session_id).one_or_none():
            return RedirectResponse(url=f"/exam/{session_id}/results", status_code=303)
        raise
    except OperationalError as exc:
        db.rollback()
        if _is_sqlite_locked_error(exc):
            if db.query(FinalGrade).filter(FinalGrade.session_id == session_id).one_or_none():
                return RedirectResponse(url=f"/exam/{session_id}/results", status_code=303)
            return RedirectResponse(url=f"/exam/{session_id}/question", status_code=303)
        raise

    return RedirectResponse(url=f"/exam/{session_id}/results", status_code=303)


@app.get("/exam/{session_id}/results", response_class=HTMLResponse)
def exam_results(request: Request, session_id: int, db: Session = Depends(get_db)):
    session = db.get(ExamSession, session_id)
    if not session:
        raise HTTPException(404, "Exam not found")
    rows = (
        db.query(ExamQuestion)
        .filter(ExamQuestion.session_id == session.id)
        .order_by(ExamQuestion.question_index.asc())
        .all()
    )
    fg = db.query(FinalGrade).filter(FinalGrade.session_id == session.id).one_or_none()
    total_points_possible = round(max(1, session.num_questions_planned) * POINTS_PER_QUESTION, 1)
    overall_points_earned = _points_from_percent(
        fg.total_grade_percent if fg else 0.0, total_points_possible
    )
    result_items = []
    for q in rows:
        grade_payload = _safe_json_dict(q.graded_state_p_json)
        rubric = _rubric_items(q.grading_rubric)
        dimension_scores = grade_payload.get("dimension_scores", {})
        rubric_breakdown = []
        for idx, criterion in enumerate(rubric):
            label, score = _best_dimension_match(dimension_scores, criterion, idx)
            rubric_breakdown.append(
                {
                    "criterion": criterion,
                    "dimension_label": label,
                    "score": score,
                }
            )
        result_items.append(
            {
                "question": q,
                "grade": grade_payload,
                "rubric": rubric,
                "rubric_breakdown": rubric_breakdown,
                "reference_answer": _reference_answer_text(grade_payload, rubric),
                "rubric_feedback": _rubric_feedback_sections(
                    grade_payload, rubric_breakdown, rubric
                ),
                "points_earned": _points_from_percent(
                    grade_payload.get("overall_percent"), POINTS_PER_QUESTION
                ),
                "points_possible": POINTS_PER_QUESTION,
            }
        )
    return templates.TemplateResponse(
        request,
        "results.html",
        {
            "session": session,
            "questions": rows,
            "result_items": result_items,
            "final_grade": fg,
            "overall_final_summary": _overall_final_summary(fg),
            "overall_points_earned": overall_points_earned,
            "overall_points_possible": total_points_possible,
            "education_label": label_for_level(session.education_level),
            "llm_mode_label": "Mock" if session.use_mock_llm else "Production",
        },
    )


@app.get("/professor", response_class=HTMLResponse)
def professor_dashboard(request: Request, db: Session = Depends(get_db)):
    sessions = db.query(ExamSession).order_by(ExamSession.created_at.desc()).limit(200).all()
    return templates.TemplateResponse(request, "professor.html", {"sessions": sessions})


@app.get("/professor/exam/{session_id}", response_class=HTMLResponse)
def professor_exam_detail(request: Request, session_id: int, db: Session = Depends(get_db)):
    session = db.get(ExamSession, session_id)
    if not session:
        raise HTTPException(404, "Not found")
    rows = (
        db.query(ExamQuestion)
        .filter(ExamQuestion.session_id == session.id)
        .order_by(ExamQuestion.question_index.asc())
        .all()
    )
    fg = db.query(FinalGrade).filter(FinalGrade.session_id == session.id).one_or_none()
    total_points_possible = round(max(1, session.num_questions_planned) * POINTS_PER_QUESTION, 1)
    overall_points_earned = _points_from_percent(
        fg.total_grade_percent if fg else 0.0, total_points_possible
    )
    graded = []
    for r in rows:
        gp = _safe_json_dict(r.graded_state_p_json)
        rubric = _rubric_items(r.grading_rubric)
        dimension_scores = gp.get("dimension_scores", {})
        rubric_breakdown = []
        for idx, criterion in enumerate(rubric):
            label, score = _best_dimension_match(dimension_scores, criterion, idx)
            rubric_breakdown.append(
                {
                    "criterion": criterion,
                    "dimension_label": label,
                    "score": score,
                }
            )
        graded.append(
            {
                "row": r,
                "grade": gp,
                "rubric": rubric,
                "rubric_breakdown": rubric_breakdown,
                "reference_answer": _reference_answer_text(gp, rubric),
                "rubric_feedback": _rubric_feedback_sections(gp, rubric_breakdown, rubric),
                "points_earned": _points_from_percent(
                    gp.get("overall_percent"), POINTS_PER_QUESTION
                ),
                "points_possible": POINTS_PER_QUESTION,
            }
        )
    return templates.TemplateResponse(
        request,
        "professor_detail.html",
        {
            "session": session,
            "items": graded,
            "final_grade": fg,
            "overall_final_summary": _overall_final_summary(fg),
            "overall_points_earned": overall_points_earned,
            "overall_points_possible": total_points_possible,
        },
    )
