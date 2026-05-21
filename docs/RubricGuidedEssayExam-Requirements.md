
**Document control**

| Field | Value |
|--------|--------|
| Product | RubricGuidedEssayExam (RGEE) — Modular Oral-Style Exam System |
| Version | 1.0 (as-implemented snapshot) |
| Source of truth | `app/`, `templates/`, `tests/`, `README.md` |

---

## 7. Requirements

### 7.1 Introduction

RubricGuidedEssayExam is a **browser-based web application** that delivers **multi-question, rubric-guided essay exams**. Students identify themselves with a **free-text student ID**, supply a **professor domain** description, and complete one or more generated essay items. The system uses a **large language model (LLM)** pipeline—either **mock (offline)** or **Together.ai (live)**—to generate questions with background context and a grading rubric, to produce **per-question grades** aligned to that rubric, and to compute a **session-level final grade** on the last submission. An **instructor-facing area** lists exam sessions and supports drill-down review of the same content students see on the results view, after **password-style authentication** backed by one-way derived credentials.

### 7.2 System Overview

At a high level, the system comprises:

1. **Web frontend** — Jinja2-rendered HTML pages with static CSS/JS under `templates/` and `static/`; optional loading overlay and client-side calls for hints and timing.
2. **HTTP API / server** — FastAPI application (`app/main.py`) exposing HTML routes for students and instructors, a JSON endpoint for interactive hints, a client timing endpoint, and OpenAPI documentation at `/docs`.
3. **LLM orchestration** — `app/llm_service.py` implements question generation, rubric-aware grading, combined “grade + next question” and “grade + final” flows, safe hints, and an AI-helper chat mode, with **mock payloads** when mock LLM mode is enabled.
4. **Persistence** — SQLAlchemy models (`app/database.py`) for students, exam sessions, questions, final grades, and performance logs; default **SQLite** with WAL pragmas and migrations for legacy schemas.
5. **Configuration** — Pydantic settings (`app/config.py`) from environment / `.env` for database URL, Together.ai key and model options, mock LLM flag, and instructor session secret / credential paths.
6. **Observability** — HTTP middleware and optional client POST record structured rows in `performance_logs`, viewable from `/performance-log`.

---

### 7.3 Functional Requirements

#### 7.3.1 Student entry, navigation, and session lifecycle

| ID | Requirement (as implemented) |
|----|--------------------------------|
| FR-7.3.1-01 | The system SHALL serve a **home page** at `/` with navigation to start or resume an exam. |
| FR-7.3.1-02 | The system SHALL serve an **exam configuration page** at `/start` where the student enters **student ID**, **professor domain**, **education level**, **LLM mode** (mock vs live), **grading strictness**, and **number of questions** (clamped to 1–20). |
| FR-7.3.1-03 | On **POST `/exam/start`**, the system SHALL validate student ID (non-empty after trim), education level against allowed IDs, grading strictness against allowed modes, and SHALL reject **live** mode when no Together API key is configured. |
| FR-7.3.1-04 | The system SHALL create or reuse a **Student** row keyed by `external_student_id`, create an **ExamSession** with status `in_progress`, assign a **unique 5-character alphanumeric exam code**, and generate the **first question** before redirecting to `/exam/{id}/question`. |
| FR-7.3.1-05 | The system SHALL provide **resume** at `/resume`: accepting student ID and exam code, locating a matching **in-progress** session, and redirecting to the current question; otherwise returning field-level or not-found messages. |
| FR-7.3.1-06 | While a session is **completed**, a GET on `/exam/{id}/question` SHALL redirect to `/exam/{id}/results`. |
| FR-7.3.1-07 | The question page SHALL display **exam code**, student ID, education level label, LLM mode label, grading strictness label, and **question N of M** with a progress bar. |

#### 7.3.2 Question presentation and answering

