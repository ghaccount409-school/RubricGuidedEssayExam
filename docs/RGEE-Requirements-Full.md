# RubricGuidedEssayExam (RGEE) — Requirements

This document defines **Section 7 — Requirements** for RubricGuidedEssayExam (RGEE): introduction, system overview, functional requirements, non-functional requirements (performance, reliability, maintainability, usability), technical requirements, security and integrity, user roles and training, testing, documentation, risk controls, change control, assumptions, and constraints. **Behavioral statements are grounded in the current implementation** (`app/`, `templates/`, `tests/`, `README.md`). Process-oriented sections (testing roles, training, change control) describe **how the project is operated and governed** for course or production use of RGEE.

**Document control**

| Field | Value |
|--------|--------|
| Product | RubricGuidedEssayExam (RGEE) — Modular Oral-Style Exam System |
| Version | 1.1 |
| Source of truth | `app/`, `templates/`, `tests/`, `README.md` |

**Canonical copy:** Prefer `docs/RubricGuidedEssayExam-Requirements.md` as the primary filename in the repository. If that path is locked by another program, copy this file over it when the lock clears, then you may delete this duplicate if you want a single file.

---

## 7. Requirements

### 7.1 Introduction

RubricGuidedEssayExam is a **browser-based web application** that delivers **multi-question, rubric-guided essay exams**. Students identify themselves with a **free-text student ID**, supply a **professor domain** description, and complete one or more generated essay items. The system uses a **large language model (LLM)** pipeline—either **mock (offline)** or **Together.ai (live)**—to generate questions with background context and a grading rubric, to produce **per-question grades** aligned to that rubric, and to compute a **session-level final grade** on the last submission. An **instructor-facing area** lists exam sessions and supports drill-down review of the same content students see on the results view, after **password-style authentication** backed by one-way derived credentials.

### 7.2 System overview

At a high level, the system comprises:

1. **Web frontend** — Jinja2-rendered HTML pages with static CSS/JS under `templates/` and `static/`; optional loading overlay and client-side calls for hints and timing.
2. **HTTP API / server** — FastAPI application (`app/main.py`) exposing HTML routes for students and instructors, a JSON endpoint for interactive hints, a client timing endpoint, and OpenAPI documentation at `/docs`.
3. **LLM orchestration** — `app/llm_service.py` implements question generation, rubric-aware grading, combined “grade + next question” and “grade + final” flows, and **`generate_safe_hint`**-based assistance (including the **AI Helper** UX when the client sends `mode=chat` to `hint-json`). **Mock payloads** apply when mock LLM mode is enabled. A separate **`generate_ai_helper_reply`** helper also exists in `llm_service.py`, but it is **not** invoked by `hint-json` (the shipped question page); it is only referenced from the legacy **`POST /exam/{id}/hint`** HTML handler, which is **broken** (undefined variables) if called without the JavaScript path.
4. **Persistence** — SQLAlchemy models (`app/database.py`) for students, exam sessions, questions, final grades, and performance logs; default **SQLite** with WAL pragmas and migrations for legacy schemas.
5. **Configuration** — Pydantic settings (`app/config.py`) from environment / `.env` for database URL, Together.ai key and model options, mock LLM flag, and instructor session secret / credential paths.
6. **Observability** — HTTP middleware and optional client POST record structured rows in `performance_logs`, viewable from `/performance-log`.

---

### 7.3 Functional requirements

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
| FR-7.3.4-09 | **Implementation note:** For `hint-json`, both **hint** and **chat** modes call **`generate_safe_hint`** (the chat query is folded into `student_text`). The function **`generate_ai_helper_reply`** exists but is **not** used by `hint-json`. The alternate **`POST /exam/{id}/hint`** HTML endpoint is not used by the bundled question-page script and would **raise** if submitted, due to undefined identifiers in `exam_hint`. |

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

### 7.4 Non-functional requirements

Non-functional requirements specify **how well** RGEE performs its functions: responsiveness and observability, resilience under failure and concurrency, ease of ongoing change, and quality of the end-user experience. Subsections are grouped as **performance**, **reliability**, **maintainability**, and **usability**.

#### 7.4.1 Performance

