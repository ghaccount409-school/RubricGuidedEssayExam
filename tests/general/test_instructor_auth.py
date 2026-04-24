"""Instructor login verification (no raises on bad stored digests)."""

from pathlib import Path
from unittest.mock import patch

from app.config import Settings
from app.instructor_auth import (
    DEFAULT_PASSWORD_PBKDF2_HEX,
    DEFAULT_USERNAME_SHA256,
    PBKDF2_ITERATIONS,
    _load_expected_from_file,
    verify_instructor_login,
)


def test_verify_login_returns_false_when_stored_password_hex_wrong_length():
    """Mismatched digest lengths used to raise ValueError → global 500 page."""
    with patch("app.instructor_auth.expected_instructor_derivatives") as m:
        m.return_value = (
            DEFAULT_USERNAME_SHA256,
            "ab" * 15,  # 15 bytes; PBKDF2-SHA256 digest is 32 bytes
            210_000,
        )
        assert verify_instructor_login("elliott", "12345", Path("/tmp"), Settings()) is False


def test_load_expected_from_file_ignores_invalid_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{ not valid json", encoding="utf-8")
    assert _load_expected_from_file(bad) is None


def test_load_expected_from_file_clamps_zero_iterations(tmp_path):
    p = tmp_path / "ok.json"
    p.write_text(
        '{"version":1,"username_sha256":"' + DEFAULT_USERNAME_SHA256 + '",'
        '"password_pbkdf2_hex":"' + DEFAULT_PASSWORD_PBKDF2_HEX + '","pbkdf2_iterations":0}',
        encoding="utf-8",
    )
    u, pw, it = _load_expected_from_file(p)
    assert u == DEFAULT_USERNAME_SHA256
    assert pw == DEFAULT_PASSWORD_PBKDF2_HEX
    assert it == PBKDF2_ITERATIONS


def test_verify_login_returns_false_when_stored_username_hash_wrong_length():
    with patch("app.instructor_auth.expected_instructor_derivatives") as m:
        m.return_value = (
            "0f9c00",  # not 64 hex chars like real SHA-256 digest
            DEFAULT_PASSWORD_PBKDF2_HEX,
            210_000,
        )
        assert verify_instructor_login("elliott", "12345", Path("/tmp"), Settings()) is False
