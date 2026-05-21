"""
Generate a human-friendly Section 5 requirements document for RGEE.

Run:
  python docs/generate_rgee_requirements_human_readable_docx.py

Writes:
  docs/RGEE_Requirements_As_Implemented_Section5_HumanReadable.docx
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

DOCS = Path(__file__).resolve().parent
OUT = DOCS / "RGEE_Requirements_As_Implemented_Section5_HumanReadable.docx"

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
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="320" w:after="140"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:sz w:val="38"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="220" w:after="100"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:sz w:val="30"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="140" w:after="80"/><w:outlineLvl w:val="2"/></w:pPr><w:rPr><w:b/><w:sz w:val="25"/></w:rPr></w:style>
</w:styles>"""


def _p(text: str) -> str:
    return f'<w:p><w:pPr><w:spacing w:after="95"/></w:pPr><w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'


def _h1(text: str) -> str:
    return f'<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>{escape(text)}</w:t></w:r></w:p>'


def _h2(text: str) -> str:
    return f'<w:p><w:pPr><w:pStyle w:val="Heading2"/></w:pPr><w:r><w:t>{escape(text)}</w:t></w:r></w:p>'


def _h3(text: str) -> str:
    return f'<w:p><w:pPr><w:pStyle w:val="Heading3"/></w:pPr><w:r><w:t>{escape(text)}</w:t></w:r></w:p>'


def _bullet(text: str) -> str:
    return (
        '<w:p><w:pPr><w:spacing w:after="55"/><w:ind w:left="420" w:hanging="320"/></w:pPr>'
        f'<w:r><w:t xml:space="preserve">• {escape(text)}</w:t></w:r></w:p>'
    )


def _divider() -> str:
    return '<w:p><w:pPr><w:spacing w:after="45"/></w:pPr><w:r><w:t>----------------------------------------</w:t></w:r></w:p>'


