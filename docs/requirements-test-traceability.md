# Requirements-to-Tests Traceability

**RubricGuidedEssayExam** — mapping the software requirements specification (SRS v1.1, local document `requirements-specification-csc394-capstone.md`) to automated tests in this repository.

**Repository:** [https://github.com/ALGeek01/RubricGuidedEssayExam](https://github.com/ALGeek01/RubricGuidedEssayExam)  
**Tests root:** [https://github.com/ALGeek01/RubricGuidedEssayExam/tree/main/tests](https://github.com/ALGeek01/RubricGuidedEssayExam/tree/main/tests)  
**Document version:** 1.0  
**Date:** 2026-04-07  

---

## 1. Purpose

This document records which **functional** and **non-functional** requirements from the capstone SRS are exercised by the current pytest suite, and which requirements have **no automated test** yet. The application implements a **subset** of the full SRS; many requirements are **forward-looking** or **not yet implemented**.

**Test environment note:** `tests/conftest.py` sets `MOCK_LLM=1` and uses an isolated SQLite database. Integration tests do **not** call the live Together API.

---

## 2. Test inventory

| File | Role |
|------|------|
| `tests/conftest.py` | Isolated SQLite (`DATABASE_URL`), `MOCK_LLM=1`, `TestClient` fixture, DB reset per test. |
| `tests/general/test_unit.py` | Pure unit tests (`pytest.mark.unit`). |
| `tests/general/test_api.py` | HTTP / user-flow tests (`pytest.mark.integration`). |
| `tests/security/test_http.py` | Security-oriented HTTP checks (`pytest.mark.security`). |

---

## 3. Unit tests (`test_unit.py`) and SRS

These tests primarily validate **education level** catalog helpers and **`TogetherApiError`**. They are **not** explicitly numbered in the SRS unless you add a requirement for audience/difficulty level.

| Test | Description | Closest SRS hook |
|------|-------------|------------------|
| `test_education_levels_ids_are_unique` | Level IDs are unique. | Optional future FR for education/audience level. |
| `test_label_for_level_known` | Known level labels. | Same as above. |
| `test_label_for_level_unknown_returns_raw_id` | Unknown id passthrough. | Same as above. |
| `test_guidance_for_level_known_contains_keywords` | Guidance text for primary. | Same as above. |
| `test_guidance_for_level_unknown_falls_back_to_default` | Fallback to default level. | Same as above. |
| `test_allowed_level_ids_expected` | Expected ids subset. | Same as above. |
| `test_default_education_level_id_is_allowed` | Default is valid. | Same as above. |
| `test_together_api_error_message_and_http_status` | Exception carries message and HTTP status. | Supports **FR-GEN-3**-style error handling if wired to retries/UI (not integration-tested). |

---

## 4. SRS requirement → integration / security tests

| Requirement | Test(s) | Coverage note |
|-------------|---------|----------------|
| **§2.0** — Essay generation & evaluation | `test_full_exam_single_question_flow`, `test_two_question_flow` | End-to-end with **mock LLM**; does not prove real-time Together behavior. |
| **§2.0.1 / FR-GEN-1** — LLM returns Python, exec, validate | — | **Not covered** (mock bypasses prompt/exec/sandbox). |
| **FR-PROF-1** — Exam configuration | `test_exam_start_redirects_and_creates_session`, `test_full_exam_single_question_flow`, `test_two_question_flow`, `test_exam_start_rejects_invalid_education_level` | Only **student_id**, **professor_domain**, **num_questions**, **education_level** via form—not full config (weights, time limits, uploads, etc.). |
| **FR-PROF-2** — Domain constraint fields | — | **Not covered** |
| **FR-PROF-3** — Time accommodations | — | **Not covered** |
| **FR-PROF-4** — Question variation | — | **Not covered** |
| **FR-GEN-2** — Required generated fields | — | **Not asserted** (mock content not validated against schema). |
| **FR-GEN-3** — Retry / backoff | — | **Not covered** |
| **FR-GEN-4** — Generation latency | — | **Not covered** |
| **FR-STU-1** — Session integrity | `test_exam_start_redirects_and_creates_session`, `test_completed_session_question_redirects_to_results`, `test_answer_invalid_session` | Session creation; completed session redirects; **rejects second POST** to `/answer` with **400**. Does not cover token auth or every close state in the SRS. |
| **FR-STU-2** — Presentation order | — | **Not explicitly tested** |
| **FR-STU-3** — Answer capture (length, UTF-8) | `test_full_exam_single_question_flow`, `test_two_question_flow` | Short answers only; **no 20,000-character or boundary tests**. |
| **FR-STU-4** — Autosave | — | **Not covered** |
| **FR-STU-5** — Timers | — | **Not covered** |
| **FR-GRADE-1 / FR-GRADE-2** — Grading payload / structured result | `test_full_exam_single_question_flow` | Weak: expects **200** on results and **“84”** or **“grade”** in body under mock—**not schema validation**. |
| **FR-GRADE-3** — `needs_human_review` | — | **Not covered** |
| **FR-FU-1 / FR-FU-2 / FR-FU-3** — Follow-ups, State P | — | **Not covered** |
| **FR-DB-1 / FR-DB-2** — Persistence & retention | *(implicit)* flows using DB | Data persists in tests; **no** explicit constraint, idempotence, or retention/purge tests. |
| **FR-FINAL-1 / FR-FINAL-2 / FR-FINAL-3** — Final aggregation / synthesis / schemes | `test_two_question_flow` | **Partial**: two questions → results; **no** `exam_final_v1` or **S1/S2** scheme tests. |
| **FR-DISP-1 / FR-DISP-2 / FR-DISP-3** — Results, disputes | `test_full_exam_single_question_flow` (results page) | **Minimal** student results; **no** dispute flow. |
| **FR-REVIEW-1** — Session browser | `test_professor_dashboard_and_detail` | Dashboard **200**; **no** filter or p95 query assertions. |
| **FR-REVIEW-2** — Full artifact view | `test_professor_dashboard_and_detail` | **Weak**: detail page loads; **no** rubric/prompt/audit field checks. |
| **FR-REVIEW-3** — Export | — | **Not covered** |
| **FR-SEC-1** — Sandboxed LLM Python | — | **Not covered** |
| **FR-SEC-2** — Authentication | — | **Not covered** (professor routes unauthenticated in tests). |
| **G-1** — Question variation metric | — | **Not covered** |
| **NFR-PERF-1** — LCP | — | **Not covered** |
| **NFR-REL-1** — API availability | — | **Not covered** |
| **NFR-AUDIT-1** — Audit events | — | **Not covered** |
| **NFR-LOG-1** — Logging / secrets | `test_not_found_exam_question_has_no_python_traceback`, `test_not_found_exam_results_has_no_python_traceback`, `test_exam_start_rejects_empty_student_id_without_traceback` | **Partial**: HTML error responses omit tracebacks; **not** full logging or secret policy. |
| **NFR-ACC-1** — WCAG | — | **Not covered** |
| **NFR-I18N-1** — Externalized strings | — | **Not covered** |
| **NFR-DOC-1** — Operator documentation | — | **Not covered** |
| **ADV-CURVE-1 / ADV-DISC-1** | — | **Not covered** |
| **App-specific: invalid education level** | `test_exam_start_rejects_invalid_education_level` | **400** for bogus `education_level`. |
| **404 / error handling** | `test_exam_not_found`, `test_professor_unknown_exam_is_404` | Missing session and professor detail return **404**. |

---

## 5. Security tests (`test_http.py`)

| Test | Requirement / theme |
|------|---------------------|
| `test_not_found_exam_question_has_no_python_traceback` | Safe error responses (**NFR-LOG-1** partial); no traceback leakage. |
| `test_not_found_exam_results_has_no_python_traceback` | Same. |
| `test_exam_start_rejects_empty_student_id_without_traceback` | Input validation + no traceback (**400**). |
| `test_professor_unknown_exam_is_404` | Aligns with professor review **404** behavior. |

---

## 6. Summary

**Well covered (relative to current app scope):** exam start → question → answer → results; two-question flow; **404** for missing resources; professor dashboard/detail smoke tests; **no Python traceback** in selected error HTML; **reject duplicate** answer POST after completion; invalid **education level** and blank **student_id** rejection.

**Major gaps vs full SRS:** **FR-GEN-1** (exec/sandbox), **FR-SEC-1/2**, **FR-STU-3** boundaries, **FR-STU-4/5**, **FR-GRADE-2** schema validation, **FR-FU***, **FR-DB** explicit tests, **FR-FINAL-2/3**, **FR-DISP-2/3**, **FR-REVIEW-3**, and **most NFRs**.

---

## 7. Regenerating Office outputs

**No extra packages (stdlib only)** — from the repository root:

```bash
python docs/generate_traceability_office_stdlib.py
```

This writes `requirements-test-traceability.docx` and `requirements-test-traceability.pptx` in this folder using only the Python standard library.

**Optional (richer Office formatting)** — with `python-docx` and `python-pptx` installed:

```bash
pip install python-docx python-pptx
python docs/generate_traceability_office.py
```

Committed copies of the Word and PowerPoint files are kept in `docs/` for convenience; re-run either script after editing the traceability content.

**Per-requirement explanations** in the Word export are defined in **`docs/traceability_data.py`** (fourth column of each main row, plus the unit-test table). Edit that file, then regenerate the `.docx`. If Word has the file open, the stdlib script writes **`requirements-test-traceability (generated).docx`** instead.
