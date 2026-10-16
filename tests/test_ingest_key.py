"""Chave de ingestão do POST /api/feedbacks."""
import logging
from unittest.mock import patch

import pytest

from app import create_app, db
from app.config import Config
from app.models.feedback import Feedback

KEY = "ingest-key-com-bem-mais-de-24-chars"
OLD_KEY = "chave-antiga-com-mais-de-24-chars"
FEEDBACK_ID = "4042f20a-45f4-4647-8050-139ac16f610b"
OK_ANALYSIS = {"sentiment": "POSITIVO", "is_spam": False, "requested_features": []}
ANALYZE = "app.routes.api.feedback_analyzer.analyze_feedback"
BYOK = {"X-LLM-Provider": "anthropic", "X-LLM-Api-Key": "sk-ant-api03-cliente-pagante-123"}


def payload(feedback_id=FEEDBACK_ID):
    return {"id": feedback_id, "feedback": "Adoro o app, falta modo escuro."}


@pytest.fixture()
def build():
    contexts = []

    def _build(**config):
        application = create_app()
        application.config.update(TESTING=True, **config)
        ctx = application.app_context()
        ctx.push()
        db.create_all()
        contexts.append(ctx)
        return application.test_client()

    yield _build
    for ctx in contexts:
        db.session.remove()
        db.drop_all()
        ctx.pop()


def stored_count():
    return db.session.query(Feedback).count()


# ------------------------------------------------------------------- aberto

def test_ingestion_stays_open_when_no_key_is_configured(build):
    client = build(INGEST_API_KEYS=[])
    with patch(ANALYZE, return_value=OK_ANALYSIS):
        assert client.post("/api/feedbacks", json=payload()).status_code == 201


# ------------------------------------------------------------------ fechado

def test_missing_key_is_401_before_anything_runs(build):
    client = build(INGEST_API_KEYS=[KEY])
    with patch(ANALYZE) as analyze:
        response = client.post("/api/feedbacks", json=payload())
    assert response.status_code == 401
    body = response.get_json()
    assert body["code"] == "ingest_key_required"
    assert response.headers["WWW-Authenticate"] == "ApiKey"
    analyze.assert_not_called()  # nenhuma chamada de LLM paga
    assert stored_count() == 0


@pytest.mark.parametrize("sent", ["", "errada", KEY[:-1], KEY + "x", KEY.upper()])
def test_wrong_key_is_401(build, sent):
    client = build(INGEST_API_KEYS=[KEY])
    with patch(ANALYZE) as analyze:
        response = client.post("/api/feedbacks", json=payload(), headers={"X-API-Key": sent})
    assert response.status_code == 401
    analyze.assert_not_called()


def test_valid_key_ingests(build):
    client = build(INGEST_API_KEYS=[KEY])
    with patch(ANALYZE, return_value=OK_ANALYSIS):
        response = client.post("/api/feedbacks", json=payload(), headers={"X-API-Key": KEY})
    assert response.status_code == 201
    assert stored_count() == 1


def test_auth_comes_before_body_validation(build):
    """Sem chave, nem a validação do corpo é revelada."""
    client = build(INGEST_API_KEYS=[KEY])
    assert client.post("/api/feedbacks", json={}).status_code == 401
    assert client.post("/api/feedbacks", data="lixo").status_code == 401
    ok_key = client.post("/api/feedbacks", json={}, headers={"X-API-Key": KEY})
    assert ok_key.status_code == 400  # com chave, a validação responde normalmente


def test_key_is_only_read_from_the_dedicated_header(build):
    client = build(INGEST_API_KEYS=[KEY])
    with patch(ANALYZE, return_value=OK_ANALYSIS):
        assert client.post("/api/feedbacks", json=payload(),
                           headers={"Authorization": f"Bearer {KEY}"}).status_code == 401
        assert client.post(f"/api/feedbacks?api_key={KEY}&key={KEY}",
                           json=payload()).status_code == 401
        body = {**payload(), "api_key": KEY, "key": KEY}
        assert client.post("/api/feedbacks", json=body).status_code == 401


def test_several_keys_allow_rotation_without_downtime(build):
    client = build(INGEST_API_KEYS=[KEY, OLD_KEY])
    with patch(ANALYZE, return_value=OK_ANALYSIS):
        first = client.post("/api/feedbacks", json=payload("00000000-0000-0000-0000-000000000001"),
                            headers={"X-API-Key": OLD_KEY})
        second = client.post("/api/feedbacks", json=payload("00000000-0000-0000-0000-000000000002"),
                             headers={"X-API-Key": KEY})
    assert first.status_code == second.status_code == 201


def test_non_ascii_header_does_not_crash(build):
    client = build(INGEST_API_KEYS=[KEY])
    response = client.post("/api/feedbacks", json=payload(), headers={"X-API-Key": "chavé-ção"})
    assert response.status_code == 401


