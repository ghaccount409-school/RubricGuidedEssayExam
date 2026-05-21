"""
Software requirements (Section 5 format) aligned with the *as-implemented* RGEE codebase,
not a forward-looking capstone wish list. Run:

  python docs/generate_rgee_requirements_as_implemented_docx.py

Writes: docs/RGEE_Requirements_As_Implemented_Section5.docx

Repository: https://github.com/ALGeek01/RubricGuidedEssayExam
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

DOCS = Path(__file__).resolve().parent
OUT = DOCS / "RGEE_Requirements_As_Implemented_Section5.docx"

CONTENT_TYPES_DOCX = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

RELS_ROOT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:lang w:val="en-US"/></w:rPr></w:rPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:styleId="Normal" w:default="1"><w:name w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="240" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:sz w:val="36"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="200" w:after="80"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="120" w:after="60"/><w:outlineLvl w:val="2"/></w:pPr><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>
</w:styles>"""


def _w_p(text: str) -> str:
    return (
        f'<w:p><w:pPr><w:spacing w:after="80"/></w:pPr>'
        f'<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'
    )


def _w_h1(text: str) -> str:
    return (
        f'<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
        f'<w:r><w:t>{escape(text)}</w:t></w:r></w:p>'
    )


def _w_h2(text: str) -> str:
    return (
        f'<w:p><w:pPr><w:pStyle w:val="Heading2"/></w:pPr>'
        f'<w:r><w:t>{escape(text)}</w:t></w:r></w:p>'
    )


def _w_h3(text: str) -> str:
    return (
        f'<w:p><w:pPr><w:pStyle w:val="Heading3"/></w:pPr>'
        f'<w:r><w:t>{escape(text)}</w:t></w:r></w:p>'
    )


def _w_bullet(text: str) -> str:
    return (
        f'<w:p><w:pPr><w:spacing w:after="40"/><w:ind w:left="360" w:hanging="360"/></w:pPr>'
        f'<w:r><w:t xml:space="preserve">• {escape(text)}</w:t></w:r></w:p>'
    )


