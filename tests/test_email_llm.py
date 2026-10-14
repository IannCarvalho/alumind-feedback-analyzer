"""Tests for the LLM-assisted weekly email generation and its fallback."""
from unittest.mock import MagicMock, patch

from app.services import email_service

STATS = {
    "total_feedbacks": 5,
    "positive_percentage": 80.0,
    "negative_percentage": 20.0,
    "top_features": [{"code": "EDITAR_PERFIL", "count": 3, "reasons": ["x"]}],
}


def test_empty_stats_uses_static_template():
    stats = {"total_feedbacks": 0, "positive_percentage": 0,
             "negative_percentage": 0, "top_features": []}
    out = email_service.generate_email_content_llm(stats)
    assert out == email_service.generate_email_content(stats)


def test_no_api_key_falls_back_to_template():
    with patch.object(email_service.Config, "OPENAI_API_KEY", None):
        out = email_service.generate_email_content_llm(STATS)
    assert out == email_service.generate_email_content(STATS)


def test_llm_error_falls_back_to_template():
    with patch.object(email_service.Config, "OPENAI_API_KEY", "k"), patch(
        "langchain.chat_models.ChatOpenAI", side_effect=RuntimeError("boom")
    ):
        out = email_service.generate_email_content_llm(STATS)
    assert out == email_service.generate_email_content(STATS)


def test_llm_success_wraps_content():
    fake_msg = MagicMock()
    fake_msg.content = "<h2>Resumo</h2><p>tudo certo</p>"
    with patch.object(email_service.Config, "OPENAI_API_KEY", "k"), patch(
        "langchain.chat_models.ChatOpenAI"
    ), patch("langchain.prompts.ChatPromptTemplate") as mock_prompt:
        chain = MagicMock()
        chain.invoke.return_value = fake_msg
        mock_prompt.from_template.return_value.__or__.return_value = chain
        out = email_service.generate_email_content_llm(STATS)
    assert "Resumo" in out
    assert out.startswith("<html><body>")