RGEE is sensitive to **LLM latency** (question generation, combined grade-and-advance, and hint/helper calls) and to **database contention** when SQLite is used with concurrent writers. The product mitigates this by logging **HTTP** and **LLM** durations into `performance_logs`, enabling operators to correlate slow pages with backend events; by applying **SQLite WAL mode**, `synchronous=NORMAL`, and **busy_timeout**; and by **pruning** old log rows so diagnostic storage does not grow without bound.

| ID | Requirement (as implemented) |
|----|--------------------------------|
| NFR-7.4.1-01 | The system SHALL record **durations in milliseconds** for HTTP handling and LLM calls in `performance_logs`. |
| NFR-7.4.1-02 | SQLite deployments SHALL enable **WAL journal mode**, `synchronous=NORMAL`, and **busy_timeout** to reduce lock contention under concurrent access. |
| NFR-7.4.1-03 | Performance log storage SHALL **prune** oldest rows when exceeding a configured cap (`MAX_LOG_ROWS` in `perf_logging.py`). |
| NFR-7.4.1-04 | The system SHOULD support **client-reported wall time** from first “generate” interaction to first question visible, via `/exam/{id}/client-timing`, for UX analysis alongside server-side timings. |

#### 7.4.2 Reliability

Reliability covers **correct behavior under duplicates, races, and partial failures**: idempotent answer submission after exam completion, graceful handling of SQLite “database is locked,” and recovery when the LLM returns malformed JSON (single repair attempt). Together.ai failures surface as controlled **TogetherApiError** responses rather than unhandled stack traces in the HTML path.

| ID | Requirement (as implemented) |
|----|--------------------------------|
| NFR-7.4.2-01 | On **SQLite database locked** operational errors during answer submission, the system SHALL roll back and **redirect** in a way that avoids surfacing a 500 where possible (retry path to question or results as coded). |
| NFR-7.4.2-02 | Concurrent **final answer** commits SHALL handle **IntegrityError** on `final_grades` by redirecting to results if a final row already exists. |
| NFR-7.4.2-03 | **LLM JSON repair** (single retry) improves resilience to malformed model output before failing. |
| NFR-7.4.2-04 | Performance logging SHALL be **best-effort** (failures inside `log_performance_event` SHALL NOT break primary user flows). |

#### 7.4.3 Maintainability

Maintainability ensures the team can **extend prompts, routes, and policies** without destabilizing unrelated behavior. RGEE separates concerns into modules (`llm_service`, `database`, `instructor_auth`, `grading_strictness`, `education_levels`, `prompts`, `perf_logging`), supplies **pytest** coverage for HTTP and security regressions, and documents run/test procedures in `README.md`.

| ID | Requirement (as implemented) |
|----|--------------------------------|
| NFR-7.4.3-01 | The repository SHALL include **pytest** suites under `tests/general` and `tests/security` with shared fixtures (`conftest.py`) using isolated SQLite and mock LLM defaults. |
| NFR-7.4.3-02 | Application logic SHALL be modularized into `app/` packages (`database`, `llm_service`, `instructor_auth`, `grading_strictness`, `education_levels`, `perf_logging`, `errors`, etc.). |
| NFR-7.4.3-03 | Changes to Together model selection SHALL be centralized in **`Settings.together_model_for_requests`** to avoid scattered magic strings. |

#### 7.4.4 Usability

Usability requirements address **clarity for students and instructors** and **error comprehension**. RGEE uses server-rendered HTML with consistent panels, progress indication during long submits, hint/AI helper affordances (tabs, carousel, collapsible panel), and friendly **`error.html`** pages for common failure classes so users are not exposed to raw API JSON or tracebacks.

| ID | Requirement (as implemented) |
|----|--------------------------------|
| NFR-7.4.4-01 | **HTTPException**, **RequestValidationError**, **TogetherApiError**, and unhandled exceptions SHALL render **HTML error pages** (`error.html`) with generic user-facing copy—not raw JSON tracebacks to end users. |
| NFR-7.4.4-02 | The question flow SHALL provide **loading feedback** during long-running submissions (overlay copy rotation for multi-question flows). |
| NFR-7.4.4-03 | The resume flow SHALL return **actionable messages** when student ID or exam ID is missing or no in-progress session matches. |