def build_document_xml() -> str:
    parts: list[str] = []

    parts.append(_w_h1("5. Requirements — RGEE (as implemented in repository)"))
    parts.append(
        _w_p(
            "This specification describes behavior that exists today in the RubricGuidedEssayExam codebase "
            "(FastAPI application in app/main.py, persistence in app/database.py, LLM integration in app/llm_service.py, "
            "prompts in app/prompts.py). Marketing language in README (for example calling exams adaptive) is interpreted here "
            "as: sequential multi-question exams where each new question can depend on a short text summary of prior questions in the same session. "
            "There is no implemented loop that replaces a single question with follow-up prompts until rubric satisfaction."
        )
    )
    parts.append(
        _w_p(
            "Source repository: https://github.com/ALGeek01/RubricGuidedEssayExam — document generated for offline use; verify against latest commit if needed."
        )
    )

    # 5.1
    parts.append(_w_h2("5.1 Introduction"))
    parts.append(_w_h3("5.1.1 Overview"))
    parts.append(
        _w_p(
            "The system is a locally hosted web application. Students start an exam by submitting a student identifier string, "
            "free-text professor domain, education level, mock versus live LLM mode, and a planned question count. "
            "The server creates a session row and the first question row, then redirects the browser to a question page. "
            "Each question includes background text, an essay prompt, and a rubric stored as text (typically a JSON-encoded list). "
            "After each answer, the server either grades and creates the next question, or grades and writes a final grade row. "
            "Results and a professor dashboard read from the same SQLite (or configured SQLAlchemy) database."
        )
    )
    parts.append(_w_h3("5.1.2 Product identity"))
    parts.append(_w_p("FastAPI application title: Modular Oral-Style Exam System; version metadata 0.1.0 (see app/main.py)."))
    parts.append(_w_h3("5.1.3 Team (from README)"))
    parts.append(_w_p("GREEN team contributors are listed in repository README; this document does not assign individual ownership of requirements."))

    # 5.2
    parts.append(_w_h2("5.2 System overview"))
    parts.append(_w_h3("5.2.1 Runtime topology"))
    parts.append(_w_bullet("One Python process runs an ASGI app (Uvicorn per README)."))
    parts.append(_w_bullet("Browser clients use HTML forms and redirects; static files under /static."))
    parts.append(_w_bullet("Optional external dependency: Together.ai HTTPS chat completions API when live mode is used."))
    parts.append(_w_h3("5.2.2 Exam behavior (implemented)"))
    parts.append(_w_bullet("Planned question count is clamped to integers 1 through 20 inclusive on POST /exam/start."))
    parts.append(_w_bullet("Session status values used in logic: in_progress and completed."))
    parts.append(_w_bullet("While in_progress, current_question_index selects which ExamQuestion row is shown."))
    parts.append(
        _w_bullet(
            "For non-final answers: one LLM call returns both grading JSON for the current answer and next_question JSON; "
            "the server persists grading on the current row, inserts the next row, increments current_question_index, redirects to question."
        )
    )
    parts.append(
        _w_bullet(
            "For the final answer: one LLM call returns grading JSON and final_grade JSON; "
            "the server persists grading, inserts FinalGrade, sets session status completed, copies summary JSON onto session, redirects to results."
        )
    )
    parts.append(_w_h3("5.2.3 Context passed to the model"))
    parts.append(
        _w_p(
            "Prior-questions summary for generation and intermediate grading: built from all questions in the session ordered by index; "
            "each line is the first 400 characters of the essay_question text prefixed with a question label (implementation in app/main.py)."
        )
    )
    parts.append(
        _w_p(
            "Final combined grade: receives a text blob of earlier questions including each essay text, student response, and stored grading JSON "
            "for indices strictly before the last question."
        )
    )
    parts.append(_w_h3("5.2.4 Explicit non-features (not in code paths)"))
    parts.append(_w_bullet("No login, sessions cookies, or role-based access control for /professor routes."))
    parts.append(_w_bullet("No file upload for domain material; professor domain is a single form text field."))
    parts.append(_w_bullet("No per-answer character limit enforced in route handlers (only empty student_id is rejected on start)."))
    parts.append(_w_bullet("No autosave of partial essay text beyond normal browser behavior."))
    parts.append(_w_bullet("No timers that auto-submit or lock the exam."))

    # 5.3
    parts.append(_w_h2("5.3 System goals (observable)"))
    parts.append(_w_h3("5.3.1 Functional"))
    parts.append(_w_bullet("FG-A: User can complete a 1-question or N-question exam and reach a results page with per-question rows and optional FinalGrade."))
    parts.append(_w_bullet("FG-B: User can choose mock LLM behavior without any Together API key."))
    parts.append(_w_bullet("FG-C: User can choose live mode only when server has a non-empty TOGETHER_API_KEY (validated on exam start)."))
    parts.append(_w_bullet("FG-D: Professor can open a list of recent sessions and a per-session detail view with parsed rubric and grade JSON."))
    parts.append(_w_h3("5.3.2 Non-functional (as exhibited)"))
    parts.append(_w_bullet("NFG-A: Together failures in live mode raise TogetherApiError; a registered handler renders templates/error_llm.html with an HTTP status carried from the exception (often 503)."))
    parts.append(_w_bullet("NFG-B: Failed first-question generation rolls back the new ExamSession; failed mid-exam answer processing rolls back that transaction."))
    parts.append(_w_bullet("NFG-C: Automated tests use temporary SQLite file and MOCK_LLM=1 via tests/conftest.py before app import."))

    # 5.4
    parts.append(_w_h2("5.4 Functional requirements — routes and validation"))
    parts.append(_w_h3("5.4.1 GET / (home)"))
    parts.append(_w_p("Renders index.html with EDUCATION_LEVELS, default level id, api_key_configured (derived from settings), and default_toggle_mock (true when key missing or settings.mock_llm is true)."))
    parts.append(_w_h3("5.4.2 POST /exam/start"))
    parts.append(_w_bullet("Requires form fields student_id, professor_domain; optional education_level (defaults to college id), llm_mode (default mock), num_questions (default 1)."))
    parts.append(_w_bullet("Returns 400 if student_id is empty after strip, or education_level not in {primary, middle, high_school, college, graduate}, or live mode requested without server API key."))
    parts.append(_w_bullet("live mode is when llm_mode stripped and lowercased is exactly live; all other values select mock behavior for the session."))
    parts.append(_w_bullet("On success: flush session, call generate_question with empty prior summary for index 0, commit session and first ExamQuestion, redirect 303 to /exam/{id}/question."))
    parts.append(_w_h3("5.4.3 GET /exam/{session_id}/question"))
    parts.append(_w_bullet("404 if session missing; 303 redirect to results if status is not in_progress."))
    parts.append(_w_bullet("404 if no ExamQuestion for current_question_index."))
    parts.append(_w_bullet("Rubric display: json.loads when valid JSON list; otherwise show raw rubric string."))
    parts.append(_w_h3("5.4.4 POST /exam/{session_id}/answer"))
    parts.append(_w_bullet("400 if session missing or status not in_progress."))
    parts.append(_w_bullet("404 if current question row missing."))
    parts.append(_w_bullet("answer is stored stripped; seconds_on_question stored as integer only when the form string is all digits, otherwise null."))
    parts.append(_w_h3("5.4.5 GET /exam/{session_id}/results"))
    parts.append(_w_bullet("404 if session missing; otherwise render all questions ordered by index and FinalGrade if present."))
    parts.append(_w_h3("5.4.6 GET /professor"))
    parts.append(_w_p("Lists ExamSession ordered by created_at descending, limit 200."))
    parts.append(_w_h3("5.4.7 GET /professor/exam/{session_id}"))
    parts.append(_w_p("404 if session missing; else detail template with per-question rubric/grade parsing same as dashboard logic."))
    parts.append(_w_h3("5.4.8 OpenAPI"))
    parts.append(_w_p("Standard FastAPI /docs for interactive schema (not a separate written API spec file in repo)."))

    # 5.5
    parts.append(_w_h2("5.5 LLM integration (as implemented)"))
    parts.append(_w_h3("5.5.1 Configuration"))
    parts.append(_w_p("Settings (pydantic-settings, .env): together_api_key, together_model default meta-llama/Llama-3.3-70B-Instruct-Turbo, together_base_url default https://api.together.xyz/v1, mock_llm boolean, database_url default sqlite:///./exam_system.db."))
    parts.append(_w_h3("5.5.2 Live requests"))
    parts.append(_w_p("httpx POST to {base}/chat/completions with Bearer token, temperature 0.4, timeout 120 seconds, max_tokens 4096 for single-output generation, 8192 for combined grade-plus-next or grade-plus-final prompts."))
    parts.append(_w_p("Specific HTTP status handling: 401/403 and 402 produce user-facing TogetherApiError messages; other HTTP errors include response snippet."))
    parts.append(_w_h3("5.5.3 Response parsing"))
    parts.append(_w_p("Model text is stripped of markdown JSON fences when present; json.loads with fallback regex object extraction."))
    parts.append(_w_p("Combined responses must contain keys grading and next_question, or grading and final_grade, or TogetherApiError with 503."))
    parts.append(_w_h3("5.5.4 Mock mode"))
    parts.append(_w_p("Deterministic mock payloads in llm_service: fixed rubric shape, overall_percent 84.0, final total_grade_percent 84.0, with [MOCK] prefixed strings."))
    parts.append(_w_h3("5.5.5 Other functions"))
    parts.append(_w_p("grade_answer and final_grade exist in llm_service for standalone calls; the HTTP exam flow uses only generate_question, grade_and_next_question_combined, and grade_and_final_combined."))

    # 5.6
    parts.append(_w_h2("5.6 Data model"))
    parts.append(_w_h3("5.6.1 ExamSession"))
    parts.append(_w_p("Fields: id PK, student_id indexed string(256), professor_domain text, education_level string(64), use_mock_llm bool, num_questions_planned int, current_question_index int, status string(64), created_at timezone-aware datetime, final_grade_json optional text."))
    parts.append(_w_h3("5.6.2 ExamQuestion"))
    parts.append(_w_p("Fields: id PK, session_id FK cascade delete, question_index int, background_information text, essay_question text, grading_rubric text, domain_notes optional text, student_response optional text, seconds_on_question optional int, graded_state_p_json optional text."))
    parts.append(_w_h3("5.6.3 FinalGrade"))
    parts.append(_w_p("Fields: id PK, session_id FK cascade delete unique, total_grade_percent float, explanation text, summary_json text."))
    parts.append(_w_h3("5.6.4 Schema migration"))
    parts.append(_w_p("init_db creates tables then attempts SQLite ALTER TABLE for education_level and use_mock_llm if missing (ignore duplicate column errors)."))

    # 5.7
    parts.append(_w_h2("5.7 Technical stack (requirements.txt)"))
    parts.append(_w_bullet("fastapi>=0.115, uvicorn[standard]>=0.32, httpx>=0.27, python-dotenv>=1, sqlalchemy>=2, jinja2>=3.1, pydantic>=2, pydantic-settings>=2, python-multipart>=0.0.9, pytest>=8."))
    parts.append(_w_p("CI: .github/workflows/python-tests.yml runs pytest on Python 3.12 for main/master branches and pull requests."))

    # 5.8
    parts.append(_w_h2("5.8 Testing (implemented)"))
    parts.append(_w_p("tests/general/test_api.py: home, static CSS, exam start redirect, invalid education level, single- and two-question flows, completed session redirect, not found, professor dashboard and detail."))
    parts.append(_w_p("tests/general/test_unit.py and tests/security/test_http.py: additional coverage per repository."))
    parts.append(_w_p("pytest.ini configures test discovery; integration marker used in tests."))

    # 5.9
    parts.append(_w_h2("5.9 Documentation delivered with code"))
    parts.append(_w_bullet("README.md: team, features, stack, prerequisites Python 3.11+, run instructions macOS and Windows, default URLs, pytest command."))
    parts.append(_w_bullet(".env.example documents TOGETHER_API_KEY, TOGETHER_MODEL, MOCK_LLM."))

    # 5.10
    parts.append(_w_h2("5.10 Security and privacy (deployment decisions)"))
    parts.append(_w_bullet("Target deployment is a department-managed server, not public internet exposure by default."))
    parts.append(_w_bullet("Access model for professor routes should be enforced by VPN or SSO at the infrastructure layer until in-app auth is added."))
    parts.append(_w_bullet("Student_id remains an opaque string in the app; institutional identity mapping and verification are external responsibilities."))
    parts.append(_w_bullet("API key is server-side only; users (professors/school) manage Together.ai account usage, budgets, and key rotation policies."))

    # 5.11
    parts.append(_w_h2("5.11 Risks and limitations"))
    parts.append(_w_bullet("If VPN/SSO controls are not consistently enforced, professor pages may expose student responses and grades."))
    parts.append(_w_bullet("LLM JSON shape drift can cause 503 errors after Together returns parseable but schema-invalid payloads."))
    parts.append(_w_bullet("SQLite default is unsuitable for high concurrent write load without migration."))
    parts.append(_w_bullet("Trusted-lab operating assumption reduces, but does not eliminate, misuse risk for shared links and copied content."))

    # 5.12
    parts.append(_w_h2("5.12 Constraints"))
    parts.append(_w_bullet("Professor list hard-coded limit 200 sessions."))
    parts.append(_w_bullet("Prior question summary truncates each essay_question to 400 characters."))
    parts.append(_w_bullet("Together client timeout 120 seconds per call."))

    # 5.13
    parts.append(_w_h2("5.13 Governance, policy defaults, and remaining open items"))
    parts.append(_w_h3("5.13.1 Confirmed decisions"))
    parts.append(_w_bullet("Deployment target: department server."))
    parts.append(_w_bullet("Professor access control: VPN only for current deployment policy."))
    parts.append(_w_bullet("Grading authority: LLM output is advisory; instructors retain final authority."))
    parts.append(_w_bullet("Integrity environment: trusted lab usage only for current deployment model."))
    parts.append(_w_bullet("Accessibility scope: no dedicated accessibility requirements section in this revision."))
    parts.append(_w_bullet("License: keep README placeholder text ('add license') for now (TBD)."))
    parts.append(_w_h3("5.13.2 Retention, deletion, and export best-practice defaults"))
    parts.append(_w_bullet("Retention default: keep exam records for one academic term plus one additional term (for grade dispute windows), then archive or purge."))
    parts.append(_w_bullet("Deletion policy: support admin-initiated deletion by session_id and batch deletion by date range; log deletion metadata (who, when, scope)."))
    parts.append(_w_bullet("Export requirement: provide official per-session JSON export including session metadata, all questions, answers, per-question grading payloads, and final grade payload."))
    parts.append(_w_bullet("Recommended export operations: single-session export, date-range export, and checksum field for integrity verification of exported files."))
    parts.append(_w_bullet("Operational review cadence: revisit retention period each term to align with department and registrar policy changes."))
    parts.append(_w_h3("5.13.3 Remaining open items"))
    parts.append(_w_bullet("Expected peak concurrent users on the department server (needed to decide when SQLite should be replaced)."))
    parts.append(_w_bullet("Access control implementation details for VPN provider, onboarding workflow, and incident revocation process."))

    parts.append(_w_h2("5.14 Document control"))
    parts.append(_w_p(f"Generated by docs/generate_rgee_requirements_as_implemented_docx.py as {OUT.name}. Regenerate after code changes."))

    body = "".join(parts)
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<w:body>{body}<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr></w:body>
</w:document>'''


def write_docx(path: Path) -> None:
    doc_xml = build_document_xml()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES_DOCX)
        z.writestr("_rels/.rels", RELS_ROOT)
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/document.xml", doc_xml.encode("utf-8"))
        z.writestr("word/styles.xml", STYLES_XML.encode("utf-8"))


def main() -> None:
    write_docx(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
