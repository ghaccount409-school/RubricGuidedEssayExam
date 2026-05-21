"""
Shared rows for requirements → tests traceability documents.
Each row: (requirement label, test(s), coverage note, explanation for SRS readers).
"""
from __future__ import annotations

ROWS_MAIN: list[tuple[str, str, str, str]] = [
    (
        "§2.0 Essay gen & eval",
        "test_full_exam_single_question_flow; test_two_question_flow",
        "Mock LLM E2E; not live Together",
        "Core product intent: the system must generate essay-style questions at runtime (not only from a fixed bank) and evaluate students’ essay answers using the LLM-assisted pipeline. Together these behaviors prove the “oral-style exam in software” goal.",
    ),
    (
        "§2.0.1 / FR-GEN-1",
        "—",
        "Not covered",
        "Architecture requirement: English prompt templates in Python are filled at runtime and sent to the LLM; the model returns Python source that assigns a structured object to a named variable; the host executes that code only under sandbox or restricted-exec rules, then validates against schema exam_gen_v1. Tests do not exercise this path when MOCK_LLM is on.",
    ),
    (
        "FR-PROF-1",
        "test_exam_start_*; test_full_exam_*; test_two_question_flow",
        "Partial: form fields only",
        "Professors must be able to define and persist an exam configuration: scope/title, number of questions, time limits, domain briefing text, optional reference material, rubric style, and per-question weights summing to 1. The app currently exposes a subset via the start form (e.g., student id, domain text, count, education level).",
    ),
    (
        "FR-PROF-2 — FR-PROF-4",
        "—",
        "Not covered",
        "FR-PROF-2: at least three independent constraint fields per question slot passed into generation. FR-PROF-3: accommodation multipliers (1.0×–3.0×) on per-question and whole-exam time limits. FR-PROF-4: vary_questions flag so prompts discourage repeating recent questions for the same config.",
    ),
    (
        "FR-GEN-2 — FR-GEN-4",
        "—",
        "Not covered",
        "FR-GEN-2: each generated item must include background sheet, essay question, rubric (≥3 criteria with points), expected concepts, and metadata. FR-GEN-3: on validation or API failure, retry up to three times with backoff. FR-GEN-4: p95 generation time ≤45 s under nominal staging conditions.",
    ),
    (
        "FR-STU-1",
        "test_exam_start_*; test_completed_session_*; test_answer_invalid_session",
        "Session + duplicate answer 400",
        "Each exam session is bound to one student and one exam configuration. After the session is finished, closed, expired, or finally submitted, the system must not accept further answers. Tests cover creation, redirect after completion, and rejecting a second answer POST with HTTP 400.",
    ),
    (
        "FR-STU-2",
        "—",
        "Not explicitly tested",
        "Questions are shown in professor-defined order or in a randomized order chosen at session start and kept stable across refresh and reconnect for that session.",
    ),
    (
        "FR-STU-3",
        "test_full_exam_*; test_two_question_flow",
        "Short answers only",
        "Students submit essay answers as UTF-8 text with a maximum length (SRS: 20,000 characters) enforced on client and server. Current tests use short strings only; boundary and encoding tests are still needed.",
    ),
    (
        "FR-STU-4 — FR-STU-5",
        "—",
        "Not covered",
        "FR-STU-4: autosave drafts on a timed and debounced schedule so work is not lost. FR-STU-5: optional per-question and whole-exam timers with server-authoritative expiry (±5 s) and visible countdown where applicable.",
    ),
    (
        "FR-GRADE-1 / FR-GRADE-2",
        "test_full_exam_single_question_flow",
        "Weak; no schema validation",
        "FR-GRADE-1: the grading prompt must include question, rubric, background, student answer, optional time-on-question, and weighting preset. FR-GRADE-2: the LLM returns a graded structure (exam_grade_v1) via the same execute-and-validate pattern as generation, including scores, satisfactory flag, explanation, and confidence.",
    ),
    (
        "FR-GRADE-3",
        "—",
        "Not covered",
        "If grading fails after retries, the item is marked needs_human_review and no numeric final is stored until a professor resolves it.",
    ),
    (
        "FR-FU-*",
        "—",
        "Not covered",
        "When an answer is not satisfactory and follow-ups are enabled, the LLM may issue follow-up questions and rubrics (up to a max count), then produce a final grade using the initial answer and all follow-up responses. State P is the persisted terminal bundle for that question.",
    ),
    (
        "FR-DB-1 / FR-DB-2",
        "(implicit)",
        "No constraint/retention tests",
        "FR-DB-1: store each finalized question under a unique key (student, session, question index) with indexes for session lookup. FR-DB-2: configurable retention window and automated purge of expired records.",
    ),
    (
        "FR-FINAL-*",
        "test_two_question_flow",
        "Partial only",
        "When all questions are resolved, aggregate summaries per question and call the LLM for a final percentage and narrative (exam_final_v1). Support at least two professor-selectable schemes (e.g., pure weighted average vs. LLM-adjusted composite). Tests only assert a multi-question path reaches results.",
    ),
    (
        "FR-DISP-*",
        "test_full_exam_* (results)",
        "No disputes",
        "FR-DISP-1: after finalization, show the student final percentage, per-question scores, and short explanations. FR-DISP-2/3: optional dispute submission after a cooling-off window and LLM triage with professor-controlled auto-regrade.",
    ),
    (
        "FR-REVIEW-1 / FR-REVIEW-2",
        "test_professor_dashboard_and_detail",
        "Smoke only",
        "FR-REVIEW-1: professors filter and list sessions with acceptable query performance on a reference dataset. FR-REVIEW-2: one consolidated view of prompts (redacted secrets), rubrics, backgrounds, student answers, model outputs, timings, and aggregates.",
    ),
    (
        "FR-REVIEW-3",
        "—",
        "Not covered",
        "Export a session for archival or accreditation, at minimum as schema-valid JSON (PDF optional).",
    ),
    (
        "FR-SEC-1 / FR-SEC-2",
        "—",
        "Not covered",
        "FR-SEC-1: LLM-generated Python must run only in a sandbox or restricted namespace with resource limits. FR-SEC-2: authenticate professor routes; bind student routes to session tokens tied to student and exam config with bounded lifetime.",
    ),
    (
        "G-1",
        "—",
        "Not covered",
        "Measurable variation goal: when vary_questions is enabled, at least 90% of questions are not byte-identical to another student’s in the same configuration within the prior seven days (stochastic acceptance criteria in SRS).",
    ),
    (
        "NFR-PERF-1; NFR-REL-1; NFR-AUDIT-1",
        "—",
        "Not covered",
        "NFR-PERF-1: student UI performance (e.g., LCP ≤2.5 s under a reference network profile). NFR-REL-1: core API availability (e.g., ≥99.5% over pilot). NFR-AUDIT-1: append-only audit events with correlation IDs and high durability on commit.",
    ),
    (
        "NFR-LOG-1 (partial)",
        "test_*traceback*; test_exam_start_rejects_empty*",
        "No traceback in HTML",
        "Operational logging must omit API secrets; logging full student answers is off by default. Security tests check that common error pages do not embed Python tracebacks or host file paths in HTML.",
    ),
    (
        "NFR-ACC-1; NFR-I18N-1; NFR-DOC-1",
        "—",
        "Not covered",
        "NFR-ACC-1: WCAG 2.1 AA on primary student flows with automated axe checks. NFR-I18N-1: externalize UI strings (en-US in v1). NFR-DOC-1: operator runbook for deploy, env vars, backup, and incidents within a page budget.",
    ),
    (
        "ADV-CURVE-1; ADV-DISC-1",
        "—",
        "Not covered",
        "Optional advanced features: cohort-based curved grading with minimum sample size and visible fallbacks; or discussion-based testing with bounded transcript length and token budget passed into each grading call.",
    ),
]

ROWS_UNIT: list[tuple[str, str, str]] = [
    (
        "test_education_levels_ids_are_unique",
        "Optional SRS: education/audience level",
        "Catalog tests: each education level has a unique id so the UI and prompts cannot reference ambiguous tiers.",
    ),
    (
        "test_label_for_level_*",
        "Optional SRS",
        "Human-readable labels (e.g., “High school (9–12)”) display correctly for known ids and degrade gracefully for unknown ids.",
    ),
    (
        "test_guidance_for_level_*",
        "Optional SRS",
        "Prompt guidance text matches the selected difficulty/audience; unknown levels fall back to the default level’s guidance so generation still behaves predictably.",
    ),
    (
        "test_together_api_error_message_and_http_status",
        "Supports FR-GEN-3 if wired to retries",
        "TogetherApiError carries a message and HTTP status so higher layers can map provider failures to retries or user-visible errors without losing context.",
    ),
]