---

### 7.5 Technical requirements

Technical requirements define the **implementation stack, deployment interfaces, and operational knobs** for RGEE. The system is a **Python** service exposing **HTTP** on a configurable host/port (documented default `127.0.0.1:8000` with Uvicorn), backed by a **SQLAlchemy** database URL defaulting to file-based SQLite, and optionally calling **Together.ai** over HTTPS via HTTPX. Configuration is **environment-driven** through `.env` / process environment for API keys, mock mode, database URL, instructor secrets, and optional credential file path.

| ID | Requirement (as implemented) |
|----|--------------------------------|
| TR-7.5-01 | The runtime stack SHALL be **Python 3.11+** with **FastAPI**, **Uvicorn** (as per README), **Jinja2** templates, **SQLAlchemy** ORM, and **HTTPX** for outbound Together API calls. |
| TR-7.5-02 | Default database SHALL be **`sqlite:///./exam_system.db`** unless overridden by `database_url` in settings. |
| TR-7.5-03 | Configuration SHALL be loaded via **pydantic-settings** from `.env` and environment variables (`TOGETHER_API_KEY`, `MOCK_LLM`, optional `TOGETHER_MODEL` / `TOGETHER_USE_ENV_MODEL`, instructor overrides, etc.). |
| TR-7.5-04 | Container/CI workflows in `.github/workflows` SHALL exist for **Python tests** and optional **static site / pages** deployment (as present in repo). |
| TR-7.5-05 | The service SHALL expose machine-readable **OpenAPI** documentation at `/docs` for integrators and course demos. |

---

### 7.6 Security and integrity requirements

Security and integrity requirements protect **instructor accounts**, **session state**, and **student-facing surfaces** from casual abuse, while acknowledging RGEE’s classroom-scale threat model (not a full multi-tenant SaaS). Instructor passwords are verified via **slow hashing** (PBKDF2) and usernames via **SHA-256** compared to stored derivatives; session cookies are signed with **`INSTRUCTOR_SESSION_SECRET`**. Student flows rely on **knowledge of exam code** plus student ID for resume, not passwords. Hint and AI-helper inputs pass through **lightweight misuse heuristics** (injection phrases, off-topic detection). Error pages are tested to avoid leaking **tracebacks** and internal paths to browsers.

| ID | Requirement (as implemented) |
|----|--------------------------------|
| SR-7.6-01 | Instructor passwords SHALL **not** be stored in plaintext in the default credentials file; only **PBKDF2** and **SHA-256** derivatives SHALL be stored (with iteration count metadata). |
| SR-7.6-02 | Instructor session integrity SHALL depend on **`INSTRUCTOR_SESSION_SECRET`** (or default dev constant) for cookie signing. |
| SR-7.6-03 | Error responses tested under `tests/security` SHALL **not** embed Python tracebacks or filesystem paths for typical not-found and validation failures. |
| SR-7.6-04 | The application SHALL apply **basic prompt-injection heuristics** on hint/helper inputs to limit misuse. |
| SR-7.6-05 | Instructor **post-login redirects** (`next` query/form) SHALL be restricted to safe same-origin relative paths to reduce open-redirect issues. |
| SR-7.6-06 | **Grade and rubric integrity** at the application level means: once persisted, per-question JSON grades and final summaries are the source for student and instructor views (no secondary hidden scoring engine in code paths outside `llm_service` + mock). |

---

### 7.7 User profile and training requirements

This section defines **user profile and training** expectations: who interacts with RGEE, what they must understand, and what training is expected before safe use in a course or demo.

#### 7.7.1 User roles

| Role | Description (RGEE) |
|------|---------------------|
| **Student / examinee** | Uses the public student UI: home, start exam, optional resume, question/answer, hints/AI helper, and results. Identified by a **self-declared student ID** string; receives a short **exam code** for resumption. |
| **Instructor / course staff** | Uses `/professor/login`, dashboard, session detail, and logout. Reviews stored prompts, answers, and model-generated grades; does not edit rubrics in-place in the current product (rubric is LLM-generated per question). |
| **System operator / developer** | Installs dependencies, configures `.env`, runs Uvicorn, manages `instructor_credentials.json` or env overrides, may inspect `/performance-log` and `/docs`, and is responsible for database backups when SQLite (or another DB URL) is used. |
| **External LLM provider** | Together.ai (when not in mock mode) processes prompts constructed by RGEE; availability and data-handling terms are governed by the provider agreement, not by this document. |