| ID | Requirement (as implemented) |
|----|--------------------------------|
| FR-7.3.2-01 | For the active question, the system SHALL render **background information**, **essay question**, and **rubric** (as a list when stored as JSON array, otherwise as text). |
| FR-7.3.2-02 | The system SHALL accept **POST `/exam/{id}/answer`** with a required **answer** body field, persist it on the current `ExamQuestion`, and advance the session according to whether more questions remain. |
| FR-7.3.2-03 | For **intermediate questions** (not the last), after grading the current answer the system SHALL create the **next** `ExamQuestion` using **prior session questions summary** as context and SHALL increment `current_question_index`. |
| FR-7.3.2-04 | For the **last** question, the system SHALL persist the per-question grade, create a **FinalGrade** row, set session status to **completed**, store aggregate summary JSON on the session, and redirect to results. |
| FR-7.3.2-05 | **Duplicate submission** after completion SHALL be treated idempotently: **POST `/exam/{id}/answer`** SHALL redirect to results without error. |
| FR-7.3.2-06 | The question page SHALL use **client-side fetch** for answer submission with a **loading state** (including overlay for non-final questions) and cancellation hooks on navigation/unload. |

*Note:* The data model includes `seconds_on_question`, but the current `exam_answer` handler does not populate it from the form (timing field is effectively unused in the handler as implemented).

#### 7.3.3 LLM-driven question generation and grading

| ID | Requirement (as implemented) |
|----|--------------------------------|
| FR-7.3.3-01 | The system SHALL call the LLM service to produce a structured payload containing at least **background_information**, **essay_question**, **grading_rubric** (stored as JSON text), and optional **domain_notes**, for the first and subsequent questions. |
| FR-7.3.3-02 | **Mock LLM mode** SHALL supply deterministic mock question and grade payloads without external API calls. |
| FR-7.3.3-03 | **Live mode** SHALL use Together.ai chat completions with the configured model selection rules (`together_model_for_requests`). |
| FR-7.3.3-04 | Grading prompts SHALL incorporate **education level guidance** and **grading strictness guidance** (`education_levels.py`, `grading_strictness.py`). |
| FR-7.3.3-05 | When model output JSON is invalid, the service MAY attempt a **single repair** completion to recover parseable JSON before failing with a user-facing error. |
| FR-7.3.3-06 | Per-question grade payloads SHALL be stored as JSON text on `ExamQuestion.graded_state_p_json` for display and instructor review. |

#### 7.3.4 Hints, AI helper, and hint budgets

| ID | Requirement (as implemented) |
|----|--------------------------------|
| FR-7.3.4-01 | The UI SHALL request hints via **POST `/exam/{id}/hint-json`** with form fields `answer_draft`, `hint_query`, `selected_hint`, and `mode` (`hint` or `chat`). |
| FR-7.3.4-02 | **Hint budget** SHALL be enforced per exam session as a sum of `hints_used` across questions: **easy** = unlimited; **balanced** = 3; **strict** = 1; **insane** = 0. |
| FR-7.3.4-03 | In **chat** mode with exhausted budget, the JSON response SHALL indicate exhaustion and return the configured “no hints” message without consuming further budget. |
| FR-7.3.4-04 | **Hint reveal** mode SHALL increment `hints_used` when a real hint is returned; **chat** mode SHALL increment `hints_used` when a substantive reply is returned, but SHALL **not** increment when the reply is only the generic off-topic redirection message. |
| FR-7.3.4-05 | The system SHALL reject **hint queries longer than 100 words** with a JSON error payload (no hint consumption). |
| FR-7.3.4-06 | The system SHALL detect **obvious prompt-injection patterns** in combined student text and SHALL respond with a safe redirection message; behavior differs slightly between hint vs chat as implemented (history and budget updates). |
| FR-7.3.4-07 | For **chat** queries that are clearly unrelated to exam content (heuristic overlap with question context), the system SHALL return the off-topic message **without** charging the hint budget. |
| FR-7.3.4-08 | The question page SHALL maintain **carousel UI** for hint history and AI helper history, collapsible hint panel, and **word count** display for the AI helper query (max 100 words). |

#### 7.3.5 Results and scoring presentation

| ID | Requirement (as implemented) |
|----|--------------------------------|
| FR-7.3.5-01 | **GET `/exam/{id}/results`** SHALL render all questions in order with **rubric breakdown** (mapping rubric lines to `dimension_scores` when present), **reference / model answer guidance** derived from grade JSON or rubric text, and synthesized **Strengths**, **Areas for improvement**, and **Suggestions** sections (template labels: “Rubric breakdown”, “Reference answer guidance”, etc.). |
| FR-7.3.5-02 | The system SHALL show **per-question points** computed as a percentage of a fixed **10 points per question**, and an **overall points** total from the final grade percentage over the full exam. |
| FR-7.3.5-03 | The system SHALL show an **overall final summary** extracted from final grade JSON when available. |

