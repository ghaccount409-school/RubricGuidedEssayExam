"""HTTP tests for all routes (MOCK_LLM, isolated SQLite)."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_home(client: TestClient):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


def test_static_css(client: TestClient):
    r = client.get("/static/style.css")
    assert r.status_code == 200


def test_exam_start_redirects_and_creates_session(client: TestClient):
    r = client.post(
        "/exam/start",
        data={
            "student_id": "test-student-1",
            "professor_domain": "Fair grading in CS courses.",
            "num_questions": "1",
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"].startswith("/exam/")
    assert "/question" in r.headers["location"]


def test_exam_start_rejects_empty_student_id(client: TestClient):
    r = client.post(
        "/exam/start",
        data={
            "student_id": "   ",
            "professor_domain": "x",
            "num_questions": "1",
        },
    )
    assert r.status_code == 400


def test_full_exam_single_question_flow(client: TestClient):
    r0 = client.post(
        "/exam/start",
        data={
            "student_id": "s1",
            "professor_domain": "Domain text for testing.",
            "num_questions": "1",
        },
        follow_redirects=False,
    )
    assert r0.status_code == 303
    loc = r0.headers["location"]
    session_id = int(loc.split("/exam/")[1].split("/")[0])

    q = client.get(f"/exam/{session_id}/question")
    assert q.status_code == 200
    assert b"MOCK" in q.content or b"essay" in q.content.lower()

    r1 = client.post(
        f"/exam/{session_id}/answer",
        data={"answer": "A complete answer for testing.", "seconds_on_question": "120"},
        follow_redirects=False,
    )
    assert r1.status_code == 303
    assert r1.headers["location"] == f"/exam/{session_id}/results"

    res = client.get(f"/exam/{session_id}/results")
    assert res.status_code == 200
    assert b"84" in res.content or b"grade" in res.content.lower()


def test_two_question_flow(client: TestClient):
    r0 = client.post(
        "/exam/start",
        data={
            "student_id": "s2",
            "professor_domain": "Multi-q domain.",
            "num_questions": "2",
        },
        follow_redirects=False,
    )
    assert r0.status_code == 303
    loc = r0.headers["location"]
    session_id = int(loc.split("/exam/")[1].split("/")[0])

    r1 = client.post(
        f"/exam/{session_id}/answer",
        data={"answer": "Answer one.", "seconds_on_question": ""},
        follow_redirects=False,
    )
    assert r1.status_code == 303
    assert "/question" in r1.headers["location"]

    r2 = client.post(
        f"/exam/{session_id}/answer",
        data={"answer": "Answer two.", "seconds_on_question": "60"},
        follow_redirects=False,
    )
    assert r2.status_code == 303
    assert r2.headers["location"] == f"/exam/{session_id}/results"

    res = client.get(f"/exam/{session_id}/results")
    assert res.status_code == 200


def test_completed_session_question_redirects_to_results(client: TestClient):
    r0 = client.post(
        "/exam/start",
        data={"student_id": "s4", "professor_domain": "x", "num_questions": "1"},
        follow_redirects=False,
    )
    session_id = int(r0.headers["location"].split("/exam/")[1].split("/")[0])
    client.post(
        f"/exam/{session_id}/answer",
        data={"answer": "done", "seconds_on_question": ""},
        follow_redirects=True,
    )
    r = client.get(f"/exam/{session_id}/question", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == f"/exam/{session_id}/results"


def test_exam_not_found(client: TestClient):
    assert client.get("/exam/99999/question").status_code == 404
    assert client.get("/exam/99999/results").status_code == 404


def test_professor_dashboard_and_detail(client: TestClient):
    r0 = client.post(
        "/exam/start",
        data={"student_id": "prof-test", "professor_domain": "y", "num_questions": "1"},
        follow_redirects=False,
    )
    session_id = int(r0.headers["location"].split("/exam/")[1].split("/")[0])
    client.post(
        f"/exam/{session_id}/answer",
        data={"answer": "final", "seconds_on_question": ""},
        follow_redirects=True,
    )

    dash = client.get("/professor")
    assert dash.status_code == 200
    assert b"prof-test" in dash.content or b"prof" in dash.content.lower()

    det = client.get(f"/professor/exam/{session_id}")
    assert det.status_code == 200

    assert client.get("/professor/exam/99999").status_code == 404


def test_answer_invalid_session(client: TestClient):
    r0 = client.post(
        "/exam/start",
        data={"student_id": "s5", "professor_domain": "z", "num_questions": "1"},
        follow_redirects=False,
    )
    session_id = int(r0.headers["location"].split("/exam/")[1].split("/")[0])
    client.post(
        f"/exam/{session_id}/answer",
        data={"answer": "x", "seconds_on_question": ""},
        follow_redirects=True,
    )
    r = client.post(
        f"/exam/{session_id}/answer",
        data={"answer": "again", "seconds_on_question": ""},
    )
    assert r.status_code == 400
