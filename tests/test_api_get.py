"""Integration tests for the GET feedback endpoints.

Full request -> persist -> read-back path against in-memory SQLite, LLM mocked.
"""
from unittest.mock import patch


def _post(client, feedback_id, text, analysis):
    with patch(
        "app.routes.api.feedback_analyzer.analyze_feedback",
        return_value=analysis,
    ):
        return client.post("/api/feedbacks", json={"id": feedback_id, "feedback": text})


POSITIVE = {"sentiment": "POSITIVO", "is_spam": False, "requested_features": []}
NEGATIVE = {"sentiment": "NEGATIVO", "is_spam": False, "requested_features": []}
SPAM = {"sentiment": "NEGATIVO", "is_spam": True, "requested_features": []}


def test_list_empty_returns_pagination_metadata(client):
    resp = client.get("/api/feedbacks")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["items"] == []
    assert data["pagination"]["total"] == 0
    assert data["pagination"]["page"] == 1


def test_list_returns_persisted_feedbacks(client):
    _post(client, "11111111-1111-1111-1111-111111111111", "otimo", POSITIVE)
    _post(client, "22222222-2222-2222-2222-222222222222", "ruim", NEGATIVE)

    resp = client.get("/api/feedbacks")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["pagination"]["total"] == 2
    assert {item["id"] for item in data["items"]} == {
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
    }


def test_list_excludes_spam(client):
    _post(client, "11111111-1111-1111-1111-111111111111", "otimo", POSITIVE)
    _post(client, "33333333-3333-3333-3333-333333333333", "spam", SPAM)

    data = client.get("/api/feedbacks").get_json()
    ids = {item["id"] for item in data["items"]}
    assert "33333333-3333-3333-3333-333333333333" not in ids
    assert data["pagination"]["total"] == 1


def test_list_filters_by_sentiment(client):
    _post(client, "11111111-1111-1111-1111-111111111111", "otimo", POSITIVE)
    _post(client, "22222222-2222-2222-2222-222222222222", "ruim", NEGATIVE)

    data = client.get("/api/feedbacks?sentiment=NEGATIVO").get_json()
    assert data["pagination"]["total"] == 1
    assert data["items"][0]["id"] == "22222222-2222-2222-2222-222222222222"


def test_list_rejects_non_integer_page(client):
    resp = client.get("/api/feedbacks?page=abc")
    assert resp.status_code == 400


def test_list_rejects_non_positive_page(client):
    resp = client.get("/api/feedbacks?page=0")
    assert resp.status_code == 400


def test_get_by_id_returns_feedback(client):
    fid = "11111111-1111-1111-1111-111111111111"
    _post(client, fid, "otimo app", POSITIVE)

    resp = client.get(f"/api/feedbacks/{fid}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["id"] == fid
    assert data["feedback"] == "otimo app"
    assert data["sentiment"] == "POSITIVO"


def test_get_by_id_unknown_returns_404(client):
    resp = client.get("/api/feedbacks/44444444-4444-4444-4444-444444444444")
    assert resp.status_code == 404


def test_get_by_id_malformed_returns_400(client):
    resp = client.get("/api/feedbacks/not-a-uuid")
    assert resp.status_code == 400
