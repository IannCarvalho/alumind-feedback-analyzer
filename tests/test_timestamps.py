"""created_at sai sempre com fuso UTC explícito, em qualquer banco."""
from datetime import datetime, timedelta, timezone

from app.models.feedback import Feedback, as_utc


def test_as_utc_marks_naive_values_as_utc():
    naive = datetime(2026, 1, 2, 3, 4, 5)
    assert as_utc(naive) == datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


def test_as_utc_converts_other_offsets():
    brt = timezone(timedelta(hours=-3))
    aware = datetime(2026, 1, 2, 0, 4, 5, tzinfo=brt)
    assert as_utc(aware) == datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    assert as_utc(aware).utcoffset() == timedelta(0)


def test_to_dict_created_at_has_utc_offset(app):
    feedback = Feedback(feedback_text="oi", sentiment="POSITIVO",
                        created_at=datetime(2026, 1, 2, 3, 4, 5))
    assert feedback.to_dict()["created_at"] == "2026-01-02T03:04:05+00:00"