#### 7.3.6 Instructor dashboard and authentication

| ID | Requirement (as implemented) |
|----|--------------------------------|
| FR-7.3.6-01 | **GET `/professor` and `/professor/exam/{id}`** SHALL require an authenticated instructor session; unauthenticated users SHALL receive a **303 redirect** to `/professor/login?next=...` with `next` limited to same-origin relative paths (no open redirect to `//`). |
| FR-7.3.6-02 | **POST `/professor/login`** SHALL verify username/password against **SHA-256(username)** and **PBKDF2-HMAC-SHA256(password)** compared to values from `instructor_credentials.json` (auto-created with default derivatives if missing) or environment overrides. |
| FR-7.3.6-03 | Successful login SHALL set a signed session cookie (`SessionMiddleware`, cookie name `rgee_instructor`). |
| FR-7.3.6-04 | **POST `/professor/logout`** SHALL clear the instructor session and redirect to login. |
| FR-7.3.6-05 | The dashboard SHALL list recent sessions (up to 200) ordered by creation time; the detail view SHALL mirror student results breakdown for that session. |

#### 7.3.7 Diagnostics and client-reported timing

| ID | Requirement (as implemented) |
|----|--------------------------------|
| FR-7.3.7-01 | The system SHALL log **HTTP request duration** and status for non-static routes into `performance_logs`, associating `exam_session_id` when derivable from the path or from `/exam/start` redirect location. |
| FR-7.3.7-02 | The system SHALL expose **GET `/performance-log`** as an HTML table of recent rows (limit 400 in the handler), including links to professor exam detail when `exam_session_id` is present. |
| FR-7.3.7-03 | **POST `/exam/{id}/client-timing`** SHALL accept `client_ms_wall`, clamp it to a safe range, log a **client** category event named `generate_click_to_first_question_visible`, and return **204** on success. |
| FR-7.3.7-04 | The first-question page SHALL POST client timing once per session using `sessionStorage` keys (best-effort; errors swallowed client-side). |

#### 7.3.8 Static content, OpenAPI, and accessibility affordances

| ID | Requirement (as implemented) |
|----|--------------------------------|
| FR-7.3.8-01 | The system SHALL mount **static** files at `/static` and `/assets`. |
| FR-7.3.8-02 | FastAPI SHALL expose **interactive OpenAPI** at `/docs` (default FastAPI behavior). |
| FR-7.3.8-03 | The home page SHALL include **accessibility** controls and **ADHD focus highlighter** hooks as asserted by tests (`test_home_includes_accessibility_menu_and_focus_highlighter_controls`). |

---

### 7.4 Non-Functional Requirements

#### 7.4.1 Performance

| ID | Requirement (as implemented) |
|----|--------------------------------|
| NFR-7.4.1-01 | The system SHALL record **durations in milliseconds** for HTTP handling and LLM calls in `performance_logs`. |
| NFR-7.4.1-02 | SQLite deployments SHALL enable **WAL journal mode**, `synchronous=NORMAL`, and **busy_timeout** to reduce lock contention under concurrent access. |
| NFR-7.4.1-03 | Performance log storage SHALL **prune** oldest rows when exceeding a configured cap (`MAX_LOG_ROWS` in `perf_logging.py`). |

#### 7.4.2 Reliability and defensive behavior

| ID | Requirement (as implemented) |
|----|--------------------------------|
| NFR-7.4.2-01 | On **SQLite database locked** operational errors during answer submission, the system SHALL roll back and **redirect** in a way that avoids surfacing a 500 where possible (retry path to question or results as coded). |
| NFR-7.4.2-02 | Concurrent **final answer** commits SHALL handle **IntegrityError** on `final_grades` by redirecting to results if a final row already exists. |
| NFR-7.4.2-03 | **LLM JSON repair** (single retry) improves resilience to malformed model output before failing. |

#### 7.4.3 Maintainability

| ID | Requirement (as implemented) |
|----|--------------------------------|
| NFR-7.4.3-01 | The repository SHALL include **pytest** suites under `tests/general` and `tests/security` with shared fixtures (`conftest.py`) using isolated SQLite and mock LLM defaults. |
| NFR-7.4.3-02 | Application logic SHALL be modularized into `app/` packages (`database`, `llm_service`, `instructor_auth`, `grading_strictness`, `education_levels`, `perf_logging`, `errors`, etc.). |

