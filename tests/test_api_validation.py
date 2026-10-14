"""Tests for the API request validator (no database access).

Uses a bare Flask app with a request context so validate_feedback_request can
read the incoming JSON, without creating the real app (which starts a
scheduler and requires a DB engine).
"""
import pytest
from flask import Flask

from app.routes.api import validate_feedback_request


@pytest.fixture()
def ctx_app():
    return Flask(__name__)


def test_valid_request_returns_data(ctx_app):
    body = {"id": "4042f20a-45f4-4647-8050-139ac16f610b", "feedback": "oi"}
    with ctx_app.test_request_context(json=body):
        data = validate_feedback_request()
    assert data["id"] == body["id"]
    assert data["feedback"] == "oi"


def test_missing_feedback_field_raises(ctx_app):
    with ctx_app.test_request_context(json={"id": "x"}):
        with pytest.raises(ValueError):
            validate_feedback_request()


def test_missing_id_field_raises(ctx_app):
    with ctx_app.test_request_context(json={"feedback": "oi"}):
        with pytest.raises(ValueError):
            validate_feedback_request()


def test_non_json_body_raises(ctx_app):
    with ctx_app.test_request_context(data="not json", content_type="text/plain"):
        with pytest.raises(ValueError):
            validate_feedback_request()