def build_document_xml() -> str:
    parts: list[str] = []

    parts.append(_h1("5. Requirements — RGEE (Human-Readable Edition)"))
    parts.append(_p("This version keeps the same Section 5 structure, but rewrites requirements in plain language and cleaner layout for easier review."))
    parts.append(_p("Repository source: https://github.com/ALGeek01/RubricGuidedEssayExam"))
    parts.append(_divider())

    parts.append(_h2("5.1 Introduction"))
    parts.append(_h3("5.1.1 What this system does"))
    parts.append(_p("RGEE is a web app for oral-style essay exams. A student starts a session, receives generated questions one at a time, submits answers, and gets per-question grading plus a final result."))
    parts.append(_p("All exam activity is stored in the database so professors can review attempts later."))
    parts.append(_h3("5.1.2 What this document covers"))
    parts.append(_p("Only implemented behavior is described. Future ideas are intentionally excluded unless they already appear in code paths."))
    parts.append(_h3("5.1.3 Product identity"))
    parts.append(_p("FastAPI app title is Modular Oral-Style Exam System, version 0.1.0. Main logic lives in app/main.py, app/llm_service.py, and app/database.py."))

    parts.append(_h2("5.2 System overview"))
    parts.append(_h3("5.2.1 Runtime model"))
    parts.append(_bullet("One FastAPI server handles student flows, professor pages, and static assets."))
    parts.append(_bullet("Together.ai is optional; mock mode works without API keys."))
    parts.append(_h3("5.2.2 Exam flow in plain steps"))
    parts.append(_bullet("Student starts exam with ID, domain prompt, education level, mode, and number of questions (1 to 20)."))
    parts.append(_bullet("Server creates session and first question, then redirects student to the question page."))
    parts.append(_bullet("Each answer is saved; system either creates next question or finalizes exam."))
    parts.append(_bullet("Results page shows all question records and final grade when available."))
    parts.append(_h3("5.2.3 Context passed to the model"))
    parts.append(_bullet("Intermediate generation uses a prior-question summary built from existing session questions, truncating each essay question to 400 characters."))
    parts.append(_bullet("Final grading receives a text blob of all earlier questions with essay text, student response, and stored grading JSON."))
    parts.append(_h3("5.2.4 Explicit non-features"))
    parts.append(_bullet("No built-in user login or role model in application routes."))
    parts.append(_bullet("No file upload for domain material; professor domain is plain form text."))
    parts.append(_bullet("No timer enforcement that auto-submits answers."))

    parts.append(_h2("5.3 Requirements summary"))
    parts.append(_h3("5.3.1 Core functional requirements"))
    parts.append(_bullet("Student can complete full exam and reach results page."))
    parts.append(_bullet("Professor can view recent sessions and per-session details."))
    parts.append(_bullet("Live mode requires a server-side Together API key; otherwise request is rejected."))
    parts.append(_bullet("Mock mode always works for local testing and CI."))
    parts.append(_h3("5.3.2 Non-functional requirements currently enforced"))
    parts.append(_bullet("Invalid input produces explicit HTTP errors (400 or 404)."))
    parts.append(_bullet("Live API errors return a readable HTML error page."))
    parts.append(_bullet("Database writes are rolled back when LLM calls fail mid-flow."))
    parts.append(_h3("5.3.3 Performance and scale notes"))
    parts.append(_bullet("Live LLM requests use a 120-second timeout in httpx."))
    parts.append(_bullet("Default storage is SQLite, which is fine for class-scale use but limited under heavy concurrent writes."))

    parts.append(_h2("5.4 Route requirements"))
    parts.append(_h3("5.4.1 Home page (GET /)"))
    parts.append(_p("Shows available education levels, default level, and whether mock mode should be selected by default."))
    parts.append(_h3("5.4.2 Start exam (POST /exam/start)"))
    parts.append(_bullet("Rejects empty student ID."))
    parts.append(_bullet("Rejects invalid education level IDs."))
    parts.append(_bullet("Rejects live mode if TOGETHER_API_KEY is missing."))
    parts.append(_bullet("On success: creates session and first question, then redirects to /exam/{id}/question."))
    parts.append(_h3("5.4.3 Question page (GET /exam/{session_id}/question)"))
    parts.append(_bullet("404 when session or question does not exist."))
    parts.append(_bullet("Redirects completed sessions directly to results."))
    parts.append(_h3("5.4.4 Submit answer (POST /exam/{session_id}/answer)"))
    parts.append(_bullet("Stores stripped answer text and optional numeric seconds_on_question."))
    parts.append(_bullet("Intermediate question: one combined call grades current answer and generates next question."))
    parts.append(_bullet("Final question: one combined call grades current answer and returns final grade payload."))
    parts.append(_h3("5.4.5 Results and professor pages"))
    parts.append(_bullet("GET /exam/{session_id}/results shows ordered question records and optional final grade row."))
    parts.append(_bullet("GET /professor lists latest 200 sessions."))
    parts.append(_bullet("GET /professor/exam/{session_id} shows full question-by-question detail."))
    parts.append(_h3("5.4.6 API docs"))
    parts.append(_bullet("FastAPI auto-docs are available at /docs."))

    parts.append(_h2("5.5 LLM integration requirements"))
    parts.append(_h3("5.5.1 Configuration"))
    parts.append(_bullet("Settings include TOGETHER_API_KEY, TOGETHER_MODEL, TOGETHER_BASE_URL, MOCK_LLM, and DATABASE_URL through pydantic-settings."))
    parts.append(_bullet("Default model is meta-llama/Llama-3.3-70B-Instruct-Turbo and default base URL is https://api.together.xyz/v1."))
    parts.append(_h3("5.5.2 Live requests"))
    parts.append(_bullet("Live requests use Together chat completions with 120-second timeout."))
    parts.append(_bullet("Temperature is 0.4; max_tokens is 4096 for simple calls and 8192 for combined calls."))
    parts.append(_bullet("HTTP 401/403/402 are transformed into user-facing TogetherApiError messages."))
    parts.append(_h3("5.5.3 Parsing and validation"))
    parts.append(_bullet("Combined responses must include expected keys (grading + next_question or grading + final_grade)."))
    parts.append(_bullet("JSON parsing strips markdown fences and uses fallback extraction when needed."))
    parts.append(_h3("5.5.4 Mock mode"))
    parts.append(_bullet("Mock mode returns stable fake data to keep tests deterministic."))

    parts.append(_h2("5.6 Data model requirements"))
    parts.append(_h3("5.6.1 ExamSession"))
    parts.append(_bullet("ExamSession stores user/session metadata and status."))
    parts.append(_h3("5.6.2 ExamQuestion"))
    parts.append(_bullet("ExamQuestion stores prompt content, response, timing, and per-question grading JSON."))
    parts.append(_h3("5.6.3 FinalGrade"))
    parts.append(_bullet("FinalGrade stores final percentage, explanation, and raw summary JSON."))
    parts.append(_h3("5.6.4 Migration behavior"))
    parts.append(_bullet("Startup migration adds missing columns in SQLite when required."))

    parts.append(_h2("5.7 Security, policy, and operations"))
    parts.append(_h3("5.7.1 Deployment and access policy"))
    parts.append(_bullet("Deployment target: department-managed server."))
    parts.append(_bullet("Professor access: VPN only (current policy)."))
    parts.append(_bullet("Grade output is advisory; instructors keep final authority."))
    parts.append(_bullet("Trusted-lab environment is assumed."))
    parts.append(_h3("5.7.2 Retention and export defaults"))
    parts.append(_bullet("Retention baseline: one academic term plus one additional term."))
    parts.append(_bullet("Deletion support should include by-session and by-date-range operations with audit logging."))
    parts.append(_bullet("Official export is required in JSON, including session metadata, questions, answers, and grading payloads."))

    parts.append(_h2("5.8 Known limitations"))
    parts.append(_bullet("No built-in authentication for professor routes in the app itself."))
    parts.append(_bullet("No file upload pipeline for professor domain material."))
    parts.append(_bullet("SQLite may need replacement for higher concurrency usage."))

    parts.append(_h2("5.9 Testing and CI"))
    parts.append(_bullet("Test suite uses pytest with FastAPI TestClient and a temporary SQLite database in tests/conftest.py."))
    parts.append(_bullet("CI workflow runs pytest on Python 3.12 for pushes and pull requests to main/master."))

    parts.append(_h2("5.10 Documentation delivered with code"))
    parts.append(_bullet("README documents setup, run commands for Windows/macOS, and app URLs."))
    parts.append(_bullet(".env.example documents required environment variables."))

    parts.append(_h2("5.11 Risks and caveats"))
    parts.append(_bullet("If VPN controls are bypassed or misconfigured, professor pages may expose student responses and grades."))
    parts.append(_bullet("Unexpected model output shape can still cause request failures, even with parsing safeguards."))

    parts.append(_h2("5.12 Constraints"))
    parts.append(_bullet("Professor dashboard currently limits display to 200 sessions."))
    parts.append(_bullet("Prior-question summary truncation is fixed at 400 characters per question text."))

    parts.append(_h2("5.13 Governance details"))
    parts.append(_h3("5.13.1 Confirmed decisions"))
    parts.append(_bullet("Department server deployment, VPN-only professor access, advisory grading, and trusted-lab use are current policy decisions."))
    parts.append(_h3("5.13.2 Remaining technical planning items"))
    parts.append(_bullet("Define expected peak concurrent users to decide when database migration from SQLite is necessary."))
    parts.append(_bullet("Define VPN onboarding and deprovisioning workflow for professors and support staff."))

    parts.append(_h2("5.14 Document notes"))
    parts.append(_p("License status remains TBD (README still says add license)."))
    parts.append(_p(f"Generated by docs/generate_rgee_requirements_human_readable_docx.py as {OUT.name}."))

    body = "".join(parts)
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><w:body>{body}<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr></w:body></w:document>'''


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