#### 7.7.2 Skill and education requirements by role

| Role | Skills and knowledge (RGEE-specific) |
|------|--------------------------------------|
| **Student** | Basic **web literacy** (forms, navigation), ability to read essay prompts and rubric lists, understanding that **hints are limited** by grading strictness, and awareness that the **AI helper does not replace** course policies on authorized aid. |
| **Instructor** | Ability to **interpret LLM-generated grades** as advisory, to use the dashboard to audit attempts, and to **rotate credentials** away from any sample defaults before production use. Familiarity with **mock vs live** mode is required to avoid accidental live API usage during dry runs. |
| **System operator** | **Python virtual environments**, environment files, and command-line server startup; optional **GitHub Actions** literacy for CI; understanding of **API keys** (`TOGETHER_API_KEY`) and **`INSTRUCTOR_SESSION_SECRET`** rotation. |
| **Exam configuration (student-selected)** | Students choose an **education level** (primary through graduate) and **grading strictness** (easy/balanced/strict/insane); these selections SHALL match allowed IDs enforced in `exam_start` and SHALL steer LLM prompts (`ALLOWED_LEVEL_IDS`, `ALLOWED_STRICTNESS_IDS`). |

#### 7.7.3 Training requirements

| Audience | Training topic | Rationale |
|----------|----------------|-----------|
| **Students** | How to **save the exam code**, use **Resume**, and when **hints/AI helper** count against the session budget. | Prevents accidental loss of progress and confusion during high-stakes attempts. |
| **Instructors** | How to **log in**, locate a session, read **rubric breakdown** vs model JSON, and **log out** on shared machines. | Protects session confidentiality on lab PCs. |
| **Operators** | **Mock-first** demos (`MOCK_LLM`), safe `.env` handling, and **not committing** live keys or plaintext instructor secrets. | Aligns deployment practice with repo `.gitignore` / security expectations. |
| **Course staff (live mode)** | **Together.ai** quota/latency expectations and **fallback messaging** when the provider errors. | Reduces support load during exams if the network or API degrades. |

---

### 7.8 Testing requirements

Testing requirements ensure RGEE behavior remains **verifiable and regression-resistant** as prompts and routes evolve, with explicit **test plans**, **roles**, **traceability**, and **sign-off** expectations.

#### 7.8.1 Test plan (critical paths)

The **critical path** for RGEE is: start session → answer one or more questions → receive results; optional branches include **resume**, **hint-json** (hint and chat modes), **professor login and review**, **performance log** linkage, and **client timing** POST. Automated tests in `tests/general/test_api.py` and `tests/security/test_http.py` exercise these paths against **mock LLM** and an **isolated SQLite** database provided by pytest fixtures (`conftest.py`). Running `python -m pytest tests/ -v` (per README) is the canonical full-suite command for developers.

| ID | Requirement (as evidenced in repo) |
|----|-------------------------------------|
| TE-7.8-01 | Automated tests SHALL cover **home**, **start**, **resume**, **exam flows** (single- and multi-question), **hint-json** behaviors, **professor auth**, **performance log**, **client timing**, and **security** error bodies. |
| TE-7.8-02 | Tests SHALL run with **mock LLM** and isolated database configuration via pytest fixtures. |

#### 7.8.2 Testing roles

| Role | Responsibility |
|------|----------------|
| **Developer / CI** | Run pytest on each change; keep fixtures compatible with SQLite isolation patterns already in `conftest.py`. |
| **Reviewer** | Treat failing **security** tests (`tests/security`) as release blockers for any change touching error handlers or templates. |
| **Demonstrator** | Before class demos, run a **smoke path** (start → one answer → results) in both **mock** and, if applicable, **live** configuration. |

#### 7.8.3 Traceability and verification

