"""API de leitura fechada (sessão ou Bearer) e CSRF no painel."""
import pytest

from app import create_app, db
from app.config import Config

from tests.helpers import csrf_token, login, post_form

PASSWORD = "segredo-do-painel"
TOKEN = "t0ken-de-leitura-com-32-caracteres!"
FEEDBACK_ID = "4042f20a-45f4-4647-8050-139ac16f610b"
READ_PATHS = ["/api/feedbacks", f"/api/feedbacks/{FEEDBACK_ID}"]


def make_client(**config):
    application = create_app()
    application.config.update(TESTING=True, **config)
    ctx = application.app_context()
    ctx.push()
    db.create_all()
    return application.test_client(), ctx


@pytest.fixture()
def build():
    contexts = []

    def _build(**config):
        client, ctx = make_client(**config)
        contexts.append(ctx)
        return client

    yield _build
    for ctx in contexts:
        db.session.remove()
        db.drop_all()
        ctx.pop()


def bearer(token=TOKEN):
    return {"Authorization": f"Bearer {token}"}


# ------------------------------------------------------------------ leitura

@pytest.mark.parametrize("path", READ_PATHS)
def test_read_api_is_open_when_nothing_is_configured(build, path):
    """Comportamento histórico de dev: sem senha nem token, nada muda."""
    client = build(DASHBOARD_PASSWORD=None, API_READ_TOKEN=None)
    assert client.get(path).status_code in (200, 404)


@pytest.mark.parametrize("path", READ_PATHS)
def test_read_api_requires_login_when_a_password_is_set(build, path):
    client = build(DASHBOARD_PASSWORD=PASSWORD)
    denied = client.get(path)
    assert denied.status_code == 401
    assert denied.get_json()["code"] == "unauthenticated"
    assert denied.headers["WWW-Authenticate"] == "Bearer"

    login(client, PASSWORD)
    assert client.get(path).status_code in (200, 404)


def test_read_api_denial_does_not_leak_data(build):
    client = build(DASHBOARD_PASSWORD=PASSWORD)
    body = client.get("/api/feedbacks").get_json()
    assert set(body) == {"error", "code"}


@pytest.mark.parametrize("path", READ_PATHS)
def test_bearer_token_unlocks_the_read_api(build, path):
    client = build(DASHBOARD_PASSWORD=None, API_READ_TOKEN=TOKEN)
    assert client.get(path).status_code == 401
    assert client.get(path, headers=bearer("errado")).status_code == 401
    assert client.get(path, headers=bearer(TOKEN[:-1])).status_code == 401
    assert client.get(path, headers=bearer()).status_code in (200, 404)


def test_bearer_scheme_is_case_insensitive_but_other_schemes_are_not(build):
    client = build(API_READ_TOKEN=TOKEN)
    assert client.get("/api/feedbacks", headers={"Authorization": f"bearer {TOKEN}"}).status_code == 200
    assert client.get("/api/feedbacks", headers={"Authorization": f"Basic {TOKEN}"}).status_code == 401
    assert client.get("/api/feedbacks", headers={"Authorization": TOKEN}).status_code == 401


def test_token_is_not_accepted_from_the_query_string(build):
    client = build(API_READ_TOKEN=TOKEN)
    assert client.get(f"/api/feedbacks?token={TOKEN}&api_key={TOKEN}").status_code == 401


def test_password_and_token_both_work_when_both_are_set(build):
    client = build(DASHBOARD_PASSWORD=PASSWORD, API_READ_TOKEN=TOKEN)
    assert client.get("/api/feedbacks").status_code == 401
    assert client.get("/api/feedbacks", headers=bearer()).status_code == 200
    login(client, PASSWORD)
    assert client.get("/api/feedbacks").status_code == 200


def test_only_a_token_does_not_turn_every_visitor_into_a_session_user(build):
    """Com só o token, 'sem auth no painel' não pode virar acesso à API."""
    client = build(DASHBOARD_PASSWORD=None, API_READ_TOKEN=TOKEN)
    assert client.get("/dashboard").status_code == 200  # painel aberto, como antes
    assert client.get("/api/feedbacks").status_code == 401


