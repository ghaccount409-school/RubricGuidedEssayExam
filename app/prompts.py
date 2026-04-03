"""Prompt templates completed at runtime (spec: string manipulation → full prompt for Together.ai)."""

QUESTION_GENERATION_TEMPLATE = """You are an expert exam author. The professor has provided domain guidance below (not verbatim questions — use it to scope topic and difficulty).

PROFESSOR DOMAIN / CONSTRAINTS:
---
{professor_domain}
---

Prior questions already used in this session (avoid near-duplicates; empty if none):
---
{prior_questions_summary}
---

Respond with ONLY valid JSON (no markdown fences, no commentary). Use exactly these keys:
- "background_information": string, short reference sheet the student may read before answering
- "essay_question": string, one clear essay prompt tied to that background
- "grading_rubric": array of strings, each a criterion that should appear in a strong answer
- "domain_notes": string, optional notes on what a prepared student should know for this item

The JSON must be parseable by Python json.loads.
"""

GRADE_RESPONSE_TEMPLATE = """You grade one essay exam answer using the rubric and background provided.

BACKGROUND SHOWN TO STUDENT:
---
{background_information}
---

ESSAY QUESTION:
---
{essay_question}
---

GRADING RUBRIC (criteria for a strong answer):
---
{grading_rubric}
---

STUDENT RESPONSE:
---
{student_response}
---

TIME ON QUESTION (seconds, if provided): {seconds_on_question}

Respond with ONLY valid JSON (no markdown fences). Keys:
- "highly_satisfactory": boolean — true only if the answer substantially meets all rubric criteria
- "dimension_scores": object with numeric 0-100 keys e.g. "rubric_alignment", "completeness", "clarity"
- "overall_percent": number 0-100
- "explanation": string, detailed justification referencing the rubric and student text

The JSON must be parseable by Python json.loads.
"""

FINAL_GRADE_TEMPLATE = """You compile a fair overall exam grade from per-question summaries.

Each element is one question's grading outcome (JSON-like summaries):
---
{per_question_summaries}
---

Respond with ONLY valid JSON. Keys:
- "total_grade_percent": number 0-100 for the whole exam
- "explanation": string describing how you combined the parts and any weighting assumptions
- "weighting_notes": string, optional

The JSON must be parseable by Python json.loads.
"""
