import json
import re
from typing import Any

import httpx

from app.config import get_settings
from app.prompts import FINAL_GRADE_TEMPLATE, GRADE_RESPONSE_TEMPLATE, QUESTION_GENERATION_TEMPLATE


def _strip_json_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()


def _parse_json_object(text: str) -> dict[str, Any]:
    raw = _strip_json_fence(text)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            return json.loads(m.group())
        raise


def _mock_question_payload(professor_domain: str, q_index: int) -> dict[str, Any]:
    return {
        "background_information": (
            f"[MOCK] Brief context for domain snippet: {professor_domain[:120]}..."
            if len(professor_domain) > 120
            else f"[MOCK] Brief context for: {professor_domain}"
        ),
        "essay_question": (
            f"[MOCK Question {q_index + 1}] Explain two main ideas from the domain guidance above "
            "and how they connect to fair assessment in asynchronous courses."
        ),
        "grading_rubric": [
            "Names at least two distinct ideas from the domain",
            "Explains the connection between those ideas clearly",
            "Discusses assessment or async context in a substantive way",
        ],
        "domain_notes": "Mock mode: no live LLM.",
    }


def _mock_grade_payload() -> dict[str, Any]:
    return {
        "highly_satisfactory": True,
        "dimension_scores": {"rubric_alignment": 85, "completeness": 80, "clarity": 88},
        "overall_percent": 84.0,
        "explanation": "[MOCK] Answer addresses rubric at a reasonable level; mock grader always passes.",
    }


def _mock_final_payload() -> dict[str, Any]:
    return {
        "total_grade_percent": 84.0,
        "explanation": "[MOCK] Average of mock per-question scores.",
        "weighting_notes": "Equal weight per question in mock.",
    }


def _chat_completion(messages: list[dict[str, str]]) -> str:
    s = get_settings()
    if s.mock_llm:
        raise RuntimeError("mock_llm should be handled before _chat_completion")
    if not s.together_api_key:
        raise ValueError(
            "TOGETHER_API_KEY is missing. Copy .env.example to .env and set your key, or set MOCK_LLM=1."
        )
    url = f"{s.together_base_url.rstrip('/')}/chat/completions"
    body = {
        "model": s.together_model,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 4096,
    }
    with httpx.Client(timeout=120.0) as client:
        r = client.post(
            url,
            headers={
                "Authorization": f"Bearer {s.together_api_key}",
                "Content-Type": "application/json",
            },
            json=body,
        )
        r.raise_for_status()
        data = r.json()
    return data["choices"][0]["message"]["content"] or ""


def generate_question(
    professor_domain: str,
    prior_questions_summary: str,
    question_index: int = 0,
) -> dict[str, Any]:
    if get_settings().mock_llm:
        return _mock_question_payload(professor_domain, question_index)

    prompt = QUESTION_GENERATION_TEMPLATE.format(
        professor_domain=professor_domain,
        prior_questions_summary=prior_questions_summary or "(none yet)",
    )
    content = _chat_completion(
        [
            {"role": "system", "content": "You output only valid JSON objects for exam software."},
            {"role": "user", "content": prompt},
        ]
    )
    return _parse_json_object(content)


def grade_answer(
    background_information: str,
    essay_question: str,
    grading_rubric: str,
    student_response: str,
    seconds_on_question: int | None,
) -> dict[str, Any]:
    if get_settings().mock_llm:
        return _mock_grade_payload()

    rubric_display = grading_rubric
    try:
        rubric_list = json.loads(grading_rubric)
        if isinstance(rubric_list, list):
            rubric_display = "\n".join(f"- {x}" for x in rubric_list)
    except json.JSONDecodeError:
        pass

    prompt = GRADE_RESPONSE_TEMPLATE.format(
        background_information=background_information,
        essay_question=essay_question,
        grading_rubric=rubric_display,
        student_response=student_response,
        seconds_on_question=seconds_on_question if seconds_on_question is not None else "not recorded",
    )
    content = _chat_completion(
        [
            {"role": "system", "content": "You are a fair, consistent exam grader. Output only valid JSON."},
            {"role": "user", "content": prompt},
        ]
    )
    return _parse_json_object(content)


def final_grade(per_question_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    if get_settings().mock_llm:
        return _mock_final_payload()

    blob = json.dumps(per_question_summaries, ensure_ascii=False, indent=2)
    prompt = FINAL_GRADE_TEMPLATE.format(per_question_summaries=blob)
    content = _chat_completion(
        [
            {
                "role": "system",
                "content": "You synthesize exam results into one overall grade. Output only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ]
    )
    return _parse_json_object(content)
