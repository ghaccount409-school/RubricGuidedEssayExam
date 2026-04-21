"""Grading strictness modes for per-session exam scoring (LLM + mock)."""

from typing import Any

DEFAULT_GRADING_STRICTNESS = "balanced"

ALLOWED_STRICTNESS_IDS: frozenset[str] = frozenset({"easy", "balanced", "strict", "insane"})

# UI + validation order
GRADING_STRICTNESS_OPTIONS: list[dict[str, Any]] = [
    {
        "id": "easy",
        "label": "Easy",
        "hint": "Generous scoring; credit partial understanding.",
    },
    {
        "id": "balanced",
        "label": "Balanced",
        "hint": "Fair, typical exam expectations.",
    },
    {
        "id": "strict",
        "label": "Strict",
        "hint": "High bar; gaps and vagueness cost more.",
    },
    {
        "id": "insane",
        "label": "Insane",
        "hint": "Maximum rigor; near-perfect answers only score very high.",
    },
]


def normalize_strictness(raw: str | None) -> str:
    key = (raw or "").strip().lower()
    return key if key in ALLOWED_STRICTNESS_IDS else DEFAULT_GRADING_STRICTNESS


def label_for_strictness(mode: str) -> str:
    for opt in GRADING_STRICTNESS_OPTIONS:
        if opt["id"] == normalize_strictness(mode):
            return str(opt["label"])
    return "Balanced"


def guidance_for_strictness(mode: str) -> str:
    """Instructions embedded in grading prompts for Together / mock."""
    m = normalize_strictness(mode)
    if m == "easy":
        return (
            "Use generous scoring. Reward good faith effort and partial understanding. "
            "When in doubt between two scores, choose the higher. Minor omissions or informal wording should not heavily penalize."
        )
    if m == "strict":
        return (
            "Use demanding scoring. Expect clear structure, precise use of concepts, and explicit ties to the rubric. "
            "Vague or under-supported claims should lower scores noticeably. Reserve top scores for answers that are thorough and well justified."
        )
    if m == "insane":
        return (
            "Use extremely rigorous scoring comparable to a very hard oral defense. "
            "Be skeptical of hand-waving; require tight logic, specificity, and coverage of rubric criteria. "
            "Top scores (90+) should be rare; mediocre answers should land in the middle or below."
        )
    # balanced
    return (
        "Use fair, typical exam grading. Align scores tightly to the rubric: solid answers earn solid scores, "
        "excellent answers earn high scores, and weak or off-topic answers earn low scores. Avoid both inflation and harshness."
    )


def mock_percent_for_strictness(mode: str) -> float:
    """Demo scores in mock mode so strictness is visible without a live API."""
    m = normalize_strictness(mode)
    if m == "easy":
        return 91.0
    if m == "strict":
        return 76.0
    if m == "insane":
        return 68.0
    return 84.0
