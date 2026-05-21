"""
Generate RGEE detailed requirements (Section 5 style) as a .docx.
Uses only the Python standard library (OOXML). Run:

  python docs/generate_rgee_requirements_section5_docx.py

Writes docs/RGEE_Detailed_Requirements_Section5.docx
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

DOCS = Path(__file__).resolve().parent
OUT = DOCS / "RGEE_Detailed_Requirements_Section5.docx"

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

    parts.append(_w_h1("5. Requirements — RubricGuidedEssayExam (RGEE)"))
    parts.append(
        _w_p(
            "Document type: software requirements specification (Section 5 style). "
            "Source: ALGeek01/RubricGuidedEssayExam repository and implemented codebase (FastAPI, SQLite, optional Together AI). "
            "Methodology alignment: structured requirements, acceptance tests, and stakeholder sections as in typical CSC394-style requirements engineering coursework."
        )
    )

    # --- 5.1 ---
    parts.append(_w_h2("5.1 Introduction"))
    parts.append(_w_h3("5.1.1 Overview"))
    parts.append(
        _w_p(
            "RGEE is a web application that delivers multi-question, essay-style exams grounded in a professor-supplied domain text. "
            "For each question it stores background context, the essay prompt, a structured rubric, the student answer, optional time-on-question, "
            "and LLM-assisted per-question grades with explanations. When the planned number of questions is finished, the system computes "
            "a final aggregate grade with explanation. Instructors can list and inspect completed and in-progress sessions via HTML pages backed by the same database."
        )
    )
    parts.append(_w_h3("5.1.2 Educational problem statement"))
    parts.append(
        _w_p(
            "Written take-home work is vulnerable to generative AI misuse; synchronized high-stakes exams are difficult for asynchronous programs. "
            "The system targets individualized prompts per session and rubric-linked grading to approximate oral-exam depth without requiring a human examiner at attempt time."
        )
    )
    parts.append(_w_h3("5.1.3 Business / academic objective"))
    parts.append(
        _w_p(
            "Support asynchronous delivery, transparent rubric-based scoring, lower marginal grading load for instructors through machine assistance, "
            "and repeatable local deployment for demos and coursework."
        )
    )
    parts.append(_w_h3("5.1.4 Project motivation and context"))
    parts.append(
        _w_p(
            "The stack is deliberately small (Python, FastAPI, SQLite, optional Together): suitable for a course team to extend and to run in mock mode without paid API usage."
        )
    )
    parts.append(_w_h3("5.1.5 Benefits of the proposed system"))
    parts.append(_w_bullet("Individualized question text per session and per index, with prior-question context passed into generation and grading prompts."))
    parts.append(_w_bullet("Explainable per-question JSON grading payloads and a stored final grade row."))
    parts.append(_w_bullet("Mock LLM path for continuous integration and local development."))

    # --- 5.2 ---
    parts.append(_w_h2("5.2 System overview"))
    parts.append(_w_h3("5.2.1 System purpose"))
    parts.append(
        _w_p(
            "Provide a browser-based exam flow and a read-only instructor review surface over persisted attempts, defaulting to http://127.0.0.1:8000 in development."
        )
    )
    parts.append(_w_h3("5.2.2 Assessment model overview"))
    parts.append(
        _w_p(
            "Fixed plan: num_questions_planned is an integer from 1 through 20 chosen at session start. Questions are sequential. "
            "After each answer except the last, the backend performs a combined operation: grade the current answer and generate the next question (one LLM round-trip in live mode). "
            "After the last answer: grade that answer and compute the session final grade (one combined call). "
            "This is not an iterative follow-up-on-the-same-question loop; scope is N distinct main questions with session-level adaptation via prior-question summaries."
        )
    )
    parts.append(_w_h3("5.2.3 Oral examination as the reference standard"))
    parts.append(
        _w_p(
            "Conceptually modeled on oral exams (probing, individualized prompts); the implementation approximates that via LLM-generated prompts and rubric-scored written responses."
        )
    )
    parts.append(_w_h3("5.2.4 High-level system operation"))
    parts.append(_w_bullet("Student submits student ID, professor domain, education level, LLM mode (mock vs live), and question count."))
    parts.append(_w_bullet("Server creates ExamSession and the first ExamQuestion."))
    parts.append(_w_bullet("Student answers; server updates the question row, then either advances to the next question or completes the session and writes FinalGrade."))
    parts.append(_w_bullet("Student views results; professor views dashboard and session detail."))
    parts.append(_w_h3("5.2.5 System boundaries"))
    parts.append(_w_p("In scope (as implemented):"))
    parts.append(_w_bullet("HTML UI with form posts; SQLite persistence and SQLAlchemy models."))
    parts.append(_w_bullet("Together chat-completions integration with mock alternative."))
    parts.append(_w_bullet("OpenAPI documentation at /docs."))
    parts.append(_w_bullet("Optional seconds_on_question capture per answer."))
    parts.append(_w_p("Out of scope (not in current codebase):"))
    parts.append(_w_bullet("Full learning management system integration (Canvas, Blackboard, etc.)."))
    parts.append(_w_bullet("Multi-tenant authentication or SSO for students and professors."))
    parts.append(_w_bullet("Human proctoring or lockdown browser enforcement."))
    parts.append(_w_bullet("Video or audio oral exam capture."))
    parts.append(_w_bullet("Institutional grade-policy engine beyond stored percentages and explanations."))
    parts.append(_w_h3("5.2.6 In-scope features"))
    parts.append(_w_bullet("Start exam with validation: non-empty student ID; education level from allowed set; live mode requires server-side API key."))
    parts.append(_w_bullet("Display rubric (JSON list rendered for students where applicable)."))
    parts.append(_w_bullet("Store and display mock vs production mode per session."))
    parts.append(_w_bullet("Professor dashboard listing recent sessions (up to 200) and per-session audit including rubric and grade JSON."))
    parts.append(_w_h3("5.2.7 Intended use cases"))
    parts.append(_w_bullet("Course demonstrations and software engineering capstone projects."))
    parts.append(_w_bullet("Local oral-style practice exams with instructor review of stored artifacts."))
    parts.append(_w_h3("5.2.8 External systems and dependencies"))
    parts.append(_w_bullet("Together.ai HTTP API when live mode is selected and TOGETHER_API_KEY is configured; together_model and together_base_url are configurable."))
    parts.append(_w_bullet("Modern web browser for students and instructors."))
    parts.append(_w_bullet("Python 3.11 or newer runtime and Uvicorn (or equivalent ASGI server)."))
    parts.append(_w_h3("5.2.9 Out-of-scope features"))
    parts.append(
        _w_p(
            "Per-question adaptive follow-up rounds until satisfaction; student password accounts; encrypted-at-rest guarantees; production security hardening checklist, unless explicitly added in a future revision."
        )
    )

    # --- 5.3 ---
    parts.append(_w_h2("5.3 System goals and requirements"))
    parts.append(_w_h3("5.3.1 Functional goals"))
    parts.append(_w_bullet("FG-1: Students complete a full exam from start through final results using session id in URLs."))
    parts.append(_w_bullet("FG-2: System produces question packages: background, essay question, rubric, optional domain notes."))
    parts.append(_w_bullet("FG-3: System grades answers with structured JSON aligned to prompts and persists grading payloads."))
    parts.append(_w_bullet("FG-4: Professors audit prompts, rubrics, responses, per-question grades, and final grade."))
    parts.append(_w_h3("5.3.2 Non-functional goals"))
    parts.append(_w_bullet("NFG-1: Deterministic validation and HTTP status codes: 400 for invalid input, 404 for missing session or question."))
    parts.append(_w_bullet("NFG-2: Automated tests run with isolated SQLite and mock LLM configuration."))
    parts.append(_w_bullet("NFG-3: Together API failures surface as user-facing HTML error responses with appropriate status, not opaque 500 errors where handled."))
    parts.append(_w_h3("5.3.3 Performance requirements"))
    parts.append(
        _w_p(
            "Interactive latency in live mode is dominated by the LLM provider; the system shall not impose a hard maximum response time in code beyond provider and HTTP client behavior. "
            "Document as best-effort interactive web application."
        )
    )
    parts.append(_w_h3("5.3.4 Scalability requirements"))
    parts.append(
        _w_p(
            "Default SQLite file database suits class-scale demos and moderate concurrency; large concurrent write loads are not a stated design target without migration to another database backend."
        )
    )
    parts.append(_w_h3("5.3.5 Reliability and availability"))
    parts.append(
        _w_p(
            "On LLM failure during session start, the system rolls back the incomplete session creation. On failure during answer processing, the system rolls back the transaction for that submission."
        )
    )
    parts.append(_w_h3("5.3.6 Security, privacy, and compliance"))
    parts.append(_w_bullet("Student identifiers are stored as plain text fields; PII and FERPA handling are institutional responsibilities when deployed beyond local trust boundaries."))
    parts.append(_w_bullet("Professor HTML routes are not authenticated in the reference implementation; this is a known limitation for any public deployment."))
    parts.append(_w_bullet("API keys reside in server environment (.env), not in client-side secrets."))

    # --- 5.4 ---
    parts.append(_w_h2("5.4 Detailed functional requirements"))
    parts.append(_w_h3("5.4.1 Exam lifecycle management"))
    parts.append(_w_p("5.4.1.1 Exam creation: POST /exam/start creates a session with status in_progress, current_question_index 0, and clamps num_questions to the inclusive range 1 through 20."))
    parts.append(_w_p("5.4.1.2 Exam configuration: Persist education_level from the configured allow-list; persist use_mock_llm from the submitted llm_mode; persist professor_domain and student_id."))
    parts.append(_w_p("5.4.1.3 Exam completion: On the last answered question, set status to completed, create FinalGrade, and store summary JSON on the session as implemented."))
    parts.append(_w_h3("5.4.1.4 Acceptance tests (traceable)"))
    parts.append(_w_bullet("AT-1: Empty student_id on start returns HTTP 400."))
    parts.append(_w_bullet("AT-2: Invalid education_level returns HTTP 400."))
    parts.append(_w_bullet("AT-3: Live mode without server API key returns HTTP 400."))
    parts.append(_w_bullet("AT-4: Single-question flow redirects to results after answer; two-question flow returns to question after first answer."))
    parts.append(_w_bullet("AT-5: GET question URL after completion redirects to results."))
    parts.append(_w_h3("5.4.2 Question generation system"))
    parts.append(_w_p("5.4.2.1 Domain-constrained generation: pass professor_domain and, for question index greater than zero, a prior-questions text summary into the LLM generation path."))
    parts.append(_w_p("5.4.2.2 Background information: store background_information on each ExamQuestion."))
    parts.append(_w_p("5.4.2.3 Rubric generation: store grading_rubric as JSON text representing a list of criteria, with display fallback for non-JSON text."))
    parts.append(_w_h3("5.4.3 Grading and final synthesis"))
    parts.append(_w_p("5.4.3.1 Per-question grading: after each submitted answer, store graded_state_p_json with rubric-aligned scores and narrative explanation per prompt contract."))
    parts.append(_w_p("5.4.3.2 Final grade: FinalGrade holds total_grade_percent, explanation, and summary_json from the combined final grading call after the last question."))
    parts.append(_w_h3("5.4.4 Student interface"))
    parts.append(_w_p("Home page exposes education levels and default selection; exam start form supports mock vs live when server key policy allows."))
    parts.append(_w_p("Question page shows question number, total planned questions, rubric, LLM mode label, and human-readable education level label."))
    parts.append(_w_p("Results page lists all questions and final grade when the session is completed."))
    parts.append(_w_h3("5.4.5 Professor interface"))
    parts.append(_w_p("Dashboard lists sessions in reverse chronological order, limited to 200 rows."))
    parts.append(_w_p("Session detail shows each question with rubric and parsed per-question grade JSON plus final grade information."))

    # --- 5.5 ---
    parts.append(_w_h2("5.5 Orchestration and assessment flow"))
    parts.append(_w_h3("5.5.1 Purpose and responsibilities"))
    parts.append(
        _w_p(
            "Orchestration is implemented in the FastAPI application module and llm_service: session state is the ExamSession row plus ordered ExamQuestion rows; no separate orchestration microservice."
        )
    )
    parts.append(_w_h3("5.5.2 Session state"))
    parts.append(
        _w_p(
            "While current_question_index is less than num_questions_planned and status is in_progress, the student may submit an answer for the current index. "
            "After successful processing of the final question, status becomes completed and further answers are rejected with HTTP 400."
        )
    )
    parts.append(_w_h3("5.5.3 Combined LLM operations"))
    parts.append(
        _w_p(
            "The system shall use combined LLM calls where implemented: grade current answer and generate next question in one request for intermediate questions; "
            "grade last answer and compute final session grade in one request for the terminal question."
        )
    )
    parts.append(_w_h3("5.5.4 Termination conditions"))
    parts.append(_w_p("The exam ends after the last planned question is answered and graded; results and professor views read persisted rows only."))

    # --- 5.6 ---
    parts.append(_w_h2("5.6 Technical requirements"))
    parts.append(_w_h3("5.6.1 Programming language and runtime"))
    parts.append(_w_p("Python 3.11 or newer; FastAPI application with declared version metadata as in the codebase."))
    parts.append(_w_h3("5.6.2 Client-server architecture"))
    parts.append(_w_p("Server-rendered HTML via Jinja2 templates; static assets served under /static."))
    parts.append(_w_h3("5.6.3 LLM integration requirements"))
    parts.append(_w_p("Together-compatible chat completions over HTTPS; JSON response parsing tolerant of markdown code fences; explicit error type for provider failures."))
    parts.append(_w_h3("5.6.4 Prompt template system"))
    parts.append(_w_p("Prompts are centralized in the prompts module; changes to output schema require coordinated updates to prompts, parsing, persistence, and any UI that renders grades."))
    parts.append(_w_h3("5.6.5 Execution safety"))
    parts.append(_w_p("LLM output is parsed as JSON only; no execution of arbitrary code returned by the model in the grading or question paths."))
    parts.append(_w_h3("5.6.6 Data storage and persistence"))
    parts.append(
        _w_p(
            "Default database URL is SQLite file exam_system.db; SQLAlchemy engine uses SQLite thread configuration as implemented; optional non-SQLite URLs follow standard SQLAlchemy connection rules."
        )
    )
    parts.append(_w_p("Startup runs schema creation and lightweight SQLite ALTER migrations for backward-compatible columns."))

    # --- 5.7 ---
    parts.append(_w_h2("5.7 Data schema and object model requirements"))
    parts.append(_w_p("Core entities: ExamSession, ExamQuestion, FinalGrade with foreign keys and cascade delete as defined in the database module."))
    parts.append(_w_p("ExamSession shall record student_id, professor_domain, education_level, use_mock_llm, num_questions_planned, current_question_index, status, created_at, and optional final_grade_json."))
    parts.append(
        _w_p(
            "ExamQuestion shall record session_id, question_index, background_information, essay_question, grading_rubric, optional domain_notes, optional student_response, optional seconds_on_question, optional graded_state_p_json."
        )
    )
    parts.append(_w_p("FinalGrade shall record session_id uniquely, total_grade_percent, explanation, and summary_json."))

    # --- 5.8 ---
    parts.append(_w_h2("5.8 API and integration requirements"))
    parts.append(_w_h3("5.8.1 Surface summary"))
    parts.append(_w_bullet("GET / — student landing."))
    parts.append(_w_bullet("POST /exam/start — create session and first question; redirect 303 to question URL."))
    parts.append(_w_bullet("GET /exam/{session_id}/question — current question or redirect if completed."))
    parts.append(_w_bullet("POST /exam/{session_id}/answer — submit answer; chain or finalize."))
    parts.append(_w_bullet("GET /exam/{session_id}/results — results view."))
    parts.append(_w_bullet("GET /professor — instructor session list."))
    parts.append(_w_bullet("GET /professor/exam/{session_id} — instructor session detail."))
    parts.append(_w_bullet("GET /docs — OpenAPI documentation."))
    parts.append(_w_h3("5.8.2 Authentication and security"))
    parts.append(_w_p("No authentication on professor routes in the reference application; deployments requiring privacy shall add access controls outside or inside this specification's future revisions."))
    parts.append(_w_h3("5.8.3 Error handling and validation"))
    parts.append(_w_p("Validation and HTTP semantics shall match the acceptance tests in section 5.4.1.4 and automated tests in the tests package."))

    # --- 5.9 ---
    parts.append(_w_h2("5.9 Testing requirements"))
    parts.append(_w_p("Automated tests use pytest; HTTP integration tests exercise primary routes under mock LLM and isolated SQLite."))
    parts.append(_w_p("Security-focused HTTP tests exist under tests/security as provided in the repository."))
    parts.append(_w_p("Each acceptance test identifier in 5.4.1.4 shall map to an automated test or an explicit manual test record for course deliverables."))

    # --- 5.10 ---
    parts.append(_w_h2("5.10 Documentation requirements"))
    parts.append(_w_bullet("README shall document prerequisites, virtual environment setup, Windows and Unix run commands, mock vs live configuration, and default URLs."))
    parts.append(_w_bullet("Course submissions may add a Bad Developer and Bad Client review matrix keyed to requirement identifiers."))

    # --- 5.11 ---
    parts.append(_w_h2("5.11 Risk management"))
    parts.append(_w_p("Specific risk: Together API outage or quota exhaustion. Impact: students cannot start or continue live exams. Mitigation: mock mode for development; operator communication; retries only as already coded in client layer if any."))
    parts.append(_w_p("Specific risk: model output JSON shape drift. Impact: parsing failures or incomplete grades. Mitigation: prompt versioning, tests with mock payloads, monitoring logs in deployment."))
    parts.append(_w_p("Specific risk: unauthenticated professor dashboard exposed on a network. Impact: unauthorized viewing of student work. Mitigation: network isolation, reverse proxy auth, or future in-app authentication."))

    # --- 5.12 ---
    parts.append(_w_h2("5.12 Stakeholders"))
    parts.append(_w_bullet("Students: take exams and view own results."))
    parts.append(_w_bullet("Instructors: review stored sessions and grades."))
    parts.append(_w_bullet("Development team: maintain prompts, code, and tests."))
    parts.append(_w_bullet("Institution: policies for PII, retention, and deployment when used beyond local demos."))

    # --- 5.13 ---
    parts.append(_w_h2("5.13 Assumptions"))
    parts.append(_w_bullet("Operators trust the network path for localhost or controlled server environments during development."))
    parts.append(_w_bullet("Professor domain text is supplied in good faith; prompt injection defenses follow normal LLM application hygiene."))
    parts.append(_w_bullet("Education level identifiers match the application's configured allow-list."))

    # --- 5.14 ---
    parts.append(_w_h2("5.14 Constraints"))
    parts.append(_w_bullet("SQLite file locking and single-writer characteristics limit heavy concurrent write scenarios."))
    parts.append(_w_bullet("Professor dashboard caps displayed sessions at 200 by product choice; underlying data may still exist beyond the cap."))
    parts.append(_w_bullet("Course schedule and API budget constrain optional live-model testing frequency."))

    # --- 5.15 ---
    parts.append(_w_h2("5.15 Software and tools"))
    parts.append(_w_bullet("Languages: Python."))
    parts.append(_w_bullet("Frameworks: FastAPI, Starlette, Uvicorn, SQLAlchemy 2, Jinja2, Pydantic settings, httpx, python-multipart."))
    parts.append(_w_bullet("Quality: pytest as declared in project requirements."))

    # --- 5.16 ---
    parts.append(_w_h2("5.16 Hosting, deployment, and operations"))
    parts.append(_w_p("Default development hosting binds to 127.0.0.1 port 8000 as documented in README; production deployment, TLS termination, process management, and backups are operator responsibilities unless extended by a future release."))

    # --- Bad dev / bad client sample ---
    parts.append(_w_h2("5.17 Sample Bad Developer / Bad Client matrix (course practice)"))
    parts.append(_w_p("FG-2: Bad Dev delivers static lorem ipsum unrelated to domain. Bad Client insists uploaded PDF corpora are mandatory for every exam."))
    parts.append(_w_p("5.3.6: Bad Dev hides professor pages behind obscure URLs only. Bad Client demands FERPA-certified hosting without supplying infrastructure requirements."))

    parts.append(_w_h2("Document control"))
    parts.append(
        _w_p(
            f"Generated file path: {OUT.name}. Generator: docs/generate_rgee_requirements_section5_docx.py. "
            "Repository: https://github.com/ALGeek01/RubricGuidedEssayExam"
        )
    )

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
