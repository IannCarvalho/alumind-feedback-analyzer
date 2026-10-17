"""Orçamento de queries da listagem e do dashboard.

Antes, listar 20 feedbacks custava 22 queries (COUNT + página + 1 SELECT de
features por item) e o dashboard contava o total duas vezes. Estes testes
travam o número de queries para não voltar a crescer com o tamanho da página.
"""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import event

from app import db
from app.models.feedback import Feedback, RequestedFeature
from app.services.statistics_service import Statistics


@contextmanager
def count_queries():
    statements = []

    def _record(conn, cursor, statement, *args):
        statements.append(statement)

    event.listen(db.engine, "before_cursor_execute", _record)
    try:
        yield statements
    finally:
        event.remove(db.engine, "before_cursor_execute", _record)


def _seed(total=20, features_per_item=2, spam=0, null_sentiment=0):
    now = datetime.now(timezone.utc)
    sentiments = ["POSITIVO", "NEGATIVO", "INCONCLUSIVO"]
    for i in range(total + spam + null_sentiment):
        is_spam = i >= total and i < total + spam
        sentiment = None if i >= total + spam else sentiments[i % 3]
        feedback = Feedback(
            feedback_text=f"feedback {i}",
            sentiment=sentiment,
            is_spam=is_spam,
            created_at=now - timedelta(minutes=i),
        )
        for j in range(features_per_item):
            feedback.requested_features.append(
                RequestedFeature(code=f"FEATURE_{j}", reason=f"motivo {i}-{j}"))
        db.session.add(feedback)
    db.session.commit()
    db.session.expunge_all()


def test_api_listing_query_count_does_not_grow_with_page_size(client):
    _seed(total=20)
    with count_queries() as statements:
        resp = client.get("/api/feedbacks?per_page=20")
    assert resp.status_code == 200
    items = resp.get_json()["items"]
    assert len(items) == 20
    assert all(len(item["requested_features"]) == 2 for item in items)
    # COUNT da paginação + página + features da página inteira (selectin).
    assert len(statements) <= 3


def test_dashboard_statistics_use_two_queries(app):
    _seed(total=9, spam=2)
    with count_queries() as statements:
        stats = Statistics.get_dashboard_statistics()
    assert len(statements) == 2
    assert stats["total_feedbacks"] == 9
    assert stats["sentiment_counts"] == {"POSITIVO": 3, "NEGATIVO": 3, "INCONCLUSIVO": 3}
    assert stats["sentiment_percentages"]["POSITIVO"] == pytest.approx(100 / 3)
    assert stats["top_features"][0]["count"] == 9
    assert stats["top_features"][0]["percentage"] == pytest.approx(100.0)


def test_dashboard_total_matches_plain_count_even_with_null_sentiment(app):
    """A soma do GROUP BY precisa bater com o COUNT(*) que o total usava."""
    _seed(total=6, null_sentiment=2)
    stats = Statistics.get_dashboard_statistics()
    assert stats["total_feedbacks"] == Statistics.get_total_feedbacks() == 8


def test_dashboard_without_data(app):
    assert Statistics.get_dashboard_statistics() == {"has_data": False}
