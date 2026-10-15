"""Tests for FeedbackAnalyzer JSON parsing and fallback behaviour.

The LLM call is mocked, so these tests make no network request.
"""
import json
from unittest.mock import MagicMock, patch

from app.services.feedback_analyzer import FeedbackAnalyzer


def _run_with_response(content: str):
    """Run analyze_feedback with the LLM chain mocked to return `content`."""
    analyzer = FeedbackAnalyzer()
    analyzer.llm = MagicMock()
    fake_message = MagicMock()
    fake_message.content = content
    with patch(
        "app.services.feedback_analyzer.ChatPromptTemplate"
    ) as mock_prompt:
        chain = MagicMock()
        chain.invoke.return_value = fake_message
        mock_prompt.from_template.return_value.__or__.return_value = chain
        return analyzer.analyze_feedback("texto de feedback")


def test_parses_clean_json():
    payload = {
        "sentiment": "POSITIVO",
        "is_spam": False,
        "requested_features": [
            {"code": "EDITAR_PERFIL", "reason": "quer editar o perfil"}
        ],
    }
    result = _run_with_response(json.dumps(payload))
    assert result["sentiment"] == "POSITIVO"
    assert result["is_spam"] is False
    assert result["requested_features"][0]["code"] == "EDITAR_PERFIL"


def test_extracts_json_embedded_in_prose():
    content = (
        "Claro! Aqui esta a analise:\n"
        '{"sentiment": "NEGATIVO", "is_spam": false, "requested_features": []}\n'
        "Espero ter ajudado."
    )
    result = _run_with_response(content)
    assert result["sentiment"] == "NEGATIVO"
    assert result["is_spam"] is False
    assert result["requested_features"] == []


def test_malformed_response_falls_back_to_inconclusivo():
    result = _run_with_response("isto nao e json")
    # Fallback uses the canonical Portuguese value, consistent with the rest
    # of the system (not the old 'INCONCLUSIVE').
    assert result["sentiment"] == "INCONCLUSIVO"
    assert result["is_spam"] is False
    assert result["requested_features"] == []


def test_missing_keys_are_filled_with_defaults():
    result = _run_with_response('{"sentiment": "POSITIVO"}')
    assert result["sentiment"] == "POSITIVO"
    assert result["is_spam"] is False
    assert result["requested_features"] == []


def test_unknown_sentiment_is_normalised_to_inconclusivo():
    # An out-of-vocabulary sentiment must be coerced, not passed through.
    result = _run_with_response('{"sentiment": "FELIZ", "is_spam": false}')
    assert result["sentiment"] == "INCONCLUSIVO"


def test_lowercase_sentiment_is_upcased():
    result = _run_with_response('{"sentiment": "negativo"}')
    assert result["sentiment"] == "NEGATIVO"


def test_feature_without_reason_defaults_to_empty_string():
    content = '{"sentiment": "POSITIVO", "requested_features": [{"code": "DARK_MODE"}]}'
    result = _run_with_response(content)
    assert result["requested_features"][0]["code"] == "DARK_MODE"
    assert result["requested_features"][0]["reason"] == ""


def test_bad_feature_shape_fails_validation_and_falls_back():
    # A feature that is not an object (missing required 'code') makes the whole
    # payload invalid, so the analyzer returns the safe default rather than a
    # half-parsed structure.
    content = '{"sentiment": "POSITIVO", "requested_features": ["not-an-object"]}'
    result = _run_with_response(content)
    assert result["sentiment"] == "INCONCLUSIVO"
    assert result["requested_features"] == []


def test_llm_call_exception_falls_back_safely():
    # A timeout/network error from the LLM must not blow up the request: the
    # analyzer swallows it and returns the canonical safe result.
    analyzer = FeedbackAnalyzer()
    analyzer.llm = MagicMock()
    with patch(
        "app.services.feedback_analyzer.ChatPromptTemplate"
    ) as mock_prompt:
        chain = MagicMock()
        chain.invoke.side_effect = TimeoutError("request timed out")
        mock_prompt.from_template.return_value.__or__.return_value = chain
        result = analyzer.analyze_feedback("texto de feedback")

    assert result["sentiment"] == "INCONCLUSIVO"
    assert result["is_spam"] is False
    assert result["requested_features"] == []
