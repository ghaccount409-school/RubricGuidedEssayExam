"""Security-oriented checks: safe error responses (no tracebacks in HTML)."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.security


def test_not_found_exam_question_has_no_python_traceback(client: TestClient):
    r = client.get("/exam/99999/question")
    assert r.status_code == 404
    body = r.text.lower()
    assert "traceback" not in body
    assert 'file "/' not in body


def test_not_found_exam_results_has_no_python_traceback(client: TestClient):
    r = client.get("/exam/99999/results")
    assert r.status_code == 404
    assert "traceback" not in r.text.lower()


def test_exam_start_rejects_empty_student_id_without_traceback(client: TestClient):
    r = client.post(
        "/exam/start",
        data={
            "student_id": "   ",
            "professor_domain": "x",
            "num_questions": "1",
        },
    )
    assert r.status_code == 400
    assert "traceback" not in r.text.lower()


def test_professor_unknown_exam_is_404(client: TestClient):
    assert client.get("/professor/exam/99999").status_code == 404