def test_ingestion_and_health_stay_public(build):
    client = build(DASHBOARD_PASSWORD=PASSWORD, API_READ_TOKEN=TOKEN)
    assert client.post("/api/feedbacks", json={}).status_code == 400  # validação, não 401
    assert client.get("/health").status_code == 200


def test_short_read_token_refuses_to_boot():
    class ShortToken(Config):
        API_READ_TOKEN = "curto"

    with pytest.raises(ValueError, match="API_READ_TOKEN"):
        create_app(ShortToken)


# --------------------------------------------------------------------- CSRF

def test_login_without_csrf_token_is_rejected(build):
    client = build(DASHBOARD_PASSWORD=PASSWORD)
    response = client.post("/login", data={"password": PASSWORD})
    assert response.status_code == 400
    assert "expirou" in response.get_data(as_text=True)
    assert client.get("/dashboard").status_code == 302  # não autenticou


def test_login_with_a_wrong_csrf_token_is_rejected(build):
    client = build(DASHBOARD_PASSWORD=PASSWORD)
    csrf_token(client)
    response = client.post("/login", data={"password": PASSWORD, "csrf_token": "errado"})
    assert response.status_code == 400
    assert client.get("/dashboard").status_code == 302


def test_a_token_from_another_session_is_rejected(build):
    """Login CSRF: o atacante usa o PRÓPRIO token na sessão da vítima."""
    attacker = build(DASHBOARD_PASSWORD=PASSWORD)
    victim = attacker.application.test_client()
    csrf_token(victim)  # a vítima só tem a sessão dela
    stolen = csrf_token(attacker)
    response = victim.post("/login", data={"password": PASSWORD, "csrf_token": stolen})
    assert response.status_code == 400


def test_csrf_check_comes_before_the_password_check(build):
    client = build(DASHBOARD_PASSWORD=PASSWORD)
    response = client.post("/login", data={"password": "errada"})
    assert response.status_code == 400
    assert "Senha incorreta" not in response.get_data(as_text=True)


def test_login_rotates_the_csrf_token(build):
    client = build(DASHBOARD_PASSWORD=PASSWORD)
    before = csrf_token(client)
    assert login(client, PASSWORD).status_code == 302
    after = csrf_token(client)
    assert after != before
    assert client.get("/dashboard").status_code == 200


def test_logout_is_csrf_free_and_always_logs_out(build):
    """Logout é idempotente: sem token, com token ou por GET, sempre desloga
    e redireciona (302) — nunca mostra a tela de 400."""
    client = build(DASHBOARD_PASSWORD=PASSWORD)
    login(client, PASSWORD)
    assert client.post("/logout").status_code == 302  # sem token
    assert client.get("/dashboard").status_code == 302  # deslogou

    login(client, PASSWORD)
    assert post_form(client, "/logout").status_code == 302  # com token
    assert client.get("/dashboard").status_code == 302

    login(client, PASSWORD)
    assert client.get("/logout").status_code == 302  # por GET
    assert client.get("/dashboard").status_code == 302


def test_forms_render_the_hidden_token(build):
    client = build(DASHBOARD_PASSWORD=PASSWORD)
    assert 'name="csrf_token"' in client.get("/login").get_data(as_text=True)
    login(client, PASSWORD)
    assert 'name="csrf_token"' in client.get("/dashboard").get_data(as_text=True)


def test_login_page_and_other_safe_requests_need_no_token(build):
    client = build(DASHBOARD_PASSWORD=PASSWORD)
    assert client.get("/login").status_code == 200
    assert client.get("/health").status_code == 200


def test_csrf_token_is_the_one_the_settings_api_hands_out(build):
    """Um token só por sessão: a tela de configuração reaproveita o do painel."""
    client = build(DASHBOARD_PASSWORD=PASSWORD)
    login(client, PASSWORD)
    form_token = csrf_token(client)
    assert client.get("/api/settings/providers").get_json()["csrf_token"] == form_token
