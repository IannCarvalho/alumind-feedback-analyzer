"""Testes do endurecimento de segurança do painel e da API de ingestão.

Cada teste trava uma regressão concreta: open redirect via ``//host``,
500 com senha não-ASCII, força-bruta no login, cookie de sessão sem flags,
SECRET_KEY placeholder aceita em produção, 500s de entrada na API e a
corrida de id duplicado.
"""
from unittest.mock import patch
from urllib.parse import urlencode

import pytest

from app import create_app, db, validate_config
from app.config import Config
from app.extensions import limiter

from tests.helpers import csrf_token, login, post_form

OK_ANALYSIS = {"sentiment": "POSITIVO", "is_spam": False, "requested_features": []}
FEEDBACK_ID = "4042f20a-45f4-4647-8050-139ac16f610b"
STRONG_KEY = "k" * 48


def _secured_app(**overrides):
    application = create_app()
    settings = {"TESTING": True, "DASHBOARD_PASSWORD": "segredo", **overrides}
    application.config.update(settings)
    return application


@pytest.fixture()
def secured_client():
    application = _secured_app()
    with application.app_context():
        db.create_all()
        yield application.test_client()
        db.session.remove()
        db.drop_all()


# --- redirect pós-login -------------------------------------------------------

@pytest.mark.parametrize("target", [
    "//evil.example.com",
    "/\\evil.example.com",
    "/\t/evil.example.com",
    "https://evil.example.com/dashboard",
    "javascript:alert(1)",
    "dashboard",
])
def test_login_never_redirects_off_site(secured_client, target):
    resp = post_form(
        secured_client, f"/login?{urlencode({'next': target})}", {"password": "segredo"})
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/dashboard"


def test_login_keeps_local_next_with_query(secured_client):
    resp = post_form(
        secured_client, "/login?next=/feedbacks%3Fpage%3D2", {"password": "segredo"})
    assert resp.headers["Location"] == "/feedbacks?page=2"


# --- senha não-ASCII ------------------------------------------------------------

def test_non_ascii_password_does_not_crash():
    """compare_digest com str não-ASCII levantava TypeError (500)."""
    application = _secured_app(DASHBOARD_PASSWORD="senha-ção")
    with application.app_context():
        db.create_all()
        client = application.test_client()
        wrong = login(client, "não-é")
        right = login(client, "senha-ção")
        db.drop_all()
    assert wrong.status_code == 200
    assert "Senha incorreta" in wrong.get_data(as_text=True)
    assert right.status_code == 302


# --- força-bruta ------------------------------------------------------------------

class LoginLimitedConfig(Config):
    TESTING = True
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_LOGIN = "3 per minute"
    DASHBOARD_PASSWORD = "segredo"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


def test_login_post_is_rate_limited():
    application = create_app(LoginLimitedConfig)
    with application.app_context():
        limiter.reset()
        client = application.test_client()
        token = csrf_token(client)
        statuses = [
            client.post("/login", data={"password": "errada", "csrf_token": token}).status_code
            for _ in range(3)
        ]
        blocked = client.post("/login", data={"password": "errada", "csrf_token": token})
        # O GET da tela de login não consome o limite do POST.
        page = client.get("/login")
        limiter.reset()
    assert statuses == [200, 200, 200]
    assert blocked.status_code == 429
    assert "Muitas tentativas" in blocked.get_data(as_text=True)
    assert page.status_code == 200


# --- cookie de sessão ----------------------------------------------------------

