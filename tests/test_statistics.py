"""Tests for the pure statistics calculations (no database access)."""
from app.services.statistics_service import Statistics


def test_percentages_sum_and_values():
    counts = {"POSITIVO": 6, "NEGATIVO": 3, "INCONCLUSIVO": 1}
    pct = Statistics.get_sentiment_percentages(10, counts)
    assert pct["POSITIVO"] == 60.0
    assert pct["NEGATIVO"] == 30.0
    assert pct["INCONCLUSIVO"] == 10.0
    assert round(sum(pct.values())) == 100


def test_percentages_zero_total_returns_zeros():
    counts = {"POSITIVO": 0, "NEGATIVO": 0, "INCONCLUSIVO": 0}
    pct = Statistics.get_sentiment_percentages(0, counts)
    assert pct == {"POSITIVO": 0.0, "NEGATIVO": 0.0, "INCONCLUSIVO": 0.0}
