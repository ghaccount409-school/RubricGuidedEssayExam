from app.main import _is_clearly_unrelated_exam_ask


def test_ai_helper_accepts_general_approach_prompt():
    ctx = "Explain fractions and compare numerator and denominator using examples."
    q = "tell me how to approach this question"
    assert _is_clearly_unrelated_exam_ask(q, ctx) is False


def test_ai_helper_marks_obviously_unrelated_prompt():
    ctx = "Explain fractions and compare numerator and denominator using examples."
    q = "what is the weather in tokyo this weekend"
    assert _is_clearly_unrelated_exam_ask(q, ctx) is True
