# RubricGuidedEssayExam (RGEE) — Modular Oral-Style Exam System

A web app for **adaptive, oral-style exams**: students get essay questions tailored to a professor-provided domain, submit answers (optionally with time-on-question), and receive **LLM-assisted grading** against a structured rubric. Sessions and results are stored locally; instructors can review attempts from a simple dashboard.

## Features

- **Multi-question exams** (1–20 questions per session) with context carried across questions
- **Question generation** from a free-text “professor domain” plus prior questions in the session
- **Per-question grading** with rubric alignment and a **final aggregate grade** when the exam completes
- **Professor views** listing recent sessions and per-session detail (prompts, responses, grades)
- **Mock LLM mode** for development without API keys (`MOCK_LLM=1`, default in `run_dev.sh`)

## Stack

- Python 3.x · **FastAPI** · **Jinja2** · **SQLAlchemy** (SQLite by default)
- **Together AI** chat completions when not in mock mode (`TOGETHER_API_KEY`, model configurable)

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # set TOGETHER_API_KEY or rely on mock mode
./run_dev.sh                # or: uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) for the student flow; `/professor` for the instructor list.

## License

Add your license here if you publish the repo publicly.
