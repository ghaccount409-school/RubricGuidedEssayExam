"""Fast unit tests: pure functions and small types (no HTTP, no DB logic)."""

import pytest

from app.education_levels import (
    ALLOWED_LEVEL_IDS,
    DEFAULT_EDUCATION_LEVEL_ID,
    EDUCATION_LEVELS,
    guidance_for_level,
    label_for_level,
)
from app.errors import TogetherApiError

pytestmark = pytest.mark.unit


def test_education_levels_ids_are_unique():
    ids = [e["id"] for e in EDUCATION_LEVELS]
    assert len(ids) == len(set(ids))


def test_label_for_level_known():
    assert label_for_level("high_school") == "High school (9–12)"


def test_label_for_level_unknown_returns_raw_id():
    assert label_for_level("custom_unknown") == "custom_unknown"


def test_guidance_for_level_known_contains_keywords():
    g = guidance_for_level("primary")
    assert "young" in g.lower() or "learner" in g.lower()


def test_guidance_for_level_unknown_falls_back_to_default():
    unknown = "not_a_registered_level"
    assert unknown not in ALLOWED_LEVEL_IDS
    fallback = guidance_for_level(unknown)
    default = guidance_for_level(DEFAULT_EDUCATION_LEVEL_ID)
    assert fallback == default


def test_allowed_level_ids_expected():
    assert {"primary", "middle", "high_school", "college", "graduate"}.issubset(
        ALLOWED_LEVEL_IDS
    )


def test_default_education_level_id_is_allowed():
    assert DEFAULT_EDUCATION_LEVEL_ID in ALLOWED_LEVEL_IDS


def test_together_api_error_message_and_http_status():
    err = TogetherApiError("bad key", http_status=401)
    assert err.message == "bad key"
    assert err.http_status == 401
    assert "bad key" in str(err)