def test_other_routes_are_not_affected(build):
    client = build(INGEST_API_KEYS=[KEY])
    assert client.get("/health").status_code == 200
    assert client.get("/api/feedbacks").status_code == 200  # leitura tem a regra própria


def test_key_never_reaches_the_logs(build, caplog):
    client = build(INGEST_API_KEYS=[KEY])
    caplog.set_level(logging.DEBUG)
    with patch(ANALYZE, return_value=OK_ANALYSIS):
        client.post("/api/feedbacks", json=payload(), headers={"X-API-Key": KEY})
        client.post("/api/feedbacks", json=payload(), headers={"X-API-Key": "tentativa-errada-123456789"})
    assert KEY not in caplog.text
    assert "tentativa-errada-123456789" not in caplog.text


# --------------------------------------------------------------- BYOK sem chave

def test_byok_does_not_replace_the_key_by_default(build):
    client = build(INGEST_API_KEYS=[KEY])
    with patch(ANALYZE) as analyze:
        response = client.post("/api/feedbacks", json=payload(), headers=BYOK)
    assert response.status_code == 401
    analyze.assert_not_called()


def test_byok_without_key_is_accepted_when_explicitly_allowed(build):
    client = build(INGEST_API_KEYS=[KEY], INGEST_ALLOW_BYOK_WITHOUT_KEY=True)
    with patch(ANALYZE, return_value=OK_ANALYSIS) as analyze:
        response = client.post("/api/feedbacks", json=payload(), headers=BYOK)
    assert response.status_code == 201
    credential = analyze.call_args.kwargs["credential"]
    assert credential.source == "request"  # paga com a chave dele, nunca a do servidor
    assert credential.api_key == BYOK["X-LLM-Api-Key"]


@pytest.mark.parametrize("headers", [
    {"X-LLM-Api-Key": BYOK["X-LLM-Api-Key"]},   # falta o provedor
    {"X-LLM-Provider": "anthropic"},            # falta a chave
    {"X-LLM-Provider": " ", "X-LLM-Api-Key": " "},
    {},
])
def test_partial_byok_headers_do_not_bypass_the_key(build, headers):
    client = build(INGEST_API_KEYS=[KEY], INGEST_ALLOW_BYOK_WITHOUT_KEY=True)
    with patch(ANALYZE) as analyze:
        assert client.post("/api/feedbacks", json=payload(), headers=headers).status_code == 401
    analyze.assert_not_called()


def test_byok_bypass_respects_the_global_byok_switch(build):
    client = build(INGEST_API_KEYS=[KEY], INGEST_ALLOW_BYOK_WITHOUT_KEY=True,
                   BYOK_REQUEST_KEYS_ENABLED=False)
    assert client.post("/api/feedbacks", json=payload(), headers=BYOK).status_code == 401


def test_bypass_flag_does_nothing_without_a_configured_key(build):
    """Sem chave de ingestão a API é aberta e a flag é irrelevante."""
    client = build(INGEST_API_KEYS=[], INGEST_ALLOW_BYOK_WITHOUT_KEY=True)
    with patch(ANALYZE, return_value=OK_ANALYSIS):
        assert client.post("/api/feedbacks", json=payload()).status_code == 201


# ---------------------------------------------------------------- limite / boot

class LimitedConfig(Config):
    TESTING = True
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_INGEST = "3 per minute"
    INGEST_API_KEYS = [KEY]
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


def test_unauthorized_attempts_still_count_against_the_rate_limit():
    """Tentar adivinhar a chave não sai de graça: o limite vale antes do 401."""
    application = create_app(LimitedConfig)
    with application.app_context():
        from app.extensions import limiter

        limiter.reset()
        client = application.test_client()
        statuses = [client.post("/api/feedbacks", json=payload(),
                                headers={"X-API-Key": f"palpite-{n}-com-24-caracteres!"}).status_code
                    for n in range(4)]
        limiter.reset()
    assert statuses == [401, 401, 401, 429]


def test_short_ingest_key_refuses_to_boot():
    class Short(Config):
        INGEST_API_KEYS = [KEY, "curta"]

    with pytest.raises(ValueError, match="INGEST_API_KEY"):
        create_app(Short)


def test_production_warns_when_server_pays_and_ingestion_is_open(caplog):
    class Prod(Config):
        FLASK_ENV = "production"
        SECRET_KEY = "s" * 40
        OPENAI_API_KEY = "sk-servidor-pagando-123456"
        INGEST_API_KEYS: list = []
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    with caplog.at_level(logging.WARNING):
        create_app(Prod)
    assert "INGEST_API_KEY não está definida" in caplog.text


def test_production_does_not_warn_when_the_key_is_set(caplog):
    class Prod(Config):
        FLASK_ENV = "production"
        SECRET_KEY = "s" * 40
        OPENAI_API_KEY = "sk-servidor-pagando-123456"
        INGEST_API_KEYS = [KEY]
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    with caplog.at_level(logging.WARNING):
        create_app(Prod)
    assert "INGEST_API_KEY não está definida" not in caplog.text