Functional IDs (**FR-7.3.\***) and non-functional IDs (**NFR-7.4.\***) in this document SHALL be mappable to pytest cases (e.g., `test_full_exam_single_question_flow` ↔ FR-7.3.2 / FR-7.3.5, `test_professor_requires_login` ↔ FR-7.3.6). New features SHOULD add or extend tests in the same packages rather than ad-hoc manual-only checks.

#### 7.8.4 Failed test records and re-testing

When automated tests fail, the team SHALL record **what failed** (test name, traceback, environment: OS, Python version), **root cause classification** (product bug, flaky network for live tests, fixture drift), and **fix verification** by re-running the full `tests/` tree or the minimal failing subset plus smoke tests. Live Together tests (if introduced) SHOULD be isolated behind markers to avoid CI nondeterminism unless secrets and quotas are guaranteed.

#### 7.8.5 Test sign-off

A release or demo milestone for RGEE SHOULD be considered **test-signed** when: (1) `python -m pytest tests/ -v` passes on the target branch; (2) manual smoke of **instructor login** succeeds with the credentials intended for that environment; and (3) any **configuration checklist** items in §7.5 (keys, secrets) are verified for that deployment.

---

### 7.9 Documentation requirements

Documentation requirements ensure knowledge transfers beyond the codebase, split between **role-based documentation** and **documentation quality** expectations.

#### 7.9.1 Documentation by user role

| Role | Required documentation (RGEE) |
|------|-------------------------------|
| **Student** | README sections: URLs for home/start/professor, how to run locally if self-hosted; in-course handouts MAY add exam-code safety tips. |
| **Instructor** | README professor URLs; operational note to **replace default instructor derivatives**; how to read dashboard vs student results parity. |
| **Developer / operator** | README: Python version, venv, `pip install -r requirements.txt`, `.env.example`, `MOCK_LLM` vs `TOGETHER_API_KEY`, Uvicorn command, pytest command; optional `docs/` generators for traceability artifacts. |

#### 7.9.2 Documentation quality requirements

| ID | Requirement |
|----|-------------|
| DOC-7.9.2-01 | Run instructions SHALL stay **consistent** with actual entrypoints (`app.main:app`, default bind host/port). |
| DOC-7.9.2-02 | Security-sensitive filenames (**`instructor_credentials.json`**) SHALL be called out as **not for public repos** when populated with real secrets. |
| DOC-7.9.2-03 | Requirements documents (including this file) SHOULD state **as-implemented** vs **aspirational** behavior explicitly when they differ (e.g., `seconds_on_question` persistence). |

---

### 7.10 Bad developer / bad client risk requirements

This section identifies **process risks**: ways development or client misuse could undermine RGEE despite sound code.

| Risk category | Example (RGEE) | Mitigation requirement |
|---------------|----------------|-------------------------|
| **Bad developer practice** | Committing **`.env`**, live **Together** keys, or real **`instructor_credentials.json`** to Git. | Use secrets scanning, `.gitignore`, and team review; rotate any leaked keys immediately. |
| **Bad developer practice** | Shipping with **default `INSTRUCTOR_SESSION_SECRET`** or sample PBKDF2/SHA files in production. | Checklist item before deploy: set long random secret and custom credential derivatives. |
| **Bad developer practice** | Disabling tests or ignoring **security** failures to “merge faster.” | Policy: CI test gate on `tests/`; security tests are blocking. |
| **Client / operator misuse** | Running **live** LLM during a drill without budget or consent. | Default demos to **mock**; document cost/latency in README. |
| **Client misuse** | Treating **LLM percentage grades** as legally binding outcomes without human review. | Course policy and syllabus language outside this spec; RGEE presents model output as advisory tooling. |
| **Student misuse** | Sharing exam codes publicly mid-exam. | Instructional design: treat codes like seat tokens; consider proctoring policies external to RGEE. |

---

### 7.11 Author, editor, and revision requirements

| ID | Requirement |
|----|-------------|
| REV-7.11-01 | This requirements document SHALL name a **product version** in the document control table and increment it when sections are materially added or renumbered. |
| REV-7.11-02 | Functional changes to routes, persistence, or LLM contracts SHOULD update **both** code/tests and the corresponding **FR/NFR** rows in §7.3–§7.4 in the same change set when feasible. |
| REV-7.11-03 | Traceability IDs (**FR-**, **NFR-**, etc.) SHALL remain **stable** where possible; if retired, the replacement ID SHOULD be noted in commit messages or change logs. |