#### 7.4.4 Usability and error presentation

| ID | Requirement (as implemented) |
|----|--------------------------------|
| NFR-7.4.4-01 | **HTTPException**, **RequestValidationError**, **TogetherApiError**, and unhandled exceptions SHALL render **HTML error pages** (`error.html`) with generic user-facing copy—not raw JSON tracebacks to end users. |
| NFR-7.4.4-02 | The question flow SHALL provide **loading feedback** during long-running submissions (overlay copy rotation for multi-question flows). |

---

### 7.5 Technical Requirements

| ID | Requirement (as implemented) |
|----|--------------------------------|
| TR-7.5-01 | The runtime stack SHALL be **Python 3.11+** with **FastAPI**, **Uvicorn** (as per README), **Jinja2** templates, **SQLAlchemy** ORM, and **HTTPX** for outbound Together API calls. |
| TR-7.5-02 | Default database SHALL be **`sqlite:///./exam_system.db`** unless overridden by `database_url` in settings. |
| TR-7.5-03 | Configuration SHALL be loaded via **pydantic-settings** from `.env` and environment variables (`TOGETHER_API_KEY`, `MOCK_LLM`, optional `TOGETHER_MODEL` / `TOGETHER_USE_ENV_MODEL`, instructor overrides, etc.). |
| TR-7.5-04 | Container/CI workflows in `.github/workflows` SHALL exist for **Python tests** and optional **static site / pages** deployment (as present in repo). |

---

### 7.6 Security and Integrity Requirements

| ID | Requirement (as implemented) |
|----|--------------------------------|
| SR-7.6-01 | Instructor passwords SHALL **not** be stored in plaintext in the default credentials file; only **PBKDF2** and **SHA-256** derivatives SHALL be stored (with iteration count metadata). |
| SR-7.6-02 | Instructor session integrity SHALL depend on **`INSTRUCTOR_SESSION_SECRET`** (or default dev constant) for cookie signing. |
| SR-7.6-03 | Error responses tested under `tests/security` SHALL **not** embed Python tracebacks or filesystem paths for typical not-found and validation failures. |
| SR-7.6-04 | The application SHALL apply **basic prompt-injection heuristics** on hint/helper inputs to limit misuse. |

---

### 7.7 Education levels and grading modes (domain configuration)

These are not external “users” in a separate profile system; they are **enumerated configuration** driving prompts and UI.

| ID | Requirement (as implemented) |
|----|--------------------------------|
| CFG-7.7-01 | Education levels SHALL be one of: **primary**, **middle**, **high_school**, **college**, **graduate** (default **college**). |
| CFG-7.7-02 | Grading strictness SHALL be one of: **easy**, **balanced**, **strict**, **insane** (default **balanced**), affecting both mock score demos and LLM grading guidance. |

---

### 7.8 Testing requirements (as evidenced in repo)

| ID | Requirement (as implemented) |
|----|--------------------------------|
| TE-7.8-01 | Automated tests SHALL cover **home**, **start**, **resume**, **exam flows** (single- and multi-question), **hint-json** behaviors, **professor auth**, **performance log**, **client timing**, and **security** error bodies. |
| TE-7.8-02 | Tests SHALL run with **mock LLM** and isolated database configuration via pytest fixtures. |

---

### 7.9 Traceability keys

Requirements in this document use hierarchical IDs:

- **FR-7.3.x-yy** — Functional  
- **NFR-7.4.x-yy** — Non-functional  
- **TR-7.5-xx** — Technical  
- **SR-7.6-xx** — Security  
- **CFG-7.7-xx** — Enumerated configuration  
- **TE-7.8-xx** — Testing evidence  


---

### 7.10 Assumptions and constraints (implementation-bound)

1. **Single-server deployment** — Session cookies and SQLite file paths assume a single application instance or shared filesystem appropriate to that deployment model.  
2. **Together.ai availability** — Live mode depends on external API reachability and valid credentials.  
3. **Instructor area is not multi-tenant** — The dashboard lists sessions globally for the deployment’s database, not per-organization partitions.  
4. **Student identity** — There is no password login for students; anyone with another student’s ID and exam code could resume that in-progress exam if they obtain both values.

---

