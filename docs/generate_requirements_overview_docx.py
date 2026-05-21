"""
Build an easy-to-read Word overview of functional vs non-functional requirements.
Uses only the Python standard library (OOXML). Run:

  python docs/generate_requirements_overview_docx.py

Writes:
  - docs/capstone-requirements-overview.docx (in this repo)
  - %USERPROFILE%\\capstone-requirements-overview.docx (if writable)
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

DOCS = Path(__file__).resolve().parent

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

    parts.append(_w_h1("Capstone requirements overview"))
    parts.append(
        _w_p(
            "CSC394 / IS376 — AI-assisted oral-style exam system. "
            "This document summarizes functional requirements (what the system does), "
            "non-functional requirements (how well it must perform), and technical constraints. "
            "Full detail and acceptance criteria: requirements-specification-csc394-capstone.md (v1.1)."
        )
    )

    parts.append(_w_h2("Quick guide: functional vs non-functional"))
    parts.append(
        _w_p(
            "Functional requirements describe behavior and features — for example, saving an exam configuration, "
            "submitting an answer, or returning a structured grade."
        )
    )
    parts.append(
        _w_p(
            "Non-functional requirements describe qualities and constraints — for example, page load time, "
            "uptime targets, accessibility, logging policy, and operator documentation."
        )
    )

    parts.append(_w_h2("Technical constraints"))
    parts.append(_w_bullet("Implementation stack: Python backend, web UI, HTTP API, database (e.g. SQLite or Postgres)."))
    parts.append(_w_bullet("LLM: primary provider Together (or equivalent); subject to network, quotas, latency, and cost."))
    parts.append(
        _w_bullet(
            "Architecture: English prompt templates in code → filled at runtime → model may return Python source → "
            "execute only in a sandbox or heavily restricted environment → validate against versioned schemas before use."
        )
    )
    parts.append(_w_bullet("Security: model output is untrusted; no full-privilege exec on the host; limits on CPU, memory, and time."))
    parts.append(_w_bullet("LLM calls are stateless: each request must include the context the model needs (question, rubric, follow-up history, etc.)."))
    parts.append(_w_bullet("Testing: automated tests often use a mock LLM; live integration tests need keys and tolerate provider variability (retries, p95)."))
    parts.append(_w_bullet("Compliance: FERPA/PII handling, retention, and export may be constrained by institutional policy (see SRS open items)."))

    parts.append(_w_h2("Functional requirements"))

    parts.append(_w_h3("Product goal"))
    parts.append(
        _w_p(
            "G-1 — Question variation: with vary_questions enabled, the system targets diverse questions "
            "(e.g. not byte-identical to another student’s in the same configuration within seven days; acceptance is partly stochastic)."
        )
    )

    parts.append(_w_h3("Professor configuration"))
    parts.append(_w_p("FR-PROF-1 — Create and save exam configuration: title, N questions (1–20), optional time limits, domain briefing, optional reference files, rubric style, weights summing to 1."))
    parts.append(_w_p("FR-PROF-2 — At least three independent constraint fields per question slot, passed into generation and audit-logged."))
    parts.append(_w_p("FR-PROF-3 — Per-student time multipliers (1.0×–3.0×) for question and whole-exam limits."))
    parts.append(_w_p("FR-PROF-4 — vary_questions flag; prompts discourage repeating recent instances for the same config."))

    parts.append(_w_h3("LLM — question generation"))
    parts.append(_w_p("FR-GEN-1 — Model returns Python assigning a named result; execute under security rules; validate to exam_gen_v1; invalid responses trigger retries."))
    parts.append(_w_p("FR-GEN-2 — Generated content includes background, essay question, rubric (≥3 criteria with points), expected concepts, metadata."))
    parts.append(_w_p("FR-GEN-3 — Retries with exponential backoff (up to three) on failure."))
    parts.append(_w_p("FR-GEN-4 — Generation latency budget (p95 ≤ 45 s under nominal staging conditions)."))

    parts.append(_w_h3("Student examination"))
    parts.append(_w_p("FR-STU-1 — Session bound to one student and one exam config; no answers after session is closed, expired, or finally submitted."))
    parts.append(_w_p("FR-STU-2 — Question order is fixed or random, chosen at session start and stable across refresh."))
    parts.append(_w_p("FR-STU-3 — Essay answers up to 20,000 UTF-8 characters; enforce on client and server."))
    parts.append(_w_p("FR-STU-4 — Autosave drafts on a defined schedule."))
    parts.append(_w_p("FR-STU-5 — Optional per-question and whole-exam timers; server-authoritative expiry (±5 s)."))

    parts.append(_w_h3("Grading"))
    parts.append(_w_p("FR-GRADE-1 — Grading prompt includes question, rubric, background, answer, optional timing, weighting; auditable."))
    parts.append(_w_p("FR-GRADE-2 — Grading uses same Python-exec pattern; validate exam_grade_v1 (scores, total 0–100, satisfactory vs threshold, explanation, confidence)."))
    parts.append(_w_p("FR-GRADE-3 — After failures, mark needs_human_review; no numeric final until professor resolves."))

    parts.append(_w_h3("Follow-up rounds (optional path)"))
    parts.append(_w_p("FR-FU-1 — If not satisfactory and follow-ups enabled, request follow-up question and rubric within limits."))
    parts.append(_w_p("FR-FU-2 — Final grade considers all student turns; one terminal exam_grade_v1."))
    parts.append(_w_p("FR-FU-3 — Persist State P: grades, rubrics, backgrounds, prompt metadata, student text, timestamps."))

    parts.append(_w_h3("Persistence"))
    parts.append(_w_p("FR-DB-1 — Store finalized questions under (student_id, exam_session_id, question_index); index by session."))
    parts.append(_w_p("FR-DB-2 — Configurable retention and purge of old records."))

    parts.append(_w_h3("Final exam grade"))
    parts.append(_w_p("FR-FINAL-1 — When all questions resolved, build summaries for final grade computation."))
    parts.append(_w_p("FR-FINAL-2 — LLM returns Python → exam_final_v1 (final percentage, optional letter grade, explanation)."))
    parts.append(_w_p("FR-FINAL-3 — At least two professor-selectable grading schemes (e.g. pure weighted average vs LLM-adjusted composite)."))

    parts.append(_w_h3("Results and disputes"))
    parts.append(_w_p("FR-DISP-1 — After finalization, show student final percentage, per-question scores, truncated explanations."))
    parts.append(_w_p("FR-DISP-2 — Disputes only after a configurable delay; caps on length and count per question."))
    parts.append(_w_p("FR-DISP-3 — LLM dispute triage schema; no automatic grade change unless professor enables it."))

    parts.append(_w_h3("Professor review"))
    parts.append(_w_p("FR-REVIEW-1 — Browse/filter sessions with stated performance targets on reference data."))
    parts.append(_w_p("FR-REVIEW-2 — One consolidated view of prompts (secrets redacted), rubrics, backgrounds, answers, model output, timings, aggregates."))
    parts.append(_w_p("FR-REVIEW-3 — Export session (JSON required in v1; PDF optional); JSON matches exam_export_v1."))

    parts.append(_w_h3("Security (behavioral)"))
    parts.append(_w_p("FR-SEC-1 — Never run LLM-generated Python with full host privileges; subprocess sandbox or restricted exec with documented limits."))
    parts.append(_w_p("FR-SEC-2 — Authenticate professor routes; student routes use session tokens bound to student and config with bounded lifetime."))

    parts.append(_w_h3("Optional / advanced (if implemented)"))
    parts.append(_w_p("ADV-CURVE-1 — Cohort curve with minimum sample size and clear fallback when too few responses."))
    parts.append(_w_p("ADV-DISC-1 — Discussion-based testing with transcript limits and token budget per grading call."))

    parts.append(_w_h2("Non-functional requirements"))
    parts.append(_w_p("NFR-PERF-1 — Student UI: Largest Contentful Paint ≤ 2.5 s under a defined throttled network profile (median of measured runs)."))
    parts.append(_w_p("NFR-REL-1 — Core API availability ≥ 99.5% over a two-week pilot (synthetic checks), excluding provider outages per policy."))
    parts.append(_w_p("NFR-AUDIT-1 — Immutable audit events for key actions; correlation IDs; very high durability on committed transactions."))
    parts.append(_w_p("NFR-LOG-1 — No raw API secrets in logs; logging full student answers off by default (opt-in)."))
    parts.append(_w_p("NFR-ACC-1 — WCAG 2.1 Level AA on primary student flows; automated axe scan with zero critical violations on those flows."))
    parts.append(_w_p("NFR-I18N-1 — Externalized user-visible strings; English (en-US) for version 1."))
    parts.append(_w_p("NFR-DOC-1 — Operator documentation: deploy, environment variables, backup/restore, incident runbook; page limit per SRS."))

    parts.append(_w_h2("Document source"))
    parts.append(
        _w_p(
            "Generated for readability. Authoritative numbered requirements, acceptance tests, and schemas remain in "
            "requirements-specification-csc394-capstone.md."
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
    targets = [
        DOCS / "capstone-requirements-overview.docx",
        Path.home() / "capstone-requirements-overview.docx",
    ]
    for path in targets:
        try:
            write_docx(path)
            print(f"Wrote {path}")
        except PermissionError:
            alt = path.with_name(path.stem + " (generated).docx")
            write_docx(alt)
            print(f"Could not write {path}; wrote {alt}")


if __name__ == "__main__":
    main()