def test_session_cookie_flags_and_expiry():
    application = _secured_app(SESSION_COOKIE_SECURE=True)
    with application.app_context():
        db.create_all()
        client = application.test_client()
        client.environ_base["wsgi.url_scheme"] = "https"  # cookie Secure só volta em HTTPS
        resp = login(client, "segredo")
        db.drop_all()
    cookie = resp.headers["Set-Cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
    assert "Secure" in cookie
    # Sessão permanente => cookie com validade explícita.
    assert "Expires=" in cookie


# --- SECRET_KEY em produção ---------------------------------------------------

def _prod_config(secret_key):
    return type("ProdConfig", (Config,), {
        "FLASK_ENV": "production",
        "SECRET_KEY": secret_key,
        "OPENAI_API_KEY": "test-key",
        "EMAIL_HOST": "smtp.example.com",
        "EMAIL_USER": "user",
        "EMAIL_PASSWORD": "pass",
        "EMAIL_RECIPIENTS": ["team@example.com"],
    })


@pytest.mark.parametrize("secret_key", [
    None, "", "default-secret-key", "change-me", "sua-chave-secreta-aqui", "curta-demais",
])
def test_production_rejects_insecure_secret_key(secret_key):
    with pytest.raises(ValueError, match="SECRET_KEY"):
        validate_config(_prod_config(secret_key))


def test_production_accepts_strong_secret_key():
    validate_config(_prod_config(STRONG_KEY))


def test_development_only_warns_on_default_secret_key():
    dev = type("DevConfig", (Config,), {
        "FLASK_ENV": "development",
        "SECRET_KEY": "default-secret-key",
        "OPENAI_API_KEY": "test-key",
    })
    validate_config(dev)


# --- rota web de detalhe -------------------------------------------------------

def test_web_detail_with_malformed_id_is_404(client):
    assert client.get("/feedback/nao-e-uuid").status_code == 404


# --- validação da API de ingestão -------------------------------------------

@pytest.mark.parametrize("raw_body", ["null", "5", '["id", "feedback"]', '"texto"', "{json quebrado"])
def test_ingest_rejects_non_object_bodies_with_json_400(client, raw_body):
    resp = client.post("/api/feedbacks", data=raw_body, content_type="application/json")
    assert resp.status_code == 400
    assert resp.is_json
    assert "error" in resp.get_json()


@pytest.mark.parametrize("feedback", [None, 123, {"a": 1}, ["x"]])
def test_ingest_rejects_non_string_feedback(client, feedback):
    resp = client.post("/api/feedbacks", json={"id": FEEDBACK_ID, "feedback": feedback})
    assert resp.status_code == 400
    assert "string" in resp.get_json()["error"]


def test_ingest_rejects_feedback_over_max_chars(client):
    client.application.config["MAX_FEEDBACK_CHARS"] = 10
    resp = client.post("/api/feedbacks", json={"id": FEEDBACK_ID, "feedback": "x" * 11})
    assert resp.status_code == 400
    assert "at most 10" in resp.get_json()["error"]


def test_ingest_body_over_max_content_length_is_413_json(client):
    client.application.config["MAX_CONTENT_LENGTH"] = 100
    resp = client.post("/api/feedbacks", json={"id": FEEDBACK_ID, "feedback": "x" * 500})
    assert resp.status_code == 413
    assert resp.is_json


def test_concurrent_duplicate_id_returns_409_not_500(client):
    body = {"id": FEEDBACK_ID, "feedback": "primeiro envio"}
    with patch("app.routes.api.feedback_analyzer.analyze_feedback", return_value=OK_ANALYSIS):
        assert client.post("/api/feedbacks", json=body).status_code == 201
        # Simula a corrida: a checagem prévia não enxerga o registro gravado
        # por outra requisição, então quem decide é a PK no commit.
        db.session.remove()
        with patch("app.routes.api.FeedbackService.get_feedback_by_id", return_value=None):
            resp = client.post("/api/feedbacks", json=body)
    assert resp.status_code == 409


def test_feature_code_is_capped_to_column_length(client):
    analysis = {
        "sentiment": "POSITIVO",
        "is_spam": False,
        "requested_features": [{"code": "X" * 80, "reason": "código longo vindo da LLM"}],
    }
    with patch("app.routes.api.feedback_analyzer.analyze_feedback", return_value=analysis):
        resp = client.post("/api/feedbacks", json={"id": FEEDBACK_ID, "feedback": "quero X"})
    assert resp.status_code == 201
    assert len(resp.get_json()["requested_features"][0]["code"]) == 50
