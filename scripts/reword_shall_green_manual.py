"""
Rewrite SHALL / SHALL NOT in Green Group Project Manual.docx requirement bullets
to plain verb forms. Only replaces exact <w:t> text blobs that contain SHALL.
"""

from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path

EM = "\u2014"  # em dash in manual bullets


def _pairs() -> list[tuple[str, str]]:
    """(old_text, new_text) for each unique w:t string containing SHALL."""
    return [
        (
            f"CC-7.13-02 {EM} Bug fixes that restore intended behavior documented in §7.3–§7.6 are exempt from freeze but SHALL still be covered by tests when behavior is user-visible.",
            f"CC-7.13-02 {EM} Bug fixes that restore intended behavior documented in §7.3–§7.6 are exempt from freeze but still receive test coverage when behavior is user-visible.",
        ),
        (
            f"CC-7.13-03 {EM} LLM prompt or Together model changes that alter grading or question style SHALL be recorded in commit messages or docs/ notes so instructors can interpret score shifts across terms.",
            f"CC-7.13-03 {EM} LLM prompt or Together model changes that alter grading or question style are recorded in commit messages or docs/ notes so instructors can interpret score shifts across terms.",
        ),
        (
            f"CC-7.13-04 {EM} Database migration scripts or init_db behavior that affect production SQLite files SHALL be treated as high-impact changes requiring backup guidance in release notes.",
            f"CC-7.13-04 {EM} Database migration scripts or init_db behavior that affect production SQLite files are treated as high-impact changes requiring backup guidance in release notes.",
        ),
        (
            f"DOC-7.9.2-01 {EM} Run instructions SHALL stay consistent with actual entrypoints (app.main:app, default bind host/port).",
            f"DOC-7.9.2-01 {EM} Run instructions stay consistent with actual entrypoints (app.main:app, default bind host/port).",
        ),
        (
            f"DOC-7.9.2-02 {EM} Security-sensitive filenames (instructor_credentials.json) SHALL be called out as not for public repos when populated with real secrets.",
            f"DOC-7.9.2-02 {EM} Security-sensitive filenames (instructor_credentials.json) are called out as not for public repos when populated with real secrets.",
        ),
        (
            f"Exam configuration (student-selected) {EM} Students choose an education level (primary through graduate) and grading strictness (easy/balanced/strict/insane); these selections SHALL match allowed IDs enforced in exam_start and SHALL steer LLM prompts (ALLOWED_LEVEL_IDS, ALLOWED_STRICTNESS_IDS).",
            f"Exam configuration (student-selected) {EM} Students choose an education level (primary through graduate) and grading strictness (easy/balanced/strict/insane); these selections match allowed IDs enforced in exam_start and steer LLM prompts (ALLOWED_LEVEL_IDS, ALLOWED_STRICTNESS_IDS).",
        ),
        (
            f"FR-7.3.1-01 {EM} The system SHALL serve a home page at / with navigation to start or resume an exam.",
            f"FR-7.3.1-01 {EM} The system serves a home page at / with navigation to start or resume an exam.",
        ),
        (
            f"FR-7.3.1-02 {EM} The system SHALL serve an exam configuration page at /start where the student enters student ID, professor domain, education level, LLM mode (mock vs live), grading strictness, and number of questions (clamped to 1–20).",
            f"FR-7.3.1-02 {EM} The system serves an exam configuration page at /start where the student enters student ID, professor domain, education level, LLM mode (mock vs live), grading strictness, and number of questions (clamped to 1–20).",
        ),
        (
            f"FR-7.3.1-03 {EM} On POST /exam/start, the system SHALL validate student ID (non-empty after trim), education level against allowed IDs, grading strictness against allowed modes, and SHALL reject live mode when no Together API key is configured.",
            f"FR-7.3.1-03 {EM} On POST /exam/start, the system validates student ID (non-empty after trim), education level against allowed IDs, grading strictness against allowed modes, and rejects live mode when no Together API key is configured.",
        ),
        (
            f"FR-7.3.1-04 {EM} The system SHALL create or reuse a Student row keyed by external_student_id, create an ExamSession with status in_progress, assign a unique 5-character alphanumeric exam code, and generate the first question before redirecting to /exam/{{id}}/question.",
            f"FR-7.3.1-04 {EM} The system creates or reuses a Student row keyed by external_student_id, creates an ExamSession with status in_progress, assigns a unique 5-character alphanumeric exam code, and generates the first question before redirecting to /exam/{{id}}/question.",
        ),
        (
            f"FR-7.3.1-05 {EM} The system SHALL provide resume at /resume: accepting student ID and exam code, locating a matching in-progress session, and redirecting to the current question; otherwise returning field-level or not-found messages.",
            f"FR-7.3.1-05 {EM} The system provides resume at /resume: accepting student ID and exam code, locating a matching in-progress session, and redirecting to the current question; otherwise returning field-level or not-found messages.",
        ),
        (
            f"FR-7.3.1-06 {EM} While a session is completed, a GET on /exam/{{id}}/question SHALL redirect to /exam/{{id}}/results.",
            f"FR-7.3.1-06 {EM} While a session is completed, a GET on /exam/{{id}}/question redirects to /exam/{{id}}/results.",
        ),
        (
            f"FR-7.3.1-07 {EM} The question page SHALL display exam code, student ID, education level label, LLM mode label, grading strictness label, and question N of M with a progress bar.",
            f"FR-7.3.1-07 {EM} The question page displays exam code, student ID, education level label, LLM mode label, grading strictness label, and question N of M with a progress bar.",
        ),
        (
            f"FR-7.3.2-01 {EM} For the active question, the system SHALL render background information, essay question, and rubric (as a list when stored as JSON array, otherwise as text).",
            f"FR-7.3.2-01 {EM} For the active question, the system renders background information, essay question, and rubric (as a list when stored as JSON array, otherwise as text).",
        ),
        (
            f"FR-7.3.2-02 {EM} The system SHALL accept POST /exam/{{id}}/answer with a required answer body field, persist it on the current ExamQuestion, and advance the session according to whether more questions remain.",
            f"FR-7.3.2-02 {EM} The system accepts POST /exam/{{id}}/answer with a required answer body field, persists it on the current ExamQuestion, and advances the session according to whether more questions remain.",
        ),
        (
            f"FR-7.3.2-03 {EM} For intermediate questions (not the last), after grading the current answer the system SHALL create the next ExamQuestion using prior session questions summary as context and SHALL increment current_question_index.",
            f"FR-7.3.2-03 {EM} For intermediate questions (not the last), after grading the current answer the system creates the next ExamQuestion using prior session questions summary as context and increments current_question_index.",
        ),
        (
            f"FR-7.3.2-04 {EM} For the last question, the system SHALL persist the per-question grade, create a FinalGrade row, set session status to completed, store aggregate summary JSON on the session, and redirect to results.",
            f"FR-7.3.2-04 {EM} For the last question, the system persists the per-question grade, creates a FinalGrade row, sets session status to completed, stores aggregate summary JSON on the session, and redirects to results.",
        ),
        (
            f"FR-7.3.2-05 {EM} Duplicate submission after completion SHALL be treated idempotently: POST /exam/{{id}}/answer SHALL redirect to results without error.",
            f"FR-7.3.2-05 {EM} Duplicate submission after completion is treated idempotently: POST /exam/{{id}}/answer redirects to results without error.",
        ),
        (
            f"FR-7.3.2-06 {EM} The question page SHALL use client-side fetch for answer submission with a loading state (including overlay for non-final questions) and cancellation hooks on navigation/unload.",
            f"FR-7.3.2-06 {EM} The question page uses client-side fetch for answer submission with a loading state (including overlay for non-final questions) and cancellation hooks on navigation/unload.",
        ),
        (
            f"FR-7.3.3-01 {EM} The system SHALL call the LLM service to produce a structured payload containing at least background_information, essay_question, grading_rubric (stored as JSON text), and optional domain_notes, for the first and subsequent questions.",
            f"FR-7.3.3-01 {EM} The system calls the LLM service to produce a structured payload containing at least background_information, essay_question, grading_rubric (stored as JSON text), and optional domain_notes, for the first and subsequent questions.",
        ),
        (
            f"FR-7.3.3-02 {EM} Mock LLM mode SHALL supply deterministic mock question and grade payloads without external API calls.",
            f"FR-7.3.3-02 {EM} Mock LLM mode supplies deterministic mock question and grade payloads without external API calls.",
        ),
        (
            f"FR-7.3.3-03 {EM} Live mode SHALL use Together.ai chat completions with the configured model selection rules (together_model_for_requests).",
            f"FR-7.3.3-03 {EM} Live mode uses Together.ai chat completions with the configured model selection rules (together_model_for_requests).",
        ),
        (
            f"FR-7.3.3-04 {EM} Grading prompts SHALL incorporate education level guidance and grading strictness guidance (education_levels.py, grading_strictness.py).",
            f"FR-7.3.3-04 {EM} Grading prompts incorporate education level guidance and grading strictness guidance (education_levels.py, grading_strictness.py).",
        ),
        (
            f"FR-7.3.3-06 {EM} Per-question grade payloads SHALL be stored as JSON text on ExamQuestion.graded_state_p_json for display and instructor review.",
            f"FR-7.3.3-06 {EM} Per-question grade payloads are stored as JSON text on ExamQuestion.graded_state_p_json for display and instructor review.",
        ),
        (
            f"FR-7.3.4-01 {EM} The UI SHALL request hints via POST /exam/{{id}}/hint-json with form fields answer_draft, hint_query, selected_hint, and mode (hint or chat).",
            f"FR-7.3.4-01 {EM} The UI requests hints via POST /exam/{{id}}/hint-json with form fields answer_draft, hint_query, selected_hint, and mode (hint or chat).",
        ),
        (
            f"FR-7.3.4-02 {EM} Hint budget SHALL be enforced per exam session as a sum of hints_used across questions: easy = unlimited; balanced = 3; strict = 1; insane = 0.",
            f"FR-7.3.4-02 {EM} Hint budget is enforced per exam session as a sum of hints_used across questions: easy = unlimited; balanced = 3; strict = 1; insane = 0.",
        ),
        (
            f"FR-7.3.4-03 {EM} In chat mode with exhausted budget, the JSON response SHALL indicate exhaustion and return the configured “no hints” message without consuming further budget.",
            f"FR-7.3.4-03 {EM} In chat mode with exhausted budget, the JSON response indicates exhaustion and returns the configured “no hints” message without consuming further budget.",
        ),
        (
            f"FR-7.3.4-04 {EM} Hint reveal mode SHALL increment hints_used when a real hint is returned; chat mode SHALL increment hints_used when a substantive reply is returned, but SHALL not increment when the reply is only the generic off-topic redirection message.",
            f"FR-7.3.4-04 {EM} Hint reveal mode increments hints_used when a real hint is returned; chat mode increments hints_used when a substantive reply is returned, but does not increment when the reply is only the generic off-topic redirection message.",
        ),
        (
            f"FR-7.3.4-05 {EM} The system SHALL reject hint queries longer than 100 words with a JSON error payload (no hint consumption).",
            f"FR-7.3.4-05 {EM} The system rejects hint queries longer than 100 words with a JSON error payload (no hint consumption).",
        ),
        (
            f"FR-7.3.4-06 {EM} The system SHALL detect obvious prompt-injection patterns in combined student text and SHALL respond with a safe redirection message; behavior differs slightly between hint vs chat as implemented (history and budget updates).",
            f"FR-7.3.4-06 {EM} The system detects obvious prompt-injection patterns in combined student text and responds with a safe redirection message; behavior differs slightly between hint vs chat as implemented (history and budget updates).",
        ),
        (
            f"FR-7.3.4-07 {EM} For chat queries that are clearly unrelated to exam content (heuristic overlap with question context), the system SHALL return the off-topic message without charging the hint budget.",
            f"FR-7.3.4-07 {EM} For chat queries that are clearly unrelated to exam content (heuristic overlap with question context), the system returns the off-topic message without charging the hint budget.",
        ),
        (
            f"FR-7.3.4-08 {EM} The question page SHALL maintain carousel UI for hint history and AI helper history, collapsible hint panel, and word count display for the AI helper query (max 100 words).",
            f"FR-7.3.4-08 {EM} The question page maintains carousel UI for hint history and AI helper history, collapsible hint panel, and word count display for the AI helper query (max 100 words).",
        ),
        (
            f"FR-7.3.5-01 {EM} GET /exam/{{id}}/results SHALL render all questions in order with rubric breakdown (mapping rubric lines to dimension_scores when present), reference / model answer guidance derived from grade JSON or rubric text, and synthesized Strengths, Areas for improvement, and Suggestions sections (template labels: “Rubric breakdown”, “Reference answer guidance”, etc.).",
            f"FR-7.3.5-01 {EM} GET /exam/{{id}}/results renders all questions in order with rubric breakdown (mapping rubric lines to dimension_scores when present), reference / model answer guidance derived from grade JSON or rubric text, and synthesized Strengths, Areas for improvement, and Suggestions sections (template labels: “Rubric breakdown”, “Reference answer guidance”, etc.).",
        ),
        (
            f"FR-7.3.5-02 {EM} The system SHALL show per-question points computed as a percentage of a fixed 10 points per question, and an overall points total from the final grade percentage over the full exam.",
            f"FR-7.3.5-02 {EM} The system shows per-question points computed as a percentage of a fixed 10 points per question, and an overall points total from the final grade percentage over the full exam.",
        ),
        (
            f"FR-7.3.5-03 {EM} The system SHALL show an overall final summary extracted from final grade JSON when available.",
            f"FR-7.3.5-03 {EM} The system shows an overall final summary extracted from final grade JSON when available.",
        ),
        (
            f"FR-7.3.6-01 {EM} GET /professor and /professor/exam/{{id}} SHALL require an authenticated instructor session; unauthenticated users SHALL receive a 303 redirect to /professor/login?next=... with next limited to same-origin relative paths (no open redirect to //).",
            f"FR-7.3.6-01 {EM} GET /professor and /professor/exam/{{id}} require an authenticated instructor session; unauthenticated users receive a 303 redirect to /professor/login?next=... with next limited to same-origin relative paths (no open redirect to //).",
        ),
        (
            f"FR-7.3.6-02 {EM} POST /professor/login SHALL verify username/password against SHA-256(username) and PBKDF2-HMAC-SHA256(password) compared to values from instructor_credentials.json (auto-created with default derivatives if missing) or environment overrides.",
            f"FR-7.3.6-02 {EM} POST /professor/login verifies username/password against SHA-256(username) and PBKDF2-HMAC-SHA256(password) compared to values from instructor_credentials.json (auto-created with default derivatives if missing) or environment overrides.",
        ),
        (
            f"FR-7.3.6-03 {EM} Successful login SHALL set a signed session cookie (SessionMiddleware, cookie name rgee_instructor).",
            f"FR-7.3.6-03 {EM} Successful login sets a signed session cookie (SessionMiddleware, cookie name rgee_instructor).",
        ),
        (
            f"FR-7.3.6-04 {EM} POST /professor/logout SHALL clear the instructor session and redirect to login.",
            f"FR-7.3.6-04 {EM} POST /professor/logout clears the instructor session and redirects to login.",
        ),
        (
            f"FR-7.3.6-05 {EM} The dashboard SHALL list recent sessions (up to 200) ordered by creation time; the detail view SHALL mirror student results breakdown for that session.",
            f"FR-7.3.6-05 {EM} The dashboard lists recent sessions (up to 200) ordered by creation time; the detail view mirrors student results breakdown for that session.",
        ),
        (
            f"FR-7.3.7-01 {EM} The system SHALL log HTTP request duration and status for non-static routes into performance_logs, associating exam_session_id when derivable from the path or from /exam/start redirect location.",
            f"FR-7.3.7-01 {EM} The system logs HTTP request duration and status for non-static routes into performance_logs, associating exam_session_id when derivable from the path or from /exam/start redirect location.",
        ),
        (
            f"FR-7.3.7-02 {EM} The system SHALL expose GET /performance-log as an HTML table of recent rows (limit 400 in the handler), including links to professor exam detail when exam_session_id is present.",
            f"FR-7.3.7-02 {EM} The system exposes GET /performance-log as an HTML table of recent rows (limit 400 in the handler), including links to professor exam detail when exam_session_id is present.",
        ),
        (
            f"FR-7.3.7-03 {EM} POST /exam/{{id}}/client-timing SHALL accept client_ms_wall, clamp it to a safe range, log a client category event named generate_click_to_first_question_visible, and return 204 on success.",
            f"FR-7.3.7-03 {EM} POST /exam/{{id}}/client-timing accepts client_ms_wall, clamps it to a safe range, logs a client category event named generate_click_to_first_question_visible, and returns 204 on success.",
        ),
        (
            f"FR-7.3.7-04 {EM} The first-question page SHALL POST client timing once per session using sessionStorage keys (best-effort; errors swallowed client-side).",
            f"FR-7.3.7-04 {EM} The first-question page posts client timing once per session using sessionStorage keys (best-effort; errors swallowed client-side).",
        ),
        (
            f"FR-7.3.8-01 {EM} The system SHALL mount static files at /static and /assets.",
            f"FR-7.3.8-01 {EM} The system mounts static files at /static and /assets.",
        ),
        (
            f"FR-7.3.8-02 {EM} FastAPI SHALL expose interactive OpenAPI at /docs (default FastAPI behavior).",
            f"FR-7.3.8-02 {EM} FastAPI exposes interactive OpenAPI at /docs (default FastAPI behavior).",
        ),
        (
            f"FR-7.3.8-03 {EM} The home page SHALL include accessibility controls and ADHD focus highlighter hooks as asserted by tests (test_home_includes_accessibility_menu_and_focus_highlighter_controls).",
            f"FR-7.3.8-03 {EM} The home page includes accessibility controls and ADHD focus highlighter hooks as asserted by tests (test_home_includes_accessibility_menu_and_focus_highlighter_controls).",
        ),
        (
            "Functional IDs (FR-7.3.*) and non-functional IDs (NFR-7.4.*) in this document SHALL be mappable to pytest cases (e.g., test_full_exam_single_question_flow \u2194 FR-7.3.2 / FR-7.3.5, test_professor_requires_login \u2194 FR-7.3.6). New features SHOULD add or extend tests in the same packages rather than ad-hoc manual-only checks.",
            "Functional IDs (FR-7.3.*) and non-functional IDs (NFR-7.4.*) in this document are mappable to pytest cases (e.g., test_full_exam_single_question_flow \u2194 FR-7.3.2 / FR-7.3.5, test_professor_requires_login \u2194 FR-7.3.6). New features SHOULD add or extend tests in the same packages rather than ad-hoc manual-only checks.",
        ),
        (
            f"NFR-7.4.1-01 {EM} The system SHALL record durations in milliseconds for HTTP handling and LLM calls in performance_logs.",
            f"NFR-7.4.1-01 {EM} The system records durations in milliseconds for HTTP handling and LLM calls in performance_logs.",
        ),
        (
            f"NFR-7.4.1-02 {EM} SQLite deployments SHALL enable WAL journal mode, synchronous=NORMAL, and busy_timeout to reduce lock contention under concurrent access.",
            f"NFR-7.4.1-02 {EM} SQLite deployments enable WAL journal mode, synchronous=NORMAL, and busy_timeout to reduce lock contention under concurrent access.",
        ),
        (
            f"NFR-7.4.1-03 {EM} Performance log storage SHALL prune oldest rows when exceeding a configured cap (MAX_LOG_ROWS in perf_logging.py).",
            f"NFR-7.4.1-03 {EM} Performance log storage prunes oldest rows when exceeding a configured cap (MAX_LOG_ROWS in perf_logging.py).",
        ),
        (
            f"NFR-7.4.2-01 {EM} On SQLite database locked operational errors during answer submission, the system SHALL roll back and redirect in a way that avoids surfacing a 500 where possible (retry path to question or results as coded).",
            f"NFR-7.4.2-01 {EM} On SQLite database locked operational errors during answer submission, the system rolls back and redirects in a way that avoids surfacing a 500 where possible (retry path to question or results as coded).",
        ),
        (
            f"NFR-7.4.2-02 {EM} Concurrent final answer commits SHALL handle IntegrityError on final_grades by redirecting to results if a final row already exists.",
            f"NFR-7.4.2-02 {EM} Concurrent final answer commits handle IntegrityError on final_grades by redirecting to results if a final row already exists.",
        ),
        (
            f"NFR-7.4.2-04 {EM} Performance logging SHALL be best-effort (failures inside log_performance_event SHALL NOT break primary user flows).",
            f"NFR-7.4.2-04 {EM} Performance logging is best-effort (failures inside log_performance_event do not break primary user flows).",
        ),
        (
            f"NFR-7.4.3-01 {EM} The repository SHALL include pytest suites under tests/general and tests/security with shared fixtures (conftest.py) using isolated SQLite and mock LLM defaults.",
            f"NFR-7.4.3-01 {EM} The repository includes pytest suites under tests/general and tests/security with shared fixtures (conftest.py) using isolated SQLite and mock LLM defaults.",
        ),
        (
            f"NFR-7.4.3-02 {EM} Application logic SHALL be modularized into app/ packages (database, llm_service, instructor_auth, grading_strictness, education_levels, perf_logging, errors, etc.).",
            f"NFR-7.4.3-02 {EM} Application logic is modularized into app/ packages (database, llm_service, instructor_auth, grading_strictness, education_levels, perf_logging, errors, etc.).",
        ),
        (
            f"NFR-7.4.3-03 {EM} Changes to Together model selection SHALL be centralized in Settings.together_model_for_requests to avoid scattered magic strings.",
            f"NFR-7.4.3-03 {EM} Changes to Together model selection are centralized in Settings.together_model_for_requests to avoid scattered magic strings.",
        ),
        (
            f"NFR-7.4.4-01 {EM} HTTPException, RequestValidationError, TogetherApiError, and unhandled exceptions SHALL render HTML error pages (error.html) with generic user-facing copy—not raw JSON tracebacks to end users.",
            f"NFR-7.4.4-01 {EM} HTTPException, RequestValidationError, TogetherApiError, and unhandled exceptions render HTML error pages (error.html) with generic user-facing copy—not raw JSON tracebacks to end users.",
        ),
        (
            f"NFR-7.4.4-02 {EM} The question flow SHALL provide loading feedback during long-running submissions (overlay copy rotation for multi-question flows).",
            f"NFR-7.4.4-02 {EM} The question flow provides loading feedback during long-running submissions (overlay copy rotation for multi-question flows).",
        ),
        (
            f"NFR-7.4.4-03 {EM} The resume flow SHALL return actionable messages when student ID or exam ID is missing or no in-progress session matches.",
            f"NFR-7.4.4-03 {EM} The resume flow returns actionable messages when student ID or exam ID is missing or no in-progress session matches.",
        ),
        (
            "Numbering SHALL follow 7 (Requirements) \u2192 7.3 major functional block \u2192 7.3.x sub-area \u2192 FR-7.3.x-yy atomic IDs. Non-functional, technical, and security items follow 7.4, 7.5, 7.6 respectively. Sections 7.7–7.11 use descriptive subsection titles for roles, testing, documentation, risks, and revision control; 7.14–7.15 capture environmental assumptions and limits.",
            "Numbering follows 7 (Requirements) \u2192 7.3 major functional block \u2192 7.3.x sub-area \u2192 FR-7.3.x-yy atomic IDs. Non-functional, technical, and security items follow 7.4, 7.5, 7.6 respectively. Sections 7.7–7.11 use descriptive subsection titles for roles, testing, documentation, risks, and revision control; 7.14–7.15 capture environmental assumptions and limits.",
        ),
        (
            f"REV-7.11-01 {EM} This requirements document SHALL name a product version in the document control table and increment it when sections are materially added or renumbered.",
            f"REV-7.11-01 {EM} This requirements document names a product version in the document control table and increments it when sections are materially added or renumbered.",
        ),
        (
            f"REV-7.11-03 {EM} Traceability IDs (FR-, NFR-, etc.) SHALL remain stable where possible; if retired, the replacement ID SHOULD be noted in commit messages or change logs.",
            f"REV-7.11-03 {EM} Traceability IDs (FR-, NFR-, etc.) remain stable where possible; if retired, the replacement ID SHOULD be noted in commit messages or change logs.",
        ),
        (
            f"SR-7.6-01 {EM} Instructor passwords SHALL not be stored in plaintext in the default credentials file; only PBKDF2 and SHA-256 derivatives SHALL be stored (with iteration count metadata).",
            f"SR-7.6-01 {EM} Instructor passwords are not stored in plaintext in the default credentials file; only PBKDF2 and SHA-256 derivatives are stored (with iteration count metadata).",
        ),
        (
            f"SR-7.6-02 {EM} Instructor session integrity SHALL depend on INSTRUCTOR_SESSION_SECRET (or default dev constant) for cookie signing.",
            f"SR-7.6-02 {EM} Instructor session integrity depends on INSTRUCTOR_SESSION_SECRET (or default dev constant) for cookie signing.",
        ),
        (
            f"SR-7.6-03 {EM} Error responses tested under tests/security SHALL not embed Python tracebacks or filesystem paths for typical not-found and validation failures.",
            f"SR-7.6-03 {EM} Error responses tested under tests/security do not embed Python tracebacks or filesystem paths for typical not-found and validation failures.",
        ),
        (
            f"SR-7.6-04 {EM} The application SHALL apply basic prompt-injection heuristics on hint/helper inputs to limit misuse.",
            f"SR-7.6-04 {EM} The application applies basic prompt-injection heuristics on hint/helper inputs to limit misuse.",
        ),
        (
            f"SR-7.6-05 {EM} Instructor post-login redirects (next query/form) SHALL be restricted to safe same-origin relative paths to reduce open-redirect issues.",
            f"SR-7.6-05 {EM} Instructor post-login redirects (next query/form) are restricted to safe same-origin relative paths to reduce open-redirect issues.",
        ),
        (
            f"TE-7.8-01 {EM} Automated tests SHALL cover home, start, resume, exam flows (single- and multi-question), hint-json behaviors, professor auth, performance log, client timing, and security error bodies.",
            f"TE-7.8-01 {EM} Automated tests cover home, start, resume, exam flows (single- and multi-question), hint-json behaviors, professor auth, performance log, client timing, and security error bodies.",
        ),
        (
            f"TE-7.8-02 {EM} Tests SHALL run with mock LLM and isolated database configuration via pytest fixtures.",
            f"TE-7.8-02 {EM} Tests run with mock LLM and isolated database configuration via pytest fixtures.",
        ),
        (
            f"TR-7.5-01 {EM} The runtime stack SHALL be Python 3.11+ with FastAPI, Uvicorn (as per README), Jinja2 templates, SQLAlchemy ORM, and HTTPX for outbound Together API calls.",
            f"TR-7.5-01 {EM} The runtime stack is Python 3.11+ with FastAPI, Uvicorn (as per README), Jinja2 templates, SQLAlchemy ORM, and HTTPX for outbound Together API calls.",
        ),
        (
            f"TR-7.5-02 {EM} Default database SHALL be sqlite:///./exam_system.db unless overridden by database_url in settings.",
            f"TR-7.5-02 {EM} Default database is sqlite:///./exam_system.db unless overridden by database_url in settings.",
        ),
        (
            f"TR-7.5-03 {EM} Configuration SHALL be loaded via pydantic-settings from .env and environment variables (TOGETHER_API_KEY, MOCK_LLM, optional TOGETHER_MODEL / TOGETHER_USE_ENV_MODEL, instructor overrides, etc.).",
            f"TR-7.5-03 {EM} Configuration is loaded via pydantic-settings from .env and environment variables (TOGETHER_API_KEY, MOCK_LLM, optional TOGETHER_MODEL / TOGETHER_USE_ENV_MODEL, instructor overrides, etc.).",
        ),
        (
            f"TR-7.5-04 {EM} Container/CI workflows in .github/workflows SHALL exist for Python tests and optional static site / pages deployment (as present in repo).",
            f"TR-7.5-04 {EM} Container/CI workflows in .github/workflows exist for Python tests and optional static site / pages deployment (as present in repo).",
        ),
        (
            f"TR-7.5-05 {EM} The service SHALL expose machine-readable OpenAPI documentation at /docs for integrators and course demos.",
            f"TR-7.5-05 {EM} The service exposes machine-readable OpenAPI documentation at /docs for integrators and course demos.",
        ),
        (
            "When automated tests fail, the team SHALL record what failed (test name, traceback, environment: OS, Python version), root cause classification (product bug, flaky network for live tests, fixture drift), and fix verification by re-running the full tests/ tree or the minimal failing subset plus smoke tests. Live Together tests (if introduced) SHOULD be isolated behind markers to avoid CI nondeterminism unless secrets and quotas are guaranteed.",
            "When automated tests fail, the team records what failed (test name, traceback, environment: OS, Python version), root cause classification (product bug, flaky network for live tests, fixture drift), and fix verification by re-running the full tests/ tree or the minimal failing subset plus smoke tests. Live Together tests (if introduced) SHOULD be isolated behind markers to avoid CI nondeterminism unless secrets and quotas are guaranteed.",
        ),
    ]