---

### 7.12 Requirement ID format and traceability keys

Requirements use hierarchical prefixes for mapping to tests and future design documents.

| Prefix | Meaning |
|--------|---------|
| **FR-7.3.\*** | Functional requirement (§7.3) |
| **NFR-7.4.\*** | Non-functional requirement (§7.4) |
| **TR-7.5.\*** | Technical requirement (§7.5) |
| **SR-7.6.\*** | Security / integrity (§7.6) |
| **TE-7.8.\*** | Testing evidence (§7.8) |
| **DOC-7.9.2-\*** | Documentation quality (§7.9.2) |
| **REV-7.11-\*** | Revision control (§7.11) |
| **CC-7.13-\*** | Change control (§7.13) |

#### 7.12.1 Hierarchical structure and numbering

Numbering SHALL follow **7** (Requirements) → **7.3** major functional block → **7.3.x** sub-area → **FR-7.3.x-yy** atomic IDs. Non-functional, technical, and security items follow **7.4**, **7.5**, **7.6** respectively. Sections **7.7–7.11** use descriptive subsection titles for roles, testing, documentation, risks, and revision control; **7.14–7.15** capture environmental assumptions and limits.

---

### 7.13 Freeze date and change-control requirements

| ID | Requirement |
|----|-------------|
| CC-7.13-01 | The team MAY designate a **requirements freeze date** for a milestone (e.g., midterm demo, final submission); after freeze, **new functional requirements** require change-control approval (course instructor / PM / team vote per local policy). |
| CC-7.13-02 | **Bug fixes** that restore intended behavior documented in §7.3–§7.6 are exempt from freeze but SHALL still be covered by tests when behavior is user-visible. |
| CC-7.13-03 | **LLM prompt** or **Together model** changes that alter grading or question style SHALL be recorded in commit messages or `docs/` notes so instructors can interpret score shifts across terms. |
| CC-7.13-04 | Database **migration** scripts or `init_db` behavior that affect production SQLite files SHALL be treated as **high-impact** changes requiring backup guidance in release notes. |

---

### 7.14 Assumptions

Assumptions state what RGEE **relies on to be true** without enforcing it in code.

1. **Browser support** — Users run a **modern browser** with JavaScript enabled for hint-json, loading overlays, and client timing; core form posts may still degrade partially without JS for some flows, but full UX is JS-assisted.
2. **Single-tenant deployment per database file** — Instructor dashboard visibility is **global per database**; course separation is achieved by operational separation (separate instances/DB files), not row-level tenancy in the app.
3. **LLM provider behavior** — Together.ai returns text that is usually parseable as JSON after repair; extreme model drift may still cause user-visible failures with friendly error pages.
4. **Student honesty on ID** — Student IDs are **not authenticated**; proctoring and identity are external processes.
5. **Clock sync** — Client timing values are self-reported wall deltas; they assume a reasonable local clock for UX studies, not forensic accuracy.
6. **Python runtime** — Operators provide **Python 3.11+** as stated in README for development and test parity.

---

### 7.15 Constraints

Constraints are **hard limits** imposed by technology, policy, or current implementation scope.

1. **SQLite scaling** — Default SQLite suits **low-to-moderate concurrency**; high concurrent write loads may still hit locks despite WAL and busy_timeout.
2. **LLM cost and rate limits** — Live mode is constrained by **Together.ai** account limits, network path, and model latency; mock mode avoids this but does not validate production grading quality.
3. **No built-in LMS integration** — RGEE does not ship LTI/Canvas-out-of-the-box; roster sync and grade push are out of scope unless added in future work.
4. **Instructor count** — Authentication supports a **single derived credential set** from file/env as implemented; multi-instructor RBAC is not present in code paths reviewed here.
5. **Grades are model-generated** — Final and per-question scores are **LLM outputs** constrained by prompts and rubric text; the app does not implement human regrade workflows.
6. **Exam length** — Planned question count is clamped to **1–20** at session start.
7. **Resume scope** — Resume only locates sessions with status **`in_progress`**; completed exams are viewed via results URLs, not resume.

---

*End of requirements document.*
