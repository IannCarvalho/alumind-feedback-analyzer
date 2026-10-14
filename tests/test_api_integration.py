"""Integration tests for the feedback API endpoint.

These exercise the full request -> analyze -> persist -> respond path against
an in-memory SQLite database. The LLM is mocked, so no network/API is used.
"""
from unittest.mock import patch


def test_post_feedback_persists_and_returns_analysis(client):
    fake_analysis = {
        "sentiment": "POSITIVO",
        "is_spam": False,
        "requested_features": [
            {"code": "EDITAR_PERFIL", "reason": "quer editar o perfil"}
        ],
    }
    body = {
        "id": "4042f20a-45f4-4647-8050-139ac16f610b",
        "feedback": "Gosto do app, so queria editar meu perfil.",
    }
    with patch(
        "app.routes.api.feedback_analyzer.analyze_feedback",
        return_value=fake_analysis,
    ):
        resp = client.post("/api/feedbacks", json=body)

    assert resp.status_code == 201
    data = resp.get_json()
    assert data["id"] == body["id"]
    assert data["sentiment"] == "POSITIVO"
    assert data["is_spam"] is False
    assert data["requested_features"][0]["code"] == "EDITAR_PERFIL"


def test_post_duplicate_id_returns_409(client):
    fake_analysis = {"sentiment": "POSITIVO", "is_spam": False, "requested_features": []}
    body = {
        "id": "4042f20a-45f4-4647-8050-139ac16f610b",
        "feedback": "primeiro envio",
    }
    with patch(
        "app.routes.api.feedback_analyzer.analyze_feedback",
        return_value=fake_analysis,
    ):
        first = client.post("/api/feedbacks", json=body)
        second = client.post("/api/feedbacks", json=body)

    assert first.status_code == 201
    assert second.status_code == 409


def test_post_missing_fields_returns_400(client):
    resp = client.post("/api/feedbacks", json={"id": "x"})
    assert resp.status_code == 400


def test_spam_is_persisted_but_hidden_from_listing(client, app):
    """Spam is stored (is_spam=True) but excluded from the recent-feedbacks view."""
    from app.services.feedback_service import FeedbackService

    fake_analysis = {"sentiment": "NEGATIVO", "is_spam": True, "requested_features": []}
    body = {
        "id": "11111111-1111-1111-1111-111111111111",
        "feedback": "compre agora http://spam.example",
    }
    with patch(
        "app.routes.api.feedback_analyzer.analyze_feedback",
        return_value=fake_analysis,
    ):
        resp = client.post("/api/feedbacks", json=body)

    assert resp.status_code == 201
    assert resp.get_json()["is_spam"] is True
    # Stored, but excluded from the non-spam recent listing.
    recent = FeedbackService.get_recent_feedbacks()
    assert all(not f.is_spam for f in recent)
    assert body["id"] not in [str(f.id) for f in recent]