def main() -> None:
    manual = Path(r"C:\Users\nigel\Downloads\Green Group Project Manual.docx")
    work = Path(os.environ.get("TEMP", ".")) / "shall_reword_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(manual, "r") as zin:
        zin.extractall(work)

    doc_xml = work / "word" / "document.xml"
    xml = doc_xml.read_text(encoding="utf-8")

    pairs = _pairs()
    # Longest-first to avoid accidental partial overlap (none expected, but safe)
    pairs.sort(key=lambda x: len(x[0]), reverse=True)
    for old, new in pairs:
        if old not in xml:
            raise SystemExit(f"Expected text not found in document.xml (encoding mismatch?): {old[:80]!r}")
        xml = xml.replace(old, new)

    if "SHALL" in xml or "shall" in xml.lower():
        # report remaining (case: 'should' contains shall? - 'SHOULD' has shall substring - check SHALL as word)
        import re as _re

        if _re.search(r"\bSHALL\b", xml, _re.I):
            raise SystemExit("SHALL still present after replacement; aborting.")

    doc_xml.write_text(xml, encoding="utf-8")

    out = Path(os.environ.get("TEMP", ".")) / "Green_Group_Project_Manual_shall_fixed.docx"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for f in sorted(work.rglob("*")):
            if f.is_file():
                zout.write(f, arcname=f.relative_to(work).as_posix())

    bak = manual.with_name(manual.stem + ".bak-before-shall-reword" + manual.suffix)
    shutil.copy2(manual, bak)
    os.replace(out, manual)
    print("Updated", manual)
    print("Backup", bak)


if __name__ == "__main__":
    main()
