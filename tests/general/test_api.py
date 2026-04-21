"""HTTP tests for all routes (MOCK_LLM, isolated SQLite)."""
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_home(client: TestClient):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    assert "Start exam" in r.text
    assert "Resume exam" in r.text


def test_start_page_loads(client: TestClient):
    r = client.get("/start")
    assert r.status_code == 200
    assert b"education_level" in r.content or b"Education level" in r.content


def test_resume_page_loads(client: TestClient):
    r = client.get("/resume")
    assert r.status_code == 200
    assert "Resume your in-progress exam" in r.text


def test_resume_redirects_to_in_progress_exam(client: TestClient):
    r0 = client.post(
        "/exam/start",
        data={"student_id": "resume-me", "professor_domain": "Resume test domain.", "num_questions": "2"},
        follow_redirects=False,
    )
    assert r0.status_code == 303
    session_id = int(r0.headers["location"].split("/exam/")[1].split("/")[0])
    r = client.post("/resume", data={"student_id": "resume-me"}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == f"/exam/{session_id}/question"


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


def test_exam_start_rejects_invalid_education_level(client: TestClient):
    r = client.post(
        "/exam/start",
        data={
            "student_id": "x",
            "professor_domain": "y",
            "education_level": "not_a_real_level",
            "num_questions": "1",
        },
        follow_redirects=False,
    )
    assert r.status_code == 400
    assert "text/html" in r.headers.get("content-type", "")
    assert "problem with that request" in r.text.lower()


def test_exam_start_rejects_invalid_grading_strictness(client: TestClient):
    r = client.post(
        "/exam/start",
        data={
            "student_id": "x",
            "professor_domain": "y",
            "grading_strictness": "not_a_mode",
            "num_questions": "1",
        },
        follow_redirects=False,
    )
    assert r.status_code == 400
    assert "text/html" in r.headers.get("content-type", "")
    assert "problem with that request" in r.text.lower()


def test_insane_grading_strictness_mock_final_percent(client: TestClient):
    r0 = client.post(
        "/exam/start",
        data={
            "student_id": "insane-tester",
            "professor_domain": "Domain for insane strictness.",
            "grading_strictness": "insane",
            "num_questions": "1",
        },
        follow_redirects=False,
    )
    assert r0.status_code == 303
    session_id = int(r0.headers["location"].split("/exam/")[1].split("/")[0])
    client.post(
        f"/exam/{session_id}/answer",
        data={"answer": "Answer text.", "seconds_on_question": ""},
        follow_redirects=True,
    )
    res = client.get(f"/exam/{session_id}/results")
    assert res.status_code == 200
    assert "68.0%" in res.text


def test_full_exam_single_question_flow(client: TestClient):
    r0 = client.post(
        "/exam/start",
        data={
            "student_id": "s1",
            "professor_domain": "Domain text for testing.",
            "education_level": "high_school",
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
    assert "High school" in q.text

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
    assert "Rubric breakdown" in res.text
    assert "Reference answer guidance" in res.text
    assert "Strengths" in res.text
    assert "Areas for improvement" in res.text
    assert "Suggestions" in res.text
    assert "Overall final summary" in res.text
    assert "Points" in res.text


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
    q = client.get("/exam/99999/question")
    r = client.get("/exam/99999/results")
    assert q.status_code == 404
    assert r.status_code == 404
    assert "text/html" in q.headers.get("content-type", "")
    assert "we could not find that page" in q.text.lower()


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
    assert "Reference answer guidance" in det.text
    assert "Rubric breakdown" in det.text
    assert "Strengths" in det.text
    assert "Areas for improvement" in det.text
    assert "Suggestions" in det.text
    assert "Overall final summary" in det.text
    assert "Points" in det.text

    assert client.get("/professor/exam/99999").status_code == 404


def test_performance_log_page(client: TestClient):
    r = client.get("/performance-log")
    assert r.status_code == 200
    assert "Performance log" in r.text


def test_http_log_links_exam_start_to_session(client: TestClient):
    r0 = client.post(
        "/exam/start",
        data={
            "student_id": "assoc-test",
            "professor_domain": "Association test domain.",
            "num_questions": "1",
        },
        follow_redirects=False,
    )
    assert r0.status_code == 303
    session_id = int(r0.headers["location"].split("/exam/")[1].split("/")[0])

    log_page = client.get("/performance-log")
    assert log_page.status_code == 200
    assert f'href="/professor/exam/{session_id}"' in log_page.text
    assert "assoc-test" in log_page.text


def test_client_timing_records_and_returns_204(client: TestClient):
    r0 = client.post(
        "/exam/start",
        data={
            "student_id": "timing-student",
            "professor_domain": "Topic for timing test.",
            "num_questions": "1",
        },
        follow_redirects=False,
    )
    assert r0.status_code == 303
    session_id = int(r0.headers["location"].split("/exam/")[1].split("/")[0])

    r = client.post(
        f"/exam/{session_id}/client-timing",
        data={"client_ms_wall": "1234.5"},
    )
    assert r.status_code == 204

    log_page = client.get("/performance-log")
    assert log_page.status_code == 200
    assert "generate_click_to_first_question_visible" in log_page.text
    assert "1234.5" in log_page.text or "1234" in log_page.text
    assert "timing-student" in log_page.text


def test_client_timing_unknown_session_404(client: TestClient):
    r = client.post(
        "/exam/99999/client-timing",
        data={"client_ms_wall": "100"},
    )
    assert r.status_code == 404


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
        follow_redirects=False,
    )
    # Idempotent: duplicate submit after exam completed → redirect to results (not 400).
    assert r.status_code == 303
    assert r.headers["location"] == f"/exam/{session_id}/results"
