import json
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import ExamQuestion, ExamSession, FinalGrade, get_db, init_db
from app.llm_service import final_grade, generate_question, grade_answer

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.filters["fromjson"] = lambda s: json.loads(s)

app = FastAPI(title="Modular Oral-Style Exam System", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


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


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.post("/exam/start", response_class=HTMLResponse)
def exam_start(
    request: Request,
    student_id: str = Form(...),
    professor_domain: str = Form(...),
    num_questions: int = Form(1),
    db: Session = Depends(get_db),
):
    student_id = student_id.strip()
    if not student_id:
        raise HTTPException(400, "Student ID required")
    n = max(1, min(20, int(num_questions)))

    session = ExamSession(
        student_id=student_id,
        professor_domain=professor_domain.strip(),
        num_questions_planned=n,
        current_question_index=0,
        status="in_progress",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    payload = generate_question(session.professor_domain, "", question_index=0)
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
    if not session or session.status != "in_progress":
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

    grade_payload = grade_answer(
        q.background_information,
        q.essay_question,
        q.grading_rubric,
        q.student_response,
        sec,
    )
    q.graded_state_p_json = json.dumps(grade_payload, ensure_ascii=False)
    db.add(q)

    next_index = idx + 1
    if next_index < session.num_questions_planned:
        db.commit()
        prior = _prior_summary(session, db)
        payload = generate_question(session.professor_domain, prior, question_index=next_index)
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
        db.commit()
        return RedirectResponse(url=f"/exam/{session_id}/question", status_code=303)

    # Final question done — aggregate grade
    db.commit()
    rows = (
        db.query(ExamQuestion)
        .filter(ExamQuestion.session_id == session.id)
        .order_by(ExamQuestion.question_index.asc())
        .all()
    )
    summaries = []
    for r in rows:
        if r.graded_state_p_json:
            summaries.append(
                {
                    "question_index": r.question_index,
                    "essay_question": r.essay_question,
                    "student_response": r.student_response,
                    "graded": json.loads(r.graded_state_p_json),
                }
            )
    final_payload = final_grade(summaries)
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
    db.commit()

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
    return templates.TemplateResponse(
        request,
        "results.html",
        {
            "session": session,
            "questions": rows,
            "final_grade": fg,
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
    graded = []
    for r in rows:
        gp = None
        if r.graded_state_p_json:
            try:
                gp = json.loads(r.graded_state_p_json)
            except json.JSONDecodeError:
                gp = None
        rubric = r.grading_rubric
        try:
            rubric = json.loads(r.grading_rubric)
        except json.JSONDecodeError:
            pass
        graded.append({"row": r, "grade": gp, "rubric": rubric})
    return templates.TemplateResponse(
        request,
        "professor_detail.html",
        {
            "session": session,
            "items": graded,
            "final_grade": fg,
        },
    )
